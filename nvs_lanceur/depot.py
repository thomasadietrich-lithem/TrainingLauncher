"""Dépôt local des exercices installés et état du lanceur.

Arborescence (sous la racine) :
  etat.json                                  état (écriture atomique)
  exercices/<id>/<version>/…                 fichiers vérifiés + _manifeste.json(.sig) d'origine
  donnees/<id>/                              données de l'exercice — JAMAIS touché ici
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from typing import Callable, Dict, Optional

from .config import Reglages
from .manifeste import Exercice, Manifeste, ManifesteInvalide, lire_manifeste

NOM_MANIFESTE = "_manifeste.json"
NOM_SIGNATURE = "_manifeste.json.sig"


def sha256_fichier(chemin: str) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def ecrire_atomique(chemin: str, contenu: bytes) -> None:
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=os.path.dirname(chemin))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(contenu)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, chemin)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


class Depot:
    def __init__(self, reglages: Reglages):
        self.r = reglages
        os.makedirs(self.r.racine, exist_ok=True)
        self.etat = self._charger_etat()

    # ---------------------------------------------------------------- état
    def _charger_etat(self) -> dict:
        try:
            with open(self.r.fichier_etat, "r", encoding="utf-8") as f:
                etat = json.load(f)
            if isinstance(etat, dict):
                etat.setdefault("sequence_vue", 0)
                etat.setdefault("exercices", {})
                return etat
        except (OSError, ValueError):
            pass
        return {"sequence_vue": 0, "exercices": {}}

    def sauver(self) -> None:
        ecrire_atomique(self.r.fichier_etat, json.dumps(self.etat, indent=2, ensure_ascii=False).encode("utf-8"))

    def _ex(self, exercice_id: str) -> dict:
        e = self.etat["exercices"].setdefault(exercice_id, {})
        e.setdefault("courante", None)
        e.setdefault("precedente", None)
        e.setdefault("en_echec", {})
        return e

    @property
    def sequence_vue(self) -> int:
        return int(self.etat.get("sequence_vue", 0))

    def noter_sequence(self, sequence: int) -> None:
        if sequence > self.sequence_vue:
            self.etat["sequence_vue"] = sequence

    def courante(self, exercice_id: str) -> Optional[str]:
        return self._ex(exercice_id)["courante"]

    def precedente(self, exercice_id: str) -> Optional[str]:
        return self._ex(exercice_id)["precedente"]

    def ids_installes(self):
        return [i for i, e in self.etat["exercices"].items() if e.get("courante")]

    def est_en_echec(self, exercice_id: str, version: str) -> bool:
        return version in self._ex(exercice_id)["en_echec"]

    def marquer_echec(self, exercice_id: str, version: str, sequence: int) -> None:
        self._ex(exercice_id)["en_echec"][version] = sequence

    def oublier_echecs_anterieurs(self, sequence: int) -> None:
        """Un nouveau manifeste (sequence plus grande) redonne sa chance à une version marquée en échec."""
        for e in self.etat["exercices"].values():
            e["en_echec"] = {v: s for v, s in e.get("en_echec", {}).items() if s >= sequence}

    # ------------------------------------------------------------ fichiers
    def dossier_version(self, exercice_id: str, version: str) -> str:
        return os.path.join(self.r.dossier_exercices, exercice_id, version)

    def verifier_installee(self, exercice_id: str, version: str) -> Optional[Exercice]:
        """Revérifie hors ligne une version installée : signature du manifeste d'origine + empreinte de chaque fichier.
        Retourne la description de l'exercice si tout est intact, sinon None."""
        if not version:
            return None
        d = self.dossier_version(exercice_id, version)
        try:
            with open(os.path.join(d, NOM_MANIFESTE), "rb") as f:
                brut = f.read()
            with open(os.path.join(d, NOM_SIGNATURE), "rb") as f:
                sig = f.read()
            m = lire_manifeste(brut, sig, self.r.cles_publiques)
        except (OSError, ManifesteInvalide):
            return None
        ex = m.exercice(exercice_id)
        if ex is None or ex.version != version:
            return None
        for fi in ex.fichiers:
            p = os.path.join(d, *fi.chemin.split("/"))
            try:
                if os.path.getsize(p) != fi.taille or sha256_fichier(p) != fi.sha256:
                    return None
            except OSError:
                return None
        return ex

    def installer(self, manifeste: Manifeste, ex: Exercice, telecharger: Callable[[str, str, int, str], None]) -> None:
        """Télécharge et vérifie TOUS les fichiers dans un dossier temporaire, puis bascule le dossier en une fois.
        telecharger(url_relative, destination, taille_max, sha256_attendu) lève une exception en cas d'écart."""
        os.makedirs(self.r.dossier_temp, exist_ok=True)
        tmp = tempfile.mkdtemp(prefix=f"{ex.id}-{ex.version}-", dir=self.r.dossier_temp)
        try:
            for fi in ex.fichiers:
                dest = os.path.join(tmp, *fi.chemin.split("/"))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                telecharger(fi.url, dest, fi.taille, fi.sha256)
                if os.path.getsize(dest) != fi.taille or sha256_fichier(dest) != fi.sha256:
                    raise IOError(f"empreinte incorrecte : {fi.chemin}")
            with open(os.path.join(tmp, NOM_MANIFESTE), "wb") as f:
                f.write(manifeste.brut)
            with open(os.path.join(tmp, NOM_SIGNATURE), "wb") as f:
                f.write(manifeste.signature)
            final = self.dossier_version(ex.id, ex.version)
            os.makedirs(os.path.dirname(final), exist_ok=True)
            if os.path.exists(final):
                shutil.rmtree(final)
            os.replace(tmp, final)
        finally:
            if os.path.exists(tmp):
                shutil.rmtree(tmp, ignore_errors=True)

    def basculer(self, exercice_id: str, version: str) -> None:
        e = self._ex(exercice_id)
        if e["courante"] != version:
            e["precedente"] = e["courante"]
            e["courante"] = version
        self.sauver()
        self._elaguer(exercice_id)

    def retour_arriere(self, exercice_id: str) -> Optional[str]:
        e = self._ex(exercice_id)
        if not e["precedente"]:
            return None
        e["courante"], e["precedente"] = e["precedente"], None
        self.sauver()
        return e["courante"]

    def _elaguer(self, exercice_id: str) -> None:
        """Ne garde que la version courante et la précédente. Ne touche JAMAIS à donnees/."""
        e = self._ex(exercice_id)
        garder = {e["courante"], e["precedente"]}
        base = os.path.join(self.r.dossier_exercices, exercice_id)
        try:
            for v in os.listdir(base):
                if v not in garder:
                    shutil.rmtree(os.path.join(base, v), ignore_errors=True)
        except OSError:
            pass
