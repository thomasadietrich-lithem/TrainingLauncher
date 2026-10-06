"""Manifeste signé : liste des exercices publiés et exigence de version du lanceur.

Format (schema 1) — fichier `canal/<canal>.json`, signature dans `canal/<canal>.json.sig` :

{
  "schema": 1, "canal": "stable", "sequence": 12, "publie_le": "2026-10-06T10:00:00Z",
  "exiger_authenticode": false,
  "lanceur": {"version": "1.0.0", "version_min": "1.0.0",
              "installeur": {"url": "installeur/1.0.0/Installer_NeuroVision.exe", "sha256": "…", "taille": 123}},
  "exercices": [
    {"id": "tilt_global", "nom": {"fr": "…", "en": "…"}, "version": "2.15.0", "moteur_requis": 1,
     "entree": "Fba_Training_Tilt_Global.py", "actif": true,
     "fichiers": [{"chemin": "Fba_Training_Tilt_Global.py",
                   "url": "exercices/tilt_global/2.15.0/Fba_Training_Tilt_Global.py",
                   "sha256": "…", "taille": 403912}]}
  ]
}

Signature : JSON {"cle": "<identifiant>", "signature": "<base64 Ed25519 des octets EXACTS du manifeste>"}.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from . import SCHEMA_MANIFESTE


class ManifesteInvalide(Exception):
    """Manifeste mal formé, non signé, mal signé ou incohérent : il est ignoré en bloc."""


_RE_ID = re.compile(r"^[a-z0-9_]{1,32}$")
_RE_VERSION = re.compile(r"^\d+(\.\d+){0,3}$")
_RE_SHA = re.compile(r"^[0-9a-f]{64}$")
_RE_CHEMIN = re.compile(r"^[A-Za-z0-9_\-][A-Za-z0-9_\-./]{0,199}$")


def version_tuple(v: str) -> Tuple[int, ...]:
    if not isinstance(v, str) or not _RE_VERSION.match(v):
        raise ManifesteInvalide(f"version illisible : {v!r}")
    return tuple(int(x) for x in v.split("."))


def _chemin_relatif_sur(p: str, quoi: str) -> str:
    """Chemin ou URL RELATIF, sans remontée ni schéma : impossible de pointer hors du canal ou du dossier."""
    if not isinstance(p, str) or not _RE_CHEMIN.match(p) or ".." in p.split("/") or "//" in p or p.startswith("/"):
        raise ManifesteInvalide(f"{quoi} refusé : {p!r}")
    return p


@dataclass(frozen=True)
class Fichier:
    chemin: str
    url: str
    sha256: str
    taille: int


@dataclass(frozen=True)
class Exercice:
    id: str
    version: str
    moteur_requis: int
    entree: str
    fichiers: Tuple[Fichier, ...]
    nom: Dict[str, str] = field(default_factory=dict)
    actif: bool = True

    def nom_affiche(self, langue: str) -> str:
        return self.nom.get(langue) or self.nom.get("fr") or self.id


@dataclass(frozen=True)
class Installeur:
    url: str
    sha256: str
    taille: int


@dataclass(frozen=True)
class Manifeste:
    sequence: int
    canal: str
    lanceur_version_min: str
    installeur: Optional[Installeur]
    exercices: Tuple[Exercice, ...]
    exiger_authenticode: bool
    brut: bytes          # octets exacts signés (conservés pour revérification hors ligne)
    signature: bytes     # contenu du fichier .sig

    def exercice(self, exercice_id: str) -> Optional[Exercice]:
        for e in self.exercices:
            if e.id == exercice_id:
                return e
        return None


def verifier_signature(brut: bytes, sig_brut: bytes, cles_publiques: Dict[str, str]) -> str:
    """Vérifie la signature Ed25519. Retourne l'identifiant de la clé utilisée. Lève ManifesteInvalide sinon."""
    try:
        sig = json.loads(sig_brut.decode("utf-8"))
        cle_id = str(sig["cle"])
        signature = base64.b64decode(sig["signature"], validate=True)
    except Exception as exc:
        raise ManifesteInvalide(f"fichier de signature illisible ({exc.__class__.__name__})") from None
    cle_b64 = cles_publiques.get(cle_id)
    if not cle_b64:
        raise ManifesteInvalide(f"clé de signature inconnue : {cle_id!r}")
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(cle_b64)).verify(signature, brut)
    except InvalidSignature:
        raise ManifesteInvalide("signature invalide") from None
    except ValueError as exc:
        raise ManifesteInvalide(f"clé publique invalide ({exc})") from None
    return cle_id


def _int(v, quoi: str, mini: int = 0) -> int:
    if not isinstance(v, int) or isinstance(v, bool) or v < mini:
        raise ManifesteInvalide(f"{quoi} invalide : {v!r}")
    return v


def _sha(v, quoi: str) -> str:
    if not isinstance(v, str) or not _RE_SHA.match(v):
        raise ManifesteInvalide(f"{quoi} : empreinte sha256 invalide")
    return v


def _lire_exercice(d: dict) -> Exercice:
    if not isinstance(d, dict):
        raise ManifesteInvalide("exercice mal formé")
    eid = d.get("id")
    if not isinstance(eid, str) or not _RE_ID.match(eid):
        raise ManifesteInvalide(f"identifiant d'exercice invalide : {eid!r}")
    version = d.get("version")
    version_tuple(version)
    entree = _chemin_relatif_sur(d.get("entree"), "point d'entrée")
    if not entree.endswith(".py"):
        raise ManifesteInvalide("le point d'entrée doit être un .py")
    fichiers = []
    vus = set()
    for f in d.get("fichiers") or []:
        if not isinstance(f, dict):
            raise ManifesteInvalide("fichier mal formé")
        ch = _chemin_relatif_sur(f.get("chemin"), "chemin de fichier")
        if ch in vus:
            raise ManifesteInvalide(f"fichier en double : {ch}")
        vus.add(ch)
        fichiers.append(Fichier(chemin=ch, url=_chemin_relatif_sur(f.get("url"), "url"),
                                sha256=_sha(f.get("sha256"), ch), taille=_int(f.get("taille"), "taille")))
    if entree not in vus:
        raise ManifesteInvalide(f"{eid} : le point d'entrée n'est pas dans la liste des fichiers")
    nom = d.get("nom") or {}
    if not isinstance(nom, dict):
        raise ManifesteInvalide("nom d'exercice mal formé")
    return Exercice(id=eid, version=version, moteur_requis=_int(d.get("moteur_requis"), "moteur_requis", 1),
                    entree=entree, fichiers=tuple(fichiers),
                    nom={str(k): str(v)[:80] for k, v in nom.items()}, actif=bool(d.get("actif", True)))


def lire_manifeste(brut: bytes, sig_brut: bytes, cles_publiques: Dict[str, str],
                   canal_attendu: Optional[str] = None) -> Manifeste:
    """Vérifie la signature PUIS valide le contenu. Rien n'est lu d'un manifeste non authentifié."""
    verifier_signature(brut, sig_brut, cles_publiques)
    try:
        d = json.loads(brut.decode("utf-8"))
    except Exception:
        raise ManifesteInvalide("manifeste illisible") from None
    if not isinstance(d, dict) or d.get("schema") != SCHEMA_MANIFESTE:
        raise ManifesteInvalide(f"schéma non pris en charge : {d.get('schema') if isinstance(d, dict) else '?'}")
    canal = d.get("canal")
    if canal_attendu is not None and canal != canal_attendu:
        raise ManifesteInvalide(f"canal inattendu : {canal!r}")
    lanceur = d.get("lanceur") or {}
    vmin = lanceur.get("version_min", "0")
    version_tuple(vmin)
    inst = None
    if lanceur.get("installeur"):
        i = lanceur["installeur"]
        inst = Installeur(url=_chemin_relatif_sur(i.get("url"), "url installeur"),
                          sha256=_sha(i.get("sha256"), "installeur"), taille=_int(i.get("taille"), "taille", 1))
    exercices: List[Exercice] = []
    ids = set()
    for e in d.get("exercices") or []:
        ex = _lire_exercice(e)
        if ex.id in ids:
            raise ManifesteInvalide(f"exercice en double : {ex.id}")
        ids.add(ex.id)
        exercices.append(ex)
    return Manifeste(sequence=_int(d.get("sequence"), "sequence", 1), canal=str(canal), lanceur_version_min=vmin,
                     installeur=inst, exercices=tuple(exercices),
                     exiger_authenticode=bool(d.get("exiger_authenticode", False)), brut=brut, signature=sig_brut)
