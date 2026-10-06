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
        m = json.load(f)
    return set(m["modules_autorises"]) | set(sys.stdlib_module_names) | {"__future__"}


def imports_de_premier_niveau(source: str) -> Set[str]:
    noms: Set[str] = set()
    for noeud in ast.walk(ast.parse(source)):
        if isinstance(noeud, ast.Import):
            noms.update(a.name.split(".")[0] for a in noeud.names)
        elif isinstance(noeud, ast.ImportFrom) and noeud.level == 0 and noeud.module:
            noms.add(noeud.module.split(".")[0])
    return noms


def verifier(fichiers: Iterable[str], moteur_json: str = MOTEUR_JSON) -> List[str]:
    fichiers = list(fichiers)
    autorises = modules_autorises(moteur_json)
    locaux = {os.path.splitext(os.path.basename(f))[0] for f in fichiers}
    for f in fichiers:   # paquets/modules livrés avec l'exercice
        d = os.path.dirname(os.path.abspath(f))
        for n in os.listdir(d):
            if n.endswith(".py") or os.path.isdir(os.path.join(d, n)):
                locaux.add(os.path.splitext(n)[0])
    fautes = []
    for f in fichiers:
        with open(f, encoding="utf-8") as fh:
            for nom in sorted(imports_de_premier_niveau(fh.read())):
                if nom not in autorises and nom not in locaux:
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
