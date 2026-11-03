"""Préférences du lanceur, dans la racine de l'application : aujourd'hui la langue choisie au premier lancement.

`preferences_lanceur.json` = {"langue": "fr" | "en"}. Rien d'identifiant. Écriture atomique.
Les postes déjà installés (lanceur ≤ 1.1.1) n'ont pas ce fichier : on reprend alors la langue enregistrée avec
l'acceptation des avertissements (`accord_avertissements.json`), sans reposer la question.
"""

from __future__ import annotations

import json
import os
from typing import Optional

NOM = "preferences_lanceur.json"
LANGUES = ("fr", "en")


def _lire(chemin: str) -> dict:
    try:
        with open(chemin, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def lire_langue(racine: str) -> Optional[str]:
    langue = _lire(os.path.join(racine, NOM)).get("langue")
    if langue in LANGUES:
        return langue
    from .accueil import NOM_ACCORD
    langue = _lire(os.path.join(racine, NOM_ACCORD)).get("langue")
    return langue if langue in LANGUES else None


def enregistrer_langue(racine: str, langue: str) -> None:
    if langue not in LANGUES:
        raise ValueError(langue)
    os.makedirs(racine, exist_ok=True)
    chemin = os.path.join(racine, NOM)
    d = _lire(chemin)
    d["langue"] = langue
    tmp = chemin + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f)
    os.replace(tmp, chemin)


def langue_argument(argv) -> Optional[str]:
    """`--langue=fr` ou `--langue fr` (passé par l'installeur à la fin de l'installation)."""
    argv = list(argv)
    for i, a in enumerate(argv):
        if a.startswith("--langue="):
            v = a.split("=", 1)[1]
        elif a == "--langue" and i + 1 < len(argv):
            v = argv[i + 1]
        else:
            continue
        v = v.strip().lower()[:2]
        return v if v in LANGUES else None
    return None
