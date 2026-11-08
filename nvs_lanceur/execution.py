"""Exécution d'un exercice dans un processus séparé (le lanceur reste en vie pour revenir en arrière si besoin).

Le processus enfant est le même exécutable relancé avec `--executer <entree>` : il dispose ainsi des bibliothèques
figées du moteur. Codes de sortie de l'enfant :
  0   fin normale (ou code renvoyé par l'exercice lui-même via SystemExit)
  1   exception non rattrapée pendant l'exécution
  3   exercice incompatible avec ce moteur (ImportError, SyntaxError) → retour arrière immédiat
  4   exécution REFUSÉE : le script demandé n'est pas un exercice signé intact (1.2.4)

1.2.4 (audit de sécurité du 08/11/2026, constat 1) : `--executer` n'exécute plus n'importe quel script. L'enfant
revérifie lui-même que le fichier est le point d'entrée d'un exercice décrit par un manifeste signé par le projet,
que tous les fichiers de cet exercice sont intacts et qu'aucun fichier de code n'a été ajouté à côté ; il lit le
script UNE seule fois, en contrôle l'empreinte, et exécute exactement ces octets. L'exécution elle-même est
inchangée (mêmes mécanismes que runpy.run_path : même module __main__, mêmes sys.argv, sys.path, dossier de travail
et variables d'environnement) : l'exercice et son protocole ne voient aucune différence.
"""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass
from typing import Dict, List, Optional

from . import MOTEUR, VERSION

CODE_EXCEPTION = 1
CODE_INCOMPATIBLE = 3
CODE_REFUS = 4
PROFONDEUR_MAX_ENTREE = 8          # niveaux de dossiers entre le point d'entrée et le manifeste de sa version


@dataclass
class Resultat:
    code: int
    duree_s: float


def commande_enfant(entree: str) -> List[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--executer", entree]
    return [sys.executable, "-m", "nvs_lanceur", "--executer", entree]


def environnement_enfant(dossier_donnees: str, exercice_id: str, version: str, langue: str = "") -> Dict[str, str]:
    env = dict(os.environ)
    env.update({
        "NVS_DATA_DIR": dossier_donnees,          # l'exercice y range config/ et session_data/ (chap. 16.4 a)
        "NVS_LANCEUR_VERSION": VERSION,
        "NVS_MOTEUR": str(MOTEUR),
        "NVS_EXERCICE_ID": exercice_id,
        "NVS_EXERCICE_VERSION": version,
    })
    if langue in ("fr", "en"):
        env["NVS_LANGUE"] = langue                # langue choisie dans le lanceur ; l'exercice peut s'en servir
    if not getattr(sys, "frozen", False):
        # en mode source, l'enfant doit retrouver le paquet nvs_lanceur
        racine_paquet = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env["PYTHONPATH"] = racine_paquet + os.pathsep + env.get("PYTHONPATH", "")
    return env


def lancer(entree: str, dossier_donnees: str, exercice_id: str, version: str, journal_enfant: str = "",
           langue: str = "", langue_retour: str = "", cles_publiques: Optional[Dict[str, str]] = None) -> Resultat:
    os.makedirs(dossier_donnees, exist_ok=True)
    env = environnement_enfant(dossier_donnees, exercice_id, version, langue)
    if cles_publiques and not getattr(sys, "frozen", False):
        env["NVS_CLES_PUBLIQUES"] = json.dumps(cles_publiques)   # tests (clés de test) ; ignoré une fois figé
    if langue_retour:
        env["NVS_LANGUE_RETOUR"] = langue_retour  # l'exercice y écrit « fr » ou « en » si la personne change de langue
    if journal_enfant:
        env["NVS_JOURNAL_ENFANT"] = journal_enfant
    debut = time.monotonic()
    proc = subprocess.run(commande_enfant(entree), cwd=dossier_donnees, env=env)
    return Resultat(code=proc.returncode, duree_s=time.monotonic() - debut)


def _tracer(exc_texte: str) -> None:
    """L'exécutable gelé n'a pas de console : la trace d'un échec va dans NVS_JOURNAL_ENFANT (aucune donnée patient
    n'y figure : seulement la pile d'appel Python)."""
    chemin = os.environ.get("NVS_JOURNAL_ENFANT")
    if sys.stderr is not None:
        sys.stderr.write(exc_texte)
    if chemin:
        try:
            with open(chemin, "a", encoding="utf-8") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + os.environ.get("NVS_EXERCICE_ID", "?") + " "
                        + os.environ.get("NVS_EXERCICE_VERSION", "?") + "\n" + exc_texte + "\n")
        except OSError:
            pass


class ExecutionRefusee(Exception):
    pass


def source_verifiee(entree: str, cles_publiques: Dict[str, str]) -> bytes:
    """Octets du script `entree` s'il est le point d'entrée d'un exercice signé intact ; sinon ExecutionRefusee.
    Ne dépend d'aucun réglage modifiable (ni dossier, ni variable d'environnement) : seulement des clés publiques
    embarquées dans l'exécutable."""
    from .depot import NOM_MANIFESTE, NOM_SIGNATURE
    from .manifeste import ManifesteInvalide, lire_manifeste
    entree = os.path.abspath(entree)
    dossier = os.path.dirname(entree)
    for _ in range(PROFONDEUR_MAX_ENTREE):
        if os.path.isfile(os.path.join(dossier, NOM_MANIFESTE)):
            break
        parent = os.path.dirname(dossier)
        if parent == dossier:
            raise ExecutionRefusee("aucun manifeste signé à côté du script")
        dossier = parent
    else:
        raise ExecutionRefusee("aucun manifeste signé à côté du script")
    try:
        with open(os.path.join(dossier, NOM_MANIFESTE), "rb") as f:
            brut = f.read()
        with open(os.path.join(dossier, NOM_SIGNATURE), "rb") as f:
            sig = f.read()
        m = lire_manifeste(brut, sig, cles_publiques)
    except (OSError, ManifesteInvalide) as exc:
        raise ExecutionRefusee(f"manifeste non valide : {exc}") from None
    rel = os.path.relpath(entree, dossier).replace(os.sep, "/")
    # Plusieurs exercices peuvent avoir le même nom de point d'entrée : on essaie d'abord celui annoncé par le
    # lanceur (NVS_EXERCICE_ID / _VERSION), puis les autres. Quel que soit le candidat retenu, il est signé et
    # intact : le choix n'a aucune incidence sur la sécurité.
    candidats = [e for e in m.exercices if e.entree == rel]
    candidats.sort(key=lambda e: (e.id != os.environ.get("NVS_EXERCICE_ID"),
                                  e.version != os.environ.get("NVS_EXERCICE_VERSION")))
    if not candidats:
        raise ExecutionRefusee("le script n'est le point d'entrée d'aucun exercice signé")
    motifs = []
    for ex in candidats:
        try:
            return _verifier_fichiers(dossier, ex)
        except ExecutionRefusee as exc:
            motifs.append(f"{ex.id} {ex.version} : {exc}")
    raise ExecutionRefusee(" ; ".join(motifs))


def _verifier_fichiers(dossier: str, ex) -> bytes:
    from .depot import fichiers_code_en_trop, sha256_fichier
    source = None
    for fi in ex.fichiers:
        p = os.path.join(dossier, *fi.chemin.split("/"))
        try:
            if fi.chemin == ex.entree:
                with open(p, "rb") as f:
                    octets = f.read(fi.taille + 1)
                if len(octets) != fi.taille or hashlib.sha256(octets).hexdigest() != fi.sha256:
                    raise ExecutionRefusee("point d'entrée modifié")
                source = octets
            elif os.path.getsize(p) != fi.taille or sha256_fichier(p) != fi.sha256:
                raise ExecutionRefusee(f"fichier modifié : {fi.chemin}")
        except OSError:
            raise ExecutionRefusee(f"fichier absent : {fi.chemin}") from None
    en_trop = fichiers_code_en_trop(dossier, [fi.chemin for fi in ex.fichiers])
    if en_trop:
        raise ExecutionRefusee(f"fichier(s) de code non signé(s) : {', '.join(en_trop[:3])}")
    if source is None:                                      # impossible : lire_manifeste l'exige déjà
        raise ExecutionRefusee("point d'entrée absent du manifeste")
    return source


def executer_exercice_signe(entree: str) -> int:
    """Côté enfant (`--executer`) : revérifie puis exécute ; refuse (code 4) tout script non signé."""
    from .config import charger_cles_publiques, env_de_test
    try:
        cles_test = env_de_test("NVS_CLES_PUBLIQUES")       # jamais lue dans l'exécutable distribué
        cles = {str(k): str(v) for k, v in json.loads(cles_test).items()} if cles_test else charger_cles_publiques()
        source = source_verifiee(entree, cles)
    except ExecutionRefusee as exc:
        _tracer(f"EXÉCUTION REFUSÉE ({entree}) : {exc}\n")
        return CODE_REFUS
    return executer_dans_ce_processus(entree, source)


def _executer_source(entree: str, source: bytes) -> None:
    """Exactement ce que fait runpy.run_path(entree, run_name="__main__") pour un fichier source, mais à partir des
    octets déjà vérifiés (pas de seconde lecture du disque). dont_inherit=True : aucune option __future__ de ce
    module n'est transmise à l'exercice (comme dans runpy)."""
    code = compile(source, entree, "exec", dont_inherit=True)
    runpy._run_module_code(code, None, "__main__", pkg_name="", script_name=entree)


def executer_dans_ce_processus(entree: str, source: Optional[bytes] = None) -> int:
    """Exécute le script comme `python entree` (avec `source` : ces octets, déjà vérifiés, au lieu du fichier)."""
    entree = os.path.abspath(entree)
    sys.argv = [entree]
    sys.path.insert(0, os.path.dirname(entree))
    try:
        from .identite import preparer_qt
        preparer_qt()                     # icône NeuroVision sur les fenêtres Qt de l'exercice (au mieux)
    except Exception:
        pass
    try:
        if source is None:
            runpy.run_path(entree, run_name="__main__")
        else:
            _executer_source(entree, source)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else (0 if code is None else 1)
    except (ImportError, SyntaxError):
        _tracer(traceback.format_exc())
        return CODE_INCOMPATIBLE
    except Exception:
        _tracer(traceback.format_exc())
        return CODE_EXCEPTION
    return 0


def echec_au_demarrage(res: Resultat, delai_s: float) -> bool:
    if res.code in (CODE_INCOMPATIBLE, CODE_REFUS):
        return True
    return res.code == CODE_EXCEPTION and res.duree_s < delai_s
