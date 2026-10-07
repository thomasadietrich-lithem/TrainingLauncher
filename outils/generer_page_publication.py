"""Génère outils/Publier_NVS.html (publication signée dans le navigateur, sans Python) à partir de
outils/modele_publier.html, en y inscrivant les clés publiques, le moteur et la liste des modules autorisés.

    python outils/generer_page_publication.py            (à relancer si cles_publiques.json ou moteur.json change)
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)


def generer(cles_publiques: str, moteur_json: str, sortie: str) -> None:
    with open(os.path.join(ICI, "modele_publier.html"), encoding="utf-8") as f:
        html = f.read()
    with open(cles_publiques, encoding="utf-8") as f:
        cles = json.load(f)["cles"]
    with open(moteur_json, encoding="utf-8") as f:
        moteur = json.load(f)
    remplacements = {
        "__CLES_PUBLIQUES__": json.dumps(cles),
        "__MOTEUR__": str(int(moteur["moteur"])),
        "__MODULES_AUTORISES__": json.dumps(moteur["modules_autorises"]),
        "__STDLIB__": json.dumps(sorted(sys.stdlib_module_names)),
    }
    for k, v in remplacements.items():
        assert k in html, k
        html = html.replace(k, v)
    with open(sortie, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--cles-publiques", default=os.path.join(RACINE, "nvs_lanceur", "cles_publiques.json"))
    p.add_argument("--moteur", default=os.path.join(RACINE, "nvs_lanceur", "moteur.json"))
    p.add_argument("--sortie", default=os.path.join(ICI, "Publier_NVS.html"))
    a = p.parse_args(argv)
    generer(a.cles_publiques, a.moteur, a.sortie)
    print(a.sortie)
    return 0


if __name__ == "__main__":
    sys.exit(main())
