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
# Adresse de contact affichée sur l'écran « identifiant requis » (premier lancement). Vide = « adressez-vous à la
# personne qui vous a proposé cet entraînement ». À renseigner dès que l'adresse dédiée existe (dossier Store).
CONTACT_EMAIL = "thomas.a.dietrich@gmail.com"   # contact définitif (Thomas, 03/11/2026)

NOM_DOSSIER = "NeuroVisionSolidaire"

# 1.2.4 (audit de sécurité du 08/11/2026, constat 3) : plus petite séquence de manifeste acceptée, même sur un poste
# neuf. Empêche de rejouer un ancien manifeste signé (ancien exercice) sur une nouvelle installation. = séquence en
# ligne à la fabrication de cette version (stable n° 8, exercice 2.18.3, 07/11/2026). À relever à chaque version.
SEQUENCE_MIN = 8


def est_fige() -> bool:
    """True dans l'exécutable distribué (PyInstaller) : les réglages de test par variables d'environnement y sont
    ignorés (audit de sécurité du 08/11/2026, constat 6)."""
    return bool(getattr(sys, "frozen", False))


def env_de_test(nom: str) -> Optional[str]:
    """Variable d'environnement réservée aux tests (NVS_URL_BASE, NVS_CANAL, NVS_RACINE, NVS_DOCUMENTS) :
    lue seulement hors de l'exécutable distribué."""
    if est_fige():
        return None
    return os.environ.get(nom) or None


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
    env = env_de_test("NVS_RACINE")
    if env:
        return env
    base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, NOM_DOSSIER)


@dataclass
class Reglages:
    racine: str = field(default_factory=racine_par_defaut)
    url_base: str = field(default_factory=lambda: env_de_test("NVS_URL_BASE") or URL_BASE_DEFAUT)
    canal: str = field(default_factory=lambda: env_de_test("NVS_CANAL") or CANAL_DEFAUT)
    cles_publiques: Dict[str, str] = field(default_factory=dict)
    delai_reseau_s: float = DELAI_RESEAU_S
    delai_echec_demarrage_s: float = DELAI_ECHEC_DEMARRAGE_S
    sequence_min: int = SEQUENCE_MIN
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
    def fichier_langue_retour(self) -> str:
        """Langue choisie DANS l'exercice (liste de la fenêtre de connexion), rendue au lanceur (contrat §16.4)."""
        return os.path.join(self.racine, "langue_retour.txt")

    @property
    def dossier_temp(self) -> str:
        return os.path.join(self.racine, "temp")

    def donnees_exercice(self, exercice_id: str) -> str:
        return os.path.join(self.dossier_donnees, exercice_id)
