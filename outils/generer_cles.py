"""Génère une paire de clés Ed25519 et inscrit la clé PUBLIQUE dans nvs_lanceur/cles_publiques.json.

    python outils/generer_cles.py principale --sortie D:\\cle_nvs
    python outils/generer_cles.py secours    --sortie E:\\coffre

La clé PRIVÉE est écrite dans <sortie>/<id>.cle_privee (base64). Elle ne doit JAMAIS aller sur AWS, dans ce dépôt,
dans un mail ou dans le projet Claude. Pour GitHub Actions : la coller dans le secret NVS_CLE_PRIVEE d'un
environnement protégé (validation manuelle), puis effacer le fichier si la clé USB n'est pas la garde retenue.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ICI = os.path.dirname(os.path.abspath(__file__))
FICHIER_CLES = os.path.join(ICI, "..", "nvs_lanceur", "cles_publiques.json")


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("id", help="identifiant de la clé (ex. principale, secours)")
    p.add_argument("--sortie", required=True, help="dossier HORS du dépôt où écrire la clé privée")
    p.add_argument("--cles-publiques", default=FICHIER_CLES)
    a = p.parse_args(argv)
    depot = os.path.abspath(os.path.join(ICI, ".."))
    if os.path.abspath(a.sortie).startswith(depot):
        print("REFUS : la clé privée ne doit pas être écrite dans le dépôt.", file=sys.stderr)
        return 2
    os.makedirs(a.sortie, exist_ok=True)
    chemin_priv = os.path.join(a.sortie, f"{a.id}.cle_privee")
    if os.path.exists(chemin_priv):
        print(f"REFUS : {chemin_priv} existe déjà.", file=sys.stderr)
        return 2
    cle = Ed25519PrivateKey.generate()
    priv = cle.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                             serialization.NoEncryption())
    pub = cle.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    with open(chemin_priv, "w", encoding="ascii") as f:
        f.write(base64.b64encode(priv).decode())
    with open(a.cles_publiques, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("cles", {})[a.id] = base64.b64encode(pub).decode()
    with open(a.cles_publiques, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"clé privée : {chemin_priv}  (à garder HORS d'AWS et du dépôt)")
    print(f"clé publique « {a.id} » ajoutée à {os.path.normpath(a.cles_publiques)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
