"""Tests du lanceur (conteneur Linux) : serveur HTTP local, vraies signatures, vrais processus enfants.

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import base64
import functools
import http.server
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE_DEPOT = os.path.dirname(ICI)
sys.path.insert(0, RACINE_DEPOT)

from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402

from nvs_lanceur import MOTEUR  # noqa: E402
from nvs_lanceur import reseau  # noqa: E402
from nvs_lanceur.config import Reglages  # noqa: E402
from nvs_lanceur.execution import CODE_INCOMPATIBLE, Resultat  # noqa: E402
from nvs_lanceur.interface import Interface  # noqa: E402
from nvs_lanceur.lanceur import (ERR_EXERCICE_KO, ERR_PREMIERE_INSTALLATION, OK, SORTIE_MAJ_LANCEUR,  # noqa: E402
                                 Lanceur)
from nvs_lanceur.manifeste import ManifesteInvalide, lire_manifeste  # noqa: E402
from outils import publier  # noqa: E402
from outils.verifier_imports import verifier  # noqa: E402

import logging  # noqa: E402
logging.getLogger("nvs_lanceur").addHandler(logging.NullHandler())
logging.getLogger("nvs_lanceur").propagate = False

EXERCICE_REEL = os.environ.get(
    "NVS_EXERCICE_REEL", "/mnt/user-data/uploads/Session Design AWS - Reprise/Fba_Training_Tilt_Global.py")

# Exercice factice : se comporte comme l'exercice réel vis-à-vis du disque (sauvegarde locale dans NVS_DATA_DIR).
SCRIPT_OK = '''SOFTWARE_VERSION = "{v}"
import os, json, sys
base = os.environ.get("NVS_DATA_DIR") or os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(base, "session_data"), exist_ok=True)
os.makedirs(os.path.join(base, "config"), exist_ok=True)
p = os.path.join(base, "session_data", "seances.txt")
with open(p, "a", encoding="utf-8") as f:
    f.write("{v}|" + os.getcwd() + "\\n")
with open(os.path.join(base, "config", "envois_en_attente.json"), "w") as f:
    json.dump({{"en_attente": ["seance_{v}"]}}, f)
'''
SCRIPT_CASSE = 'SOFTWARE_VERSION = "{v}"\nimport module_absent_du_moteur\n'


class Serveur:
    def __init__(self, dossier):
        class Silencieux(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a, **k):
                pass
        h = functools.partial(Silencieux, directory=dossier)
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/logiciel/"
        self.t = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.t.start()

    def arreter(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class InterfaceTest(Interface):
    def __init__(self, choix=None):
        super().__init__("fr")
        self.messages = []
        self.choix = choix
        self.options_vues = None

    def progression(self, cle):
        self.messages.append(("prog", cle))

    def message(self, cle, **kw):
        self.messages.append(("msg", cle))

    def choisir(self, options):
        self.options_vues = list(options)
        return self.choix


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="nvs_test_")
        self.web = os.path.join(self.tmp, "web")
        self.canal = os.path.join(self.web, "logiciel")
        os.makedirs(self.canal)
        self.cles = os.path.join(self.tmp, "cles")
        os.makedirs(self.cles)
        self.cles_pub = os.path.join(self.tmp, "cles_publiques.json")
        self.pub = {}
        for cid in ("principale", "secours"):
            k = Ed25519PrivateKey.generate()
            with open(os.path.join(self.cles, f"{cid}.cle_privee"), "w") as f:
                f.write(base64.b64encode(k.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                                         serialization.NoEncryption())).decode())
            self.pub[cid] = base64.b64encode(k.public_key().public_bytes(
                serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()
        with open(self.cles_pub, "w") as f:
            json.dump({"cles": self.pub}, f)
        self.srv = Serveur(self.web)
        self.racine = os.path.join(self.tmp, "poste")
        self.sources = os.path.join(self.tmp, "sources")
        os.makedirs(self.sources)

    def tearDown(self):
        self.srv.arreter()
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- publication (vrai outil outils/publier.py)
    def publier(self, eid="tilt_global", v="2.15.0", script=SCRIPT_OK, cle_id="principale", extra=(), nom=None):
        src = os.path.join(self.sources, eid, v)
        os.makedirs(src, exist_ok=True)
        f = os.path.join(src, "exo.py")
        with open(f, "w") as fh:
            fh.write(script.format(v=v))
        prec = os.path.join(self.canal, "canal", "stable.json")
        args = ["--sortie", self.canal, "--cles-publiques", self.cles_pub, "--exercice", eid, "--fichier", f,
                "--cle", os.path.join(self.cles, f"{cle_id}.cle_privee"), "--cle-id", cle_id,
                "--nom-fr", nom or f"Exercice {eid}", "--sans-verif-imports"]
        if os.path.exists(prec):
            args += ["--manifeste-precedent", prec]
        self.assertEqual(publier.main(args + list(extra)), 0)

    def publier_options(self, *extra):
        prec = os.path.join(self.canal, "canal", "stable.json")
        self.assertEqual(publier.main(["--sortie", self.canal, "--cles-publiques", self.cles_pub,
                                       "--cle", os.path.join(self.cles, "principale.cle_privee"),
                                       "--manifeste-precedent", prec, *extra]), 0)

    def lanceur(self, ui=None, **kw):
        r = Reglages(racine=self.racine, url_base=self.srv.url, canal="stable", cles_publiques=dict(self.pub),
                     delai_reseau_s=3.0)
        return Lanceur(r, ui or InterfaceTest(), **kw)

    def seances(self, eid="tilt_global"):
        p = os.path.join(self.racine, "donnees", eid, "session_data", "seances.txt")
        if not os.path.exists(p):
            return []
        with open(p) as f:
            return [l.split("|")[0] for l in f.read().splitlines()]

    def manifeste_courant(self):
        p = os.path.join(self.canal, "canal", "stable.json")
        with open(p, "rb") as a, open(p + ".sig", "rb") as b:
            return a.read(), b.read()


class TestParcours(Base):
    def test_premiere_installation_et_sauvegarde_locale(self):
        self.publier(v="2.15.0")
        L = self.lanceur()
        self.assertEqual(L.demarrer(), OK)
        self.assertEqual(self.seances(), ["2.15.0"])
        # l'exercice tourne avec cwd = son dossier de données et y range config/ + session_data/
        donnees = os.path.join(self.racine, "donnees", "tilt_global")
        with open(os.path.join(donnees, "session_data", "seances.txt")) as f:
            self.assertEqual(os.path.realpath(f.read().split("|")[1].strip()), os.path.realpath(donnees))
        self.assertTrue(os.path.exists(os.path.join(donnees, "config", "envois_en_attente.json")))
        # rien n'est écrit dans le dossier du script
        self.assertFalse(os.path.exists(os.path.join(self.racine, "exercices", "tilt_global", "2.15.0",
                                                     "session_data")))

    def test_mise_a_jour_conserve_les_donnees(self):
        self.publier(v="2.15.0")
        self.lanceur().demarrer()
        self.publier(v="2.16.0")
        L = self.lanceur()
        self.assertEqual(L.demarrer(), OK)
        self.assertEqual(self.seances(), ["2.15.0", "2.16.0"])
        self.assertEqual(L.depot.courante("tilt_global"), "2.16.0")
        self.assertEqual(L.depot.precedente("tilt_global"), "2.15.0")
        # 3e version : la plus ancienne est élaguée, les données jamais
        self.publier(v="2.17.0")
        L = self.lanceur()
        L.demarrer()
        self.assertEqual(sorted(os.listdir(os.path.join(self.racine, "exercices", "tilt_global"))),
                         ["2.16.0", "2.17.0"])
        self.assertEqual(self.seances(), ["2.15.0", "2.16.0", "2.17.0"])

    def test_hors_ligne_utilise_la_version_installee(self):
        self.publier(v="2.15.0")
        self.lanceur().demarrer()
        self.srv.arreter()
        L = self.lanceur()
        L.r.url_base = "http://127.0.0.1:9/logiciel/"   # personne n'écoute
        self.assertEqual(L.demarrer(), OK)
        self.assertEqual(self.seances(), ["2.15.0", "2.15.0"])
        self.srv = Serveur(self.web)   # pour tearDown

    def test_premiere_installation_hors_ligne(self):
        L = self.lanceur()
        L.r.url_base = "http://127.0.0.1:9/logiciel/"
        ui = L.ui
        self.assertEqual(L.demarrer(), ERR_PREMIERE_INSTALLATION)
        self.assertIn(("msg", "premiere_install"), ui.messages)


class TestSecurite(Base):
    def test_manifeste_modifie_apres_signature_refuse(self):
        self.publier(v="2.15.0")
        self.lanceur().demarrer()
        self.publier(v="2.16.0")
        p = os.path.join(self.canal, "canal", "stable.json")
        with open(p, "rb") as f:
            brut = f.read()
        with open(p, "wb") as f:
            f.write(brut.replace(b'"2.16.0"', b'"2.16.1"', 1))
        L = self.lanceur()
        self.assertEqual(L.demarrer(), OK)
        self.assertEqual(L.depot.courante("tilt_global"), "2.15.0")

    def test_cle_inconnue_refusee(self):
        self.publier(v="2.15.0")
        brut, sig = self.manifeste_courant()
        autre = Ed25519PrivateKey.generate()
        fausse = json.dumps({"cle": "pirate", "signature": base64.b64encode(autre.sign(brut)).decode()}).encode()
        with self.assertRaises(ManifesteInvalide):
            lire_manifeste(brut, fausse, self.pub)
        fausse2 = json.dumps({"cle": "principale", "signature": base64.b64encode(autre.sign(brut)).decode()}).encode()
        with self.assertRaises(ManifesteInvalide):
            lire_manifeste(brut, fausse2, self.pub)

    def test_cle_de_secours_acceptee(self):
        self.publier(v="2.15.0", cle_id="secours")
        self.assertEqual(self.lanceur().demarrer(), OK)

    def test_rejeu_d_un_ancien_manifeste_refuse(self):
        self.publier(v="2.15.0")
        ancien = self.manifeste_courant()
        self.lanceur().demarrer()
        self.publier(v="2.16.0")
        self.lanceur().demarrer()
        p = os.path.join(self.canal, "canal", "stable.json")
        with open(p, "wb") as f:
            f.write(ancien[0])
        with open(p + ".sig", "wb") as f:
            f.write(ancien[1])
        L = self.lanceur()
        self.assertIsNone(L.obtenir_manifeste())
        L.demarrer()
        self.assertEqual(L.depot.courante("tilt_global"), "2.16.0")

    def test_fichier_modifie_sur_le_serveur_non_installe(self):
        self.publier(v="2.15.0")
        self.lanceur().demarrer()
        self.publier(v="2.16.0")
        f = os.path.join(self.canal, "exercices", "tilt_global", "2.16.0", "exo.py")
        with open(f, "a") as fh:
            fh.write("# piege\n")
        L = self.lanceur()
        self.assertEqual(L.demarrer(), OK)
        self.assertEqual(L.depot.courante("tilt_global"), "2.15.0")
        self.assertEqual(self.seances(), ["2.15.0", "2.15.0"])

    def test_fichier_modifie_sur_le_poste_refuse_puis_retour(self):
        self.publier(v="2.15.0")
        self.lanceur().demarrer()
        self.publier(v="2.16.0")
        self.lanceur().demarrer()
        f = os.path.join(self.racine, "exercices", "tilt_global", "2.16.0", "exo.py")
        with open(f, "a") as fh:
            fh.write("print('modifié')\n")
        L = self.lanceur()
        L.r.url_base = "http://127.0.0.1:9/logiciel/"     # hors ligne : pas de réparation possible
        self.assertEqual(L.demarrer(), OK)
        self.assertEqual(self.seances()[-1], "2.15.0")   # la version altérée n'a PAS été exécutée

    def test_chemins_hors_canal_refuses(self):
        self.publier(v="2.15.0")
        brut, _ = self.manifeste_courant()
        d = json.loads(brut)
        for mauvais in ("../../etc/passwd", "/abs/x.py", "https://pirate.example/x.py", "a//b.py"):
            d2 = json.loads(brut)
            d2["exercices"][0]["fichiers"][0]["url"] = mauvais
            b2 = json.dumps(d2).encode()
            k = Ed25519PrivateKey.from_private_bytes(base64.b64decode(
                open(os.path.join(self.cles, "principale.cle_privee")).read()))
            s2 = publier.signer(b2, k, "principale")
            with self.assertRaises(ManifesteInvalide, msg=mauvais):
                lire_manifeste(b2, s2, self.pub)
        self.assertTrue(d)

    def test_http_distant_refuse(self):
        with self.assertRaises(reseau.ErreurReseau):
            reseau.lire("http://exemple.org/logiciel/canal/stable.json", 100, 1.0)
        with self.assertRaises(reseau.ErreurReseau):
            reseau.joindre("https://d.cloudfront.net/logiciel/", "../autre/x")


class TestRetourArriere(Base):
    def test_version_cassee_retour_et_pas_de_nouvel_essai(self):
        self.publier(v="2.15.0")
        self.lanceur().demarrer()
        self.publier(v="2.16.0", script=SCRIPT_CASSE)
        ui = InterfaceTest()
        L = self.lanceur(ui)
        self.assertEqual(L.demarrer(), OK)
        self.assertIn(("msg", "echec_retour"), ui.messages)
        self.assertEqual(L.depot.courante("tilt_global"), "2.15.0")
        self.assertTrue(L.depot.est_en_echec("tilt_global", "2.16.0"))
        self.assertEqual(self.seances(), ["2.15.0", "2.15.0"])
        # relance avec le même manifeste : la version cassée n'est pas retéléchargée
        appels = []
        L2 = self.lanceur(executer=lambda e, d, i, v: (appels.append(v), Resultat(0, 1.0))[1])
        L2.demarrer()
        self.assertEqual(appels, ["2.15.0"])
        # un nouveau manifeste avec une version corrigée est installé
        self.publier(v="2.16.1")
        L3 = self.lanceur()
        self.assertEqual(L3.demarrer(), OK)
        self.assertEqual(L3.depot.courante("tilt_global"), "2.16.1")

    def test_premiere_version_cassee_sans_precedente(self):
        self.publier(v="2.15.0", script=SCRIPT_CASSE)
        ui = InterfaceTest()
        self.assertEqual(self.lanceur(ui).demarrer(), ERR_EXERCICE_KO)
        self.assertIn(("msg", "echec_total"), ui.messages)

    def test_erreur_tardive_pas_de_retour(self):
        self.publier(v="2.15.0")
        self.lanceur().demarrer()
        self.publier(v="2.16.0")
        L = self.lanceur(executer=lambda e, d, i, v: Resultat(1, 3600.0))   # plantage après 1 h d'exercice
        L.demarrer()
        self.assertEqual(L.depot.courante("tilt_global"), "2.16.0")

    def test_code_incompatible_enfant(self):
        self.publier(v="2.15.0", script=SCRIPT_CASSE)
        L = self.lanceur()
        L.mettre_a_jour_exercices(L.obtenir_manifeste())
        ex = L.depot.verifier_installee("tilt_global", "2.15.0")
        from nvs_lanceur.execution import lancer
        res = lancer(os.path.join(L.depot.dossier_version("tilt_global", "2.15.0"), ex.entree),
                     os.path.join(self.racine, "donnees", "t"), "tilt_global", "2.15.0")
        self.assertEqual(res.code, CODE_INCOMPATIBLE)


class TestMultiExercices(Base):
    def test_choix_et_donnees_separees(self):
        self.publier(eid="tilt_global", v="2.15.0", nom="Entraînement visuel")
        self.publier(eid="recherche_cible", v="1.0.0", nom="Recherche de cible")
        ui = InterfaceTest(choix="recherche_cible")
        L = self.lanceur(ui)
        self.assertEqual(L.demarrer(), OK)
        self.assertEqual(sorted(o[0] for o in ui.options_vues), ["recherche_cible", "tilt_global"])
        self.assertEqual(self.seances("recherche_cible"), ["1.0.0"])
        self.assertEqual(self.seances("tilt_global"), [])

    def test_quitter_depuis_le_choix(self):
        self.publier(eid="tilt_global", v="2.15.0")
        self.publier(eid="recherche_cible", v="1.0.0")
        self.assertEqual(self.lanceur(InterfaceTest(choix=None)).demarrer(), OK)
        self.assertEqual(self.seances(), [])

    def test_exercice_desactive_masque_donnees_gardees(self):
        self.publier(eid="tilt_global", v="2.15.0")
        self.publier(eid="recherche_cible", v="1.0.0")
        self.lanceur(InterfaceTest(choix="recherche_cible")).demarrer()
        self.publier_options("--desactiver", "recherche_cible")
        ui = InterfaceTest(choix="recherche_cible")
        self.assertEqual(self.lanceur(ui).demarrer(), OK)
        self.assertIsNone(ui.options_vues)                  # un seul exercice : pas de choix
        self.assertEqual(self.seances("tilt_global"), ["2.15.0"])
        self.assertEqual(self.seances("recherche_cible"), ["1.0.0"])   # données conservées

    def test_moteur_trop_recent_ignore(self):
        self.publier(v="2.15.0")
        self.lanceur().demarrer()
        self.publier(v="3.0.0", extra=("--moteur-requis", str(MOTEUR + 1)))
        L = self.lanceur()
        L.demarrer()
        self.assertEqual(L.depot.courante("tilt_global"), "2.15.0")


class TestAutoMiseAJour(Base):
    def _installeur(self, contenu=b"MZ faux installeur"):
        p = os.path.join(self.tmp, "Installer_NeuroVision.exe")
        with open(p, "wb") as f:
            f.write(contenu)
        return p

    def test_lanceur_trop_ancien_installe_puis_sort(self):
        self.publier(v="2.15.0")
        self.publier_options("--lanceur-version-min", "9.0.0", "--installeur", self._installeur(),
                             "--lanceur-version", "9.0.0")
        lances = []
        L = self.lanceur(installer_lanceur=lances.append)
        self.assertEqual(L.demarrer(), SORTIE_MAJ_LANCEUR)
        self.assertEqual(len(lances), 1)
        with open(lances[0], "rb") as f:
            self.assertEqual(f.read(), b"MZ faux installeur")
        self.assertEqual(self.seances(), [])

    def test_authenticode_exige_et_absent(self):
        self.publier(v="2.15.0")
        self.publier_options("--lanceur-version-min", "9.0.0", "--installeur", self._installeur(),
                             "--lanceur-version", "9.0.0", "--exiger-authenticode")
        lances = []
        L = self.lanceur(installer_lanceur=lances.append, verifier_authenticode=lambda p: False)
        self.assertEqual(L.demarrer(), OK)          # on continue avec ce qui est installé
        self.assertEqual(lances, [])

    def test_lanceur_a_jour_ne_reinstalle_pas(self):
        self.publier(v="2.15.0")
        self.publier_options("--lanceur-version-min", "1.0.0", "--installeur", self._installeur(),
                             "--lanceur-version", "1.0.0")
        lances = []
        self.assertEqual(self.lanceur(installer_lanceur=lances.append).demarrer(), OK)
        self.assertEqual(lances, [])


class TestContratMoteur(Base):
    def test_import_hors_moteur_detecte(self):
        f = os.path.join(self.tmp, "exo.py")
        with open(f, "w") as fh:
            fh.write("import os\nimport numpy as np\nfrom psychopy import visual, core\nimport requests\n"
                     "from psychopy import data\nimport psychopy.visual.shape\nfrom scipy import stats\n")
        fautes = verifier([f])
        self.assertEqual(len(fautes), 2, fautes)
        self.assertTrue(any("requests" in x for x in fautes))
        self.assertTrue(any("psychopy.data" in x for x in fautes))   # sous-module non figé dans le moteur

    def test_publication_refusee_si_import_hors_moteur(self):
        src = os.path.join(self.sources, "x.py")
        with open(src, "w") as fh:
            fh.write('SOFTWARE_VERSION = "1.0.0"\nimport pandas\n')
        with self.assertRaises(SystemExit):
            publier.main(["--sortie", self.canal, "--cles-publiques", self.cles_pub, "--exercice", "tilt_global",
                          "--fichier", src, "--cle", os.path.join(self.cles, "principale.cle_privee")])

    def test_version_non_croissante_refusee(self):
        self.publier(v="2.15.0")
        with self.assertRaises(SystemExit):
            self.publier(v="2.15.0")

    @unittest.skipUnless(os.path.exists(EXERCICE_REEL), "exercice réel non disponible")
    def test_exercice_reel_conforme_au_moteur(self):
        self.assertEqual(verifier([EXERCICE_REEL]), [])


if __name__ == "__main__":
    unittest.main()
