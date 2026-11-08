"""Téléchargements : HTTPS uniquement (HTTP toléré seulement vers la machine locale, pour les tests),
taille plafonnée, empreinte vérifiée au fil de l'eau."""

from __future__ import annotations

import hashlib
import urllib.error
import urllib.parse
import urllib.request

from . import VERSION
from .config import est_fige


class ErreurReseau(Exception):
    pass


def joindre(url_base: str, relative: str) -> str:
    if not url_base.endswith("/"):
        url_base += "/"
    url = urllib.parse.urljoin(url_base, relative)
    if not url.startswith(url_base):          # double garde : le manifeste ne peut pas sortir du canal
        raise ErreurReseau(f"adresse hors du canal : {relative}")
    return url


def _verifier_schema(url: str) -> None:
    p = urllib.parse.urlparse(url)
    if p.scheme == "https":
        return
    if p.scheme == "http" and p.hostname in ("127.0.0.1", "localhost") and not est_fige():
        return                                # tests uniquement : jamais dans l'exécutable distribué (1.2.4)
    raise ErreurReseau(f"adresse non sécurisée refusée : {p.scheme}://{p.hostname}")


class _RedirectionsSurveillees(urllib.request.HTTPRedirectHandler):
    """1.2.4 (audit de sécurité du 08/11/2026, constat 5) : une redirection n'est suivie que vers la même adresse
    de base (même schéma, même serveur) ; toute autre est refusée."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        avant = urllib.parse.urlparse(req.full_url)
        apres = urllib.parse.urlparse(urllib.parse.urljoin(req.full_url, newurl))
        if (apres.scheme, apres.hostname, apres.port) != (avant.scheme, avant.hostname, avant.port):
            raise urllib.error.HTTPError(req.full_url, code, "redirection refusée", headers, fp)
        _verifier_schema(apres.geturl())
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OUVREUR = urllib.request.build_opener(_RedirectionsSurveillees)


def _ouvrir(url: str, delai: float):
    _verifier_schema(url)
    req = urllib.request.Request(url, headers={"User-Agent": f"NeuroVision-Lanceur/{VERSION}",
                                               "Cache-Control": "no-cache"})
    try:
        return _OUVREUR.open(req, timeout=delai)
    except urllib.error.HTTPError as exc:
        raise ErreurReseau(f"HTTP {exc.code}") from None
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise ErreurReseau(f"réseau indisponible ({exc.__class__.__name__})") from None


def lire(url: str, taille_max: int, delai: float) -> bytes:
    with _ouvrir(url, delai) as rep:
        try:
            data = rep.read(taille_max + 1)
        except OSError as exc:
            raise ErreurReseau(f"lecture interrompue ({exc.__class__.__name__})") from None
    if len(data) > taille_max:
        raise ErreurReseau("réponse trop volumineuse")
    return data


def telecharger(url: str, destination: str, taille_attendue: int, sha256_attendu: str, delai: float) -> None:
    h = hashlib.sha256()
    total = 0
    with _ouvrir(url, delai) as rep, open(destination, "wb") as f:
        while True:
            try:
                bloc = rep.read(1 << 16)
            except OSError as exc:
                raise ErreurReseau(f"téléchargement interrompu ({exc.__class__.__name__})") from None
            if not bloc:
                break
            total += len(bloc)
            if total > taille_attendue:
                raise ErreurReseau("fichier plus gros qu'annoncé")
            h.update(bloc)
            f.write(bloc)
    if total != taille_attendue or h.hexdigest() != sha256_attendu:
        raise ErreurReseau("fichier corrompu ou modifié (empreinte incorrecte)")
