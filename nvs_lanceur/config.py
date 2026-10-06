"""Réglages du lanceur : adresses, clés publiques, emplacements sur le PC du patient."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Optional

# Canal de publication (CloudFront du portail, préfixe logiciel/). Surchargé par NVS_URL_BASE (tests, canal pilote).
URL_BASE_DEFAUT = "https://d2ip5ef1wmcekr.cloudfront.net/logiciel/"
CANAL_DEFAUT = "stable"

DELAI_RESEAU_S = 8.0
TAILLE_MAX_MANIFESTE = 256 * 1024
TAILLE_MAX_FICHIER = 64 * 1024 * 1024          # un fichier d'exercice
TAILLE_MAX_INSTALLEUR = 1024 * 1024 * 1024

# Un exercice qui s'arrête en erreur moins de DELAI_ECHEC_DEMARRAGE_S secondes après son lancement est considéré
# comme « en échec au démarrage » → retour à la version précédente.
DELAI_ECHEC_DEMARRAGE_S = 60.0

NOM_DOSSIER = "NeuroVisionSolidaire"


def _dossier_ressources() -> str:
    """Dossier des fichiers embarqués (gelé par PyInstaller ou source)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, "nvs_lanceur")
    return os.path.dirname(os.path.abspath(__file__))


def charger_cles_publiques(chemin: str | None = None) -> Dict[str, str]:
    """Clés publiques Ed25519 de confiance {identifiant: clé base64}. Principale + secours."""
    chemin = chemin or os.path.join(_dossier_ressources(), "cles_publiques.json")
    with open(chemin, "r", encoding="utf-8") as f:
        data = json.load(f)
    cles = data.get("cles", {})
    if not isinstance(cles, dict) or not cles:
        raise ValueError("aucune clé publique de confiance")
    return {str(k): str(v) for k, v in cles.items()}


def racine_par_defaut() -> str:
    env = os.environ.get("NVS_RACINE")
    if env:
        return env
    base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, NOM_DOSSIER)


@dataclass
class Reglages:
    racine: str = field(default_factory=racine_par_defaut)
    url_base: str = field(default_factory=lambda: os.environ.get("NVS_URL_BASE", URL_BASE_DEFAUT))
    canal: str = field(default_factory=lambda: os.environ.get("NVS_CANAL", CANAL_DEFAUT))
    cles_publiques: Dict[str, str] = field(default_factory=dict)
    delai_reseau_s: float = DELAI_RESEAU_S
    delai_echec_demarrage_s: float = DELAI_ECHEC_DEMARRAGE_S
    donnees: Optional[str] = None   # dossier de données choisi (emplacement.resoudre) ; HORS des données de l'appli

    # Arborescence (chap. 16.2). « donnees » n'est JAMAIS effacé ni déplacé par le lanceur.
    @property
    def dossier_exercices(self) -> str:
        return os.path.join(self.racine, "exercices")

    @property
    def dossier_donnees(self) -> str:
        return self.donnees or os.path.join(self.racine, "donnees")

    @property
    def fichier_etat(self) -> str:
        return os.path.join(self.racine, "etat.json")

    @property
    def fichier_journal(self) -> str:
        return os.path.join(self.racine, "journal_lanceur.log")

    @property
    def fichier_journal_enfant(self) -> str:
        return os.path.join(self.racine, "journal_erreurs_exercices.log")

    @property
    def dossier_temp(self) -> str:
        return os.path.join(self.racine, "temp")

    def donnees_exercice(self, exercice_id: str) -> str:
        return os.path.join(self.dossier_donnees, exercice_id)
