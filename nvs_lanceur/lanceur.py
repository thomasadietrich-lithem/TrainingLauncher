"""Orchestration du démarrage (chap. 16.3 du document directeur).

1. Manifeste signé (sinon : on continue avec ce qui est installé et vérifié).
2. Lanceur trop ancien → installeur silencieux (auto-mise à jour) puis sortie.
3. Mise à jour de chaque exercice publié (compatible avec ce moteur, non marqué en échec).
4. Choix de l'exercice (s'il y en a plusieurs), revérification, exécution, retour arrière si échec au démarrage.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import subprocess
import sys
import tempfile
from typing import Callable, List, Optional, Tuple

from . import MOTEUR, VERSION
from .config import TAILLE_MAX_FICHIER, TAILLE_MAX_INSTALLEUR, TAILLE_MAX_MANIFESTE, Reglages
from .depot import Depot
from .execution import Resultat, echec_au_demarrage, lancer
from .interface import Interface
from .manifeste import Exercice, Manifeste, ManifesteInvalide, lire_manifeste, version_tuple
from . import reseau

log = logging.getLogger("nvs_lanceur")

# Codes de sortie du lanceur (journal / assistance) — aucune donnée patient.
OK = 0
SORTIE_MAJ_LANCEUR = 10
ERR_AUCUN_EXERCICE = 20
ERR_PREMIERE_INSTALLATION = 21
ERR_EXERCICE_KO = 30


def configurer_journal(reglages: Reglages) -> None:
    os.makedirs(reglages.racine, exist_ok=True)
    h = logging.handlers.RotatingFileHandler(reglages.fichier_journal, maxBytes=512 * 1024, backupCount=2,
                                             encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.handlers[:] = [h]
    log.setLevel(logging.INFO)


def signature_authenticode_valide(chemin: str) -> bool:  # pragma: no cover - Windows uniquement
    """Vérifie la signature Windows (Authenticode) d'un exécutable. Utilisé seulement si le manifeste l'exige."""
    if os.name != "nt":
        return False
    cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
           f"(Get-AuthenticodeSignature -LiteralPath '{chemin}').Status"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return out.stdout.strip() == "Valid"
    except Exception:
        return False


def lancer_installeur(chemin: str) -> None:  # pragma: no cover - Windows uniquement
    """Installeur Inno Setup en mode silencieux ; il relance NeuroVision à la fin (section [Run] de l'installeur)."""
    subprocess.Popen([chemin, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/RELANCER=1"],
                     close_fds=True, creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))


class Lanceur:
    def __init__(self, reglages: Reglages, interface: Interface,
                 executer: Callable[[str, str, str, str], Resultat] = lancer,
                 installer_lanceur: Callable[[str], None] = lancer_installeur,
                 verifier_authenticode: Callable[[str], bool] = signature_authenticode_valide):
        self.r = reglages
        self.ui = interface
        self.executer = executer
        self.installer_lanceur = installer_lanceur
        self.verifier_authenticode = verifier_authenticode
        self.depot = Depot(reglages)

    # ------------------------------------------------------------ manifeste
    def _url(self, relative: str) -> str:
        return reseau.joindre(self.r.url_base, relative)

    def obtenir_manifeste(self) -> Optional[Manifeste]:
        base = f"canal/{self.r.canal}.json"
        try:
            brut = reseau.lire(self._url(base), TAILLE_MAX_MANIFESTE, self.r.delai_reseau_s)
            sig = reseau.lire(self._url(base + ".sig"), 4096, self.r.delai_reseau_s)
            m = lire_manifeste(brut, sig, self.r.cles_publiques, canal_attendu=self.r.canal)
        except reseau.ErreurReseau as exc:
            log.info("manifeste indisponible : %s", exc)
            return None
        except ManifesteInvalide as exc:
            log.warning("manifeste REFUSÉ : %s", exc)
            return None
        if m.sequence < self.depot.sequence_vue:
            log.warning("manifeste REFUSÉ : sequence %s < %s déjà vue (retour en arrière)", m.sequence,
                        self.depot.sequence_vue)
            return None
        if m.sequence > self.depot.sequence_vue:
            self.depot.oublier_echecs_anterieurs(m.sequence)
        self.depot.noter_sequence(m.sequence)
        self.depot.sauver()
        log.info("manifeste sequence %s accepté (%d exercice(s))", m.sequence, len(m.exercices))
        return m

    # ------------------------------------------------------ auto-mise à jour
    def mettre_a_jour_lanceur(self, m: Manifeste) -> bool:
        """True si un installeur a été lancé (le lanceur doit alors se fermer)."""
        try:
            trop_vieux = version_tuple(VERSION) < version_tuple(m.lanceur_version_min)
        except ManifesteInvalide:
            return False
        if not trop_vieux:
            return False
        if m.installeur is None:
            log.warning("lanceur %s < version_min %s mais aucun installeur publié", VERSION, m.lanceur_version_min)
            return False
        self.ui.progression("maj_lanceur")
        os.makedirs(self.r.dossier_temp, exist_ok=True)
        fd, chemin = tempfile.mkstemp(prefix="Installer_NeuroVision_", suffix=".exe", dir=self.r.dossier_temp)
        os.close(fd)
        try:
            reseau.telecharger(self._url(m.installeur.url), chemin, min(m.installeur.taille, TAILLE_MAX_INSTALLEUR),
                               m.installeur.sha256, self.r.delai_reseau_s * 4)
            if m.exiger_authenticode and not self.verifier_authenticode(chemin):
                raise reseau.ErreurReseau("signature Windows de l'installeur absente ou invalide")
        except reseau.ErreurReseau as exc:
            log.warning("auto-mise à jour impossible : %s", exc)
            self.ui.fermer_progression()
            try:
                os.unlink(chemin)
            except OSError:
                pass
            return False
        log.info("lancement de l'installeur %s (version_min %s)", os.path.basename(chemin), m.lanceur_version_min)
        self.installer_lanceur(chemin)
        return True

    # ---------------------------------------------------- mise à jour exos
    def mettre_a_jour_exercices(self, m: Manifeste) -> None:
        affiche = False
        for ex in m.exercices:
            if not ex.actif:
                continue
            if ex.moteur_requis > MOTEUR:
                log.info("%s %s demande le moteur %s (lanceur : %s) : en attente d'un nouveau lanceur",
                         ex.id, ex.version, ex.moteur_requis, MOTEUR)
                continue
            if self.depot.est_en_echec(ex.id, ex.version):
                log.info("%s %s marquée en échec : ignorée jusqu'au prochain manifeste", ex.id, ex.version)
                continue
            courante = self.depot.courante(ex.id)
            if courante == ex.version and self.depot.verifier_installee(ex.id, courante):
                continue
            if not affiche:
                self.ui.progression("maj_exercice")
                affiche = True
            try:
                self.depot.installer(m, ex, lambda url, dest, taille, sha: reseau.telecharger(
                    self._url(url), dest, min(taille, TAILLE_MAX_FICHIER), sha, self.r.delai_reseau_s * 2))
            except (reseau.ErreurReseau, OSError) as exc:
                log.warning("mise à jour de %s vers %s impossible : %s", ex.id, ex.version, exc)
                continue
            self.depot.basculer(ex.id, ex.version)
            log.info("%s : version %s installée (précédente : %s)", ex.id, ex.version, self.depot.precedente(ex.id))
        if affiche:
            self.ui.fermer_progression()

    # ------------------------------------------------------------ choix
    def exercices_disponibles(self, m: Optional[Manifeste]) -> List[Tuple[str, str]]:
        """[(id, nom)] des exercices installés, intacts, et encore publiés (hors ligne : tous les installés)."""
        options = []
        ids = [e.id for e in m.exercices if e.actif] if m else self.depot.ids_installes()
        for eid in ids:
            ex = self.depot.verifier_installee(eid, self.depot.courante(eid))
            if ex is None and self.depot.precedente(eid):
                ex = self.depot.verifier_installee(eid, self.depot.precedente(eid))
            if ex is not None:
                options.append((eid, ex.nom_affiche(self.ui.langue)))
        return options

    # ---------------------------------------------------------- exécution
    def _executer_version(self, eid: str, version: str) -> Optional[Resultat]:
        ex = self.depot.verifier_installee(eid, version)      # revérification à CHAQUE lancement
        if ex is None:
            log.warning("%s %s : fichiers altérés ou absents, exécution refusée", eid, version)
            return None
        entree = os.path.join(self.depot.dossier_version(eid, version), *ex.entree.split("/"))
        log.info("exécution de %s %s", eid, version)
        res = self.executer(entree, self.r.donnees_exercice(eid), eid, version)
        log.info("%s %s terminé : code %s en %.0f s", eid, version, res.code, res.duree_s)
        return res

    def executer_exercice(self, eid: str) -> int:
        courante = self.depot.courante(eid)
        res = self._executer_version(eid, courante) if courante else None
        if res is not None and not echec_au_demarrage(res, self.r.delai_echec_demarrage_s):
            return OK
        # Échec au démarrage ou version courante altérée → marquer et revenir à la précédente.
        if courante:
            self.depot.marquer_echec(eid, courante, self.depot.sequence_vue)
            self.depot.sauver()
        precedente = self.depot.retour_arriere(eid)
        if precedente and self.depot.verifier_installee(eid, precedente):
            log.warning("%s : retour arrière %s → %s", eid, courante, precedente)
            self.ui.message("echec_retour")
            res2 = self._executer_version(eid, precedente)
            if res2 is not None and not echec_au_demarrage(res2, self.r.delai_echec_demarrage_s):
                return OK
        self.ui.message("echec_total", code=f"L{ERR_EXERCICE_KO}")
        return ERR_EXERCICE_KO

    # ------------------------------------------------------------ entrée
    def demarrer(self) -> int:
        log.info("=== lanceur %s (moteur %s) ===", VERSION, MOTEUR)
        self.ui.progression("verif")
        m = self.obtenir_manifeste()
        self.ui.fermer_progression()
        if m is not None:
            if self.mettre_a_jour_lanceur(m):
                return SORTIE_MAJ_LANCEUR
            self.mettre_a_jour_exercices(m)
        options = self.exercices_disponibles(m)
        if not options:
            if not self.depot.ids_installes() and m is None:
                self.ui.message("premiere_install")
                return ERR_PREMIERE_INSTALLATION
            self.ui.message("aucun")
            return ERR_AUCUN_EXERCICE
        eid = options[0][0] if len(options) == 1 else self.ui.choisir(options)
        if eid is None:
            return OK
        return self.executer_exercice(eid)
