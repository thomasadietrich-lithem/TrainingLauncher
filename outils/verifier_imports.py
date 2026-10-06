"""Contrat moteur (chap. 16.4) : un exercice n'importe que la bibliothèque standard + les modules du moteur.

    python outils/verifier_imports.py chemin/vers/exercice.py [autres.py…]

Code de sortie 0 si conforme, 1 sinon (liste des imports hors moteur). Utilisé en CI et par publier.py.
Les imports relatifs et les modules fournis par l'exercice lui-même (fichiers voisins) sont autorisés.
"""

from __future__ import annotations

import ast
import json
import os
import sys
from typing import Iterable, List, Set

ICI = os.path.dirname(os.path.abspath(__file__))
MOTEUR_JSON = os.path.join(ICI, "..", "nvs_lanceur", "moteur.json")


def modules_autorises(moteur_json: str = MOTEUR_JSON) -> Set[str]:
    with open(moteur_json, encoding="utf-8") as f:
        return set(json.load(f)["modules_autorises"])


def imports(source: str) -> Set[str]:
    """Noms complets importés : « import a.b » → a.b ; « from psychopy import visual » → psychopy.visual."""
    noms: Set[str] = set()
    for noeud in ast.walk(ast.parse(source)):
        if isinstance(noeud, ast.Import):
            noms.update(a.name for a in noeud.names)
        elif isinstance(noeud, ast.ImportFrom) and noeud.level == 0 and noeud.module:
            if noeud.module in ("psychopy",):          # paquet « parapluie » : on contrôle chaque sous-module
                noms.update(f"psychopy.{a.name}" for a in noeud.names)
            else:
                noms.add(noeud.module)
    return noms


def _autorise(nom: str, autorises: Set[str], locaux: Set[str]) -> bool:
    racine = nom.split(".")[0]
    if racine in sys.stdlib_module_names or racine == "__future__" or racine in locaux:
        return True
    if nom == "psychopy":
        return True
    return any(nom == a or nom.startswith(a + ".") for a in autorises)


def verifier(fichiers: Iterable[str], moteur_json: str = MOTEUR_JSON) -> List[str]:
    fichiers = list(fichiers)
    autorises = modules_autorises(moteur_json)
    locaux: Set[str] = set()
    for f in fichiers:   # modules livrés avec l'exercice (fichiers voisins)
        d = os.path.dirname(os.path.abspath(f))
        for n in os.listdir(d):
            if n.endswith(".py"):
                locaux.add(n[:-3])
    fautes = []
    for f in fichiers:
        with open(f, encoding="utf-8") as fh:
            for nom in sorted(imports(fh.read())):
                if not _autorise(nom, autorises, locaux):
                    fautes.append(f"{os.path.basename(f)} : import « {nom} » hors moteur")
    return fautes


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 2
    fautes = verifier(argv)
    for x in fautes:
        print("ÉCHEC", x)
    print("IMPORTS", "OK" if not fautes else f"ÉCHEC ({len(fautes)})")
    return 0 if not fautes else 1


if __name__ == "__main__":
    sys.exit(main())
