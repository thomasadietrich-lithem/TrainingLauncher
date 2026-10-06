"""Prépare une publication signée du canal (chap. 16.4) : arborescence prête à déposer sous `logiciel/` du bucket.

Publier une nouvelle version d'un exercice (les autres exercices du manifeste précédent sont conservés) :

    python outils/publier.py --sortie A_DEPLOYER/logiciel --manifeste-precedent A_DEPLOYER/logiciel/canal/stable.json \
        --exercice tilt_global --fichier Fba_Training_Tilt_Global.py \
        --nom-fr "Entraînement visuel" --nom-en "Visual training" \
        --cle D:\\cle_nvs\\principale.cle_privee --cle-id principale

Options : --version (sinon lue dans SOFTWARE_VERSION du point d'entrée), --entree (sinon 1er --fichier),
--moteur-requis (sinon moteur courant), --desactiver <id>, --lanceur-version-min, --installeur <exe>
--lanceur-version, --exiger-authenticode, --canal. Clé privée : --cle <fichier> ou variable NVS_CLE_PRIVEE (CI).

Ordre de dépôt S3 (Thomas) : d'abord exercices/ et installeur/, EN DERNIER canal/<canal>.json puis .sig.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, ".."))

from nvs_lanceur import MOTEUR, SCHEMA_MANIFESTE  # noqa: E402
from nvs_lanceur.manifeste import lire_manifeste, version_tuple  # noqa: E402
from outils.verifier_imports import verifier  # noqa: E402


def sha256(chemin: str) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def charger_cle(chemin: str | None) -> Ed25519PrivateKey:
    if chemin:
        with open(chemin, encoding="ascii") as f:
            b64 = f.read()
    else:
        b64 = os.environ.get("NVS_CLE_PRIVEE")
    if not b64:
        raise SystemExit("clé privée absente (--cle ou NVS_CLE_PRIVEE)")
    return Ed25519PrivateKey.from_private_bytes(base64.b64decode(b64.strip()))


def lire_version(entree: str) -> str:
    with open(entree, encoding="utf-8") as f:
        m = re.search(r'^SOFTWARE_VERSION\s*=\s*["\']([\d.]+)["\']', f.read(), re.M)
    if not m:
        raise SystemExit("version introuvable : utilisez --version")
    return m.group(1)


def signer(brut: bytes, cle: Ed25519PrivateKey, cle_id: str) -> bytes:
    return json.dumps({"cle": cle_id, "signature": base64.b64encode(cle.sign(brut)).decode()}).encode("utf-8")


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sortie", required=True)
    p.add_argument("--canal", default="stable")
    p.add_argument("--manifeste-precedent")
    p.add_argument("--cles-publiques", default=os.path.join(ICI, "..", "nvs_lanceur", "cles_publiques.json"))
    p.add_argument("--exercice")
    p.add_argument("--fichier", action="append", default=[])
    p.add_argument("--entree")
    p.add_argument("--version")
    p.add_argument("--nom-fr")
    p.add_argument("--nom-en")
    p.add_argument("--moteur-requis", type=int, default=MOTEUR)
    p.add_argument("--desactiver", action="append", default=[])
    p.add_argument("--lanceur-version-min")
    p.add_argument("--installeur")
    p.add_argument("--lanceur-version")
    p.add_argument("--exiger-authenticode", action="store_true")
    p.add_argument("--cle")
    p.add_argument("--cle-id", default="principale")
    p.add_argument("--sans-verif-imports", action="store_true")
    a = p.parse_args(argv)

    with open(a.cles_publiques, encoding="utf-8") as f:
        cles_pub = json.load(f)["cles"]
    cle = charger_cle(a.cle)

    # Point de départ : le manifeste publié (vérifié) ou un manifeste vide.
    base = {"schema": SCHEMA_MANIFESTE, "canal": a.canal, "sequence": 0, "exiger_authenticode": False,
            "lanceur": {"version_min": "1.0.0"}, "exercices": []}
    if a.manifeste_precedent:
        with open(a.manifeste_precedent, "rb") as f:
            brut = f.read()
        with open(a.manifeste_precedent + ".sig", "rb") as f:
            lire_manifeste(brut, f.read(), cles_pub, canal_attendu=a.canal)   # refuse une base non authentique
        base = json.loads(brut.decode("utf-8"))

    sortie = os.path.abspath(a.sortie)
    exercices = {e["id"]: e for e in base.get("exercices", [])}

    if a.exercice:
        if not a.fichier:
            raise SystemExit("--fichier requis avec --exercice")
        entree_src = next((f for f in a.fichier if os.path.basename(f) == a.entree), a.fichier[0])
        if not a.sans_verif_imports:
            fautes = verifier([entree_src])
            if fautes:
                print("\n".join(fautes))
                raise SystemExit("publication refusée : imports hors moteur (contrat 16.4)")
        version = a.version or lire_version(entree_src)
        version_tuple(version)
        prec = exercices.get(a.exercice)
        if prec and version_tuple(version) <= version_tuple(prec["version"]):
            # les postes comparent la version : republier sous le même numéro ne serait jamais installé
            raise SystemExit(f"{a.exercice} : version {version} ≤ version publiée {prec['version']} "
                             "(augmenter SOFTWARE_VERSION)")
        dossier_rel = f"exercices/{a.exercice}/{version}"
        os.makedirs(os.path.join(sortie, dossier_rel), exist_ok=True)
        fichiers = []
        for src in a.fichier:
            nom = os.path.basename(src)
            dest = os.path.join(sortie, dossier_rel, nom)
            if os.path.abspath(src) != dest:
                shutil.copyfile(src, dest)
            fichiers.append({"chemin": nom, "url": f"{dossier_rel}/{nom}", "sha256": sha256(dest),
                             "taille": os.path.getsize(dest)})
        nom = dict((prec or {}).get("nom", {}))
        if a.nom_fr:
            nom["fr"] = a.nom_fr
        if a.nom_en:
            nom["en"] = a.nom_en
        exercices[a.exercice] = {"id": a.exercice, "nom": nom, "version": version, "moteur_requis": a.moteur_requis,
                                 "entree": os.path.basename(entree_src), "actif": True, "fichiers": fichiers}
    for eid in a.desactiver:
        if eid in exercices:
            exercices[eid]["actif"] = False

    lanceur = dict(base.get("lanceur", {}))
    if a.lanceur_version_min:
        version_tuple(a.lanceur_version_min)
        lanceur["version_min"] = a.lanceur_version_min
    if a.installeur:
        if not a.lanceur_version:
            raise SystemExit("--lanceur-version requis avec --installeur")
        rel = f"installeur/{a.lanceur_version}/Installer_NeuroVision.exe"
        dest = os.path.join(sortie, *rel.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(a.installeur, dest)
        lanceur["version"] = a.lanceur_version
        lanceur["installeur"] = {"url": rel, "sha256": sha256(dest), "taille": os.path.getsize(dest)}

    manifeste = {"schema": SCHEMA_MANIFESTE, "canal": a.canal, "sequence": int(base.get("sequence", 0)) + 1,
                 "publie_le": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "exiger_authenticode": bool(a.exiger_authenticode or base.get("exiger_authenticode", False)),
                 "lanceur": lanceur, "exercices": sorted(exercices.values(), key=lambda e: e["id"])}
    brut = json.dumps(manifeste, indent=2, ensure_ascii=False).encode("utf-8")
    sig = signer(brut, cle, a.cle_id)
    lire_manifeste(brut, sig, cles_pub, canal_attendu=a.canal)   # contrôle final avec les clés du lanceur
    os.makedirs(os.path.join(sortie, "canal"), exist_ok=True)
    with open(os.path.join(sortie, "canal", f"{a.canal}.json"), "wb") as f:
        f.write(brut)
    with open(os.path.join(sortie, "canal", f"{a.canal}.json.sig"), "wb") as f:
        f.write(sig)
    print(f"canal {a.canal} : sequence {manifeste['sequence']}, "
          + ", ".join(f"{e['id']} {e['version']}{'' if e['actif'] else ' (désactivé)'}" for e in manifeste["exercices"]))
    print("Dépôt S3 : exercices/ et installeur/ d'abord, canal/ EN DERNIER.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
