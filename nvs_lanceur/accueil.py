"""Premier lancement : écran « identifiant requis » + avertissement santé et limitation de responsabilité à accepter
(exigences du dossier Microsoft Store, règles 10.1.1 et bonnes pratiques ; document directeur §16).

- Texte UNIQUE : `docs/AVERTISSEMENTS.md` du dépôt (le même que la page publique liée depuis la fiche Store), embarqué
  dans le lanceur. Partie française avant la ligne `---`, partie anglaise après.
- L'acceptation est mémorisée dans `accord_avertissements.json` (racine de l'application) avec l'EMPREINTE du texte :
  si le texte change, la question est reposée. Rien d'identifiant n'y est écrit (date + empreinte + langue).
- Sous MSIX, la racine de l'application est effacée à la désinstallation : après réinstallation, on redemande.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import sys
from typing import List, Optional, Tuple

NOM_TEXTE = "AVERTISSEMENTS.md"
NOM_ACCORD = "accord_avertissements.json"

# Une ligne affichée = (style, texte) ; style ∈ {"titre", "section", "texte"}
Ligne = Tuple[str, str]


def chemin_texte() -> Optional[str]:
    candidats = []
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        candidats.append(os.path.join(base, "nvs_lanceur", NOM_TEXTE))
    ici = os.path.dirname(os.path.abspath(__file__))
    candidats += [os.path.join(ici, NOM_TEXTE), os.path.join(os.path.dirname(ici), "docs", NOM_TEXTE)]
    for c in candidats:
        if os.path.isfile(c):
            return c
    return None


def _nettoyer(ligne: str) -> str:
    ligne = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", ligne)       # [texte](lien) → texte
    ligne = ligne.replace("**", "").replace("__", "")
    return ligne.strip()


def mettre_en_forme(md: str, langue: str) -> List[Ligne]:
    """Extrait la partie de la langue voulue et la convertit en lignes simples (sans syntaxe Markdown)."""
    parties = re.split(r"^\s*---\s*$", md, maxsplit=1, flags=re.M)
    texte = parties[1] if (langue == "en" and len(parties) > 1) else parties[0]
    lignes: List[Ligne] = []
    for brut in texte.splitlines():
        s = brut.strip()
        if not s:
            continue
        if re.fullmatch(r"\*[^*].*\*", s):                     # ligne en italique seule (« English version below »)
            continue
        if s.lower().startswith(("voir aussi", "see also")):
            continue
        if s.startswith("## "):
            lignes.append(("section", _nettoyer(s[3:])))
        elif s.startswith("# "):
            lignes.append(("titre", _nettoyer(s[2:])))
        else:
            lignes.append(("texte", _nettoyer(s)))
    return lignes


def charger(langue: str) -> Tuple[Optional[List[Ligne]], str]:
    """(lignes à afficher, empreinte du fichier) ; (None, "") si le texte est introuvable."""
    chemin = chemin_texte()
    if not chemin:
        return None, ""
    with open(chemin, "rb") as f:
        brut = f.read()
    return mettre_en_forme(brut.decode("utf-8"), langue), hashlib.sha256(brut).hexdigest()


def _fichier(racine: str) -> str:
    return os.path.join(racine, NOM_ACCORD)


def deja_accepte(racine: str, empreinte: str) -> bool:
    try:
        with open(_fichier(racine), encoding="utf-8") as f:
            return json.load(f).get("empreinte") == empreinte
    except (OSError, ValueError, AttributeError):
        return False


def enregistrer(racine: str, empreinte: str, langue: str) -> None:
    os.makedirs(racine, exist_ok=True)
    tmp = _fichier(racine) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"empreinte": empreinte, "langue": langue,
                   "accepte_le": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}, f)
    os.replace(tmp, _fichier(racine))
