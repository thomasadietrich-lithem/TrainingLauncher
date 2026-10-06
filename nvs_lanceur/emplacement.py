"""Emplacement des DONNÉES du patient, HORS des données de l'application (décision du 06/10, chap. 16).

Pourquoi : installé depuis le Microsoft Store (MSIX), tout ce que l'application écrit dans %LOCALAPPDATA% est rangé dans
le dossier privé du paquet, que Windows EFFACE à la désinstallation. Les séances, réglages d'écran, consentements et
envois en attente vont donc dans un dossier visible choisi au premier lancement (par défaut
« Documents\\NeuroVision Solidaire »), que ni la désinstallation ni le lanceur ne suppriment jamais.

- Un fichier témoin `.neurovision_donnees.json` marque ce dossier : après une réinstallation, le dossier par défaut est
  retrouvé tout seul (aucune question, aucune donnée perdue).
- Le choix est mémorisé dans `emplacement_donnees.json` (dans la racine de l'application).
"""

from __future__ import annotations

import ctypes
import json
import os
import uuid
from typing import Callable, Optional

NOM_DOSSIER = "NeuroVision Solidaire"
TEMOIN = ".neurovision_donnees.json"
FICHIER_CHOIX = "emplacement_donnees.json"


def dossier_documents() -> str:
    """Dossier « Documents » réel de l'utilisateur (y compris redirigé vers OneDrive)."""
    env = os.environ.get("NVS_DOCUMENTS")
    if env:
        return env
    if os.name == "nt":  # pragma: no cover - Windows
        try:
            FOLDERID_Documents = uuid.UUID("{FDD39AD0-238F-46AF-ADB4-6C85480369C7}")

            class GUID(ctypes.Structure):
                _fields_ = [("Data1", ctypes.c_uint32), ("Data2", ctypes.c_uint16), ("Data3", ctypes.c_uint16),
                            ("Data4", ctypes.c_ubyte * 8)]

            g = GUID.from_buffer_copy(FOLDERID_Documents.bytes_le)
            chemin = ctypes.c_wchar_p()
            if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(g), 0, None, ctypes.byref(chemin)) == 0:
                valeur = chemin.value
                ctypes.windll.ole32.CoTaskMemFree(chemin)
                if valeur:
                    return valeur
        except Exception:
            pass
    return os.path.join(os.path.expanduser("~"), "Documents")


def dossier_par_defaut() -> str:
    return os.path.join(dossier_documents(), NOM_DOSSIER)


def est_dossier_donnees(chemin: str) -> bool:
    return bool(chemin) and os.path.isfile(os.path.join(chemin, TEMOIN))


def preparer(chemin: str) -> bool:
    """Crée le dossier et son témoin ; vérifie qu'on peut y écrire. False si impossible."""
    try:
        os.makedirs(chemin, exist_ok=True)
        t = os.path.join(chemin, TEMOIN)
        if not os.path.exists(t):
            with open(t, "w", encoding="utf-8") as f:
                json.dump({"role": "Données des exercices NeuroVision Solidaire — NE PAS SUPPRIMER",
                           "version": 1}, f, ensure_ascii=False, indent=2)
        essai = os.path.join(chemin, ".essai_ecriture")
        with open(essai, "w") as f:
            f.write("ok")
        os.remove(essai)
        return True
    except OSError:
        return False


def resoudre(racine: str, demander: Callable[[str], Optional[str]]) -> Optional[str]:
    """Renvoie le dossier de données à utiliser, ou None si le patient a quitté.

    demander(defaut) → chemin choisi (defaut si « Continuer »), ou None pour quitter.
    """
    choix = os.path.join(racine, FICHIER_CHOIX)
    try:
        with open(choix, encoding="utf-8") as f:
            memorise = json.load(f).get("dossier")
        if memorise and est_dossier_donnees(memorise) and preparer(memorise):
            return memorise
    except (OSError, ValueError):
        pass
    defaut = dossier_par_defaut()
    if est_dossier_donnees(defaut) and preparer(defaut):          # réinstallation : on retrouve les données
        _memoriser(racine, defaut)
        return defaut
    propose = defaut
    for _ in range(5):
        chemin = demander(propose)
        if chemin is None:
            return None
        if preparer(chemin):
            _memoriser(racine, chemin)
            return chemin
        propose = chemin   # dossier non inscriptible : on redemande
    return None


def _memoriser(racine: str, chemin: str) -> None:
    os.makedirs(racine, exist_ok=True)
    with open(os.path.join(racine, FICHIER_CHOIX), "w", encoding="utf-8") as f:
        json.dump({"dossier": chemin}, f, ensure_ascii=False, indent=2)
