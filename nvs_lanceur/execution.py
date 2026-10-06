"""Exécution d'un exercice dans un processus séparé (le lanceur reste en vie pour revenir en arrière si besoin).

Le processus enfant est le même exécutable relancé avec `--executer <entree>` : il dispose ainsi des bibliothèques
figées du moteur. Codes de sortie de l'enfant :
  0   fin normale (ou code renvoyé par l'exercice lui-même via SystemExit)
  1   exception non rattrapée pendant l'exécution
  3   exercice incompatible avec ce moteur (ImportError, SyntaxError) → retour arrière immédiat
"""

from __future__ import annotations

import os
import runpy
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass
from typing import Dict, List

from . import MOTEUR, VERSION

CODE_EXCEPTION = 1
CODE_INCOMPATIBLE = 3


@dataclass
class Resultat:
    code: int
    duree_s: float


def commande_enfant(entree: str) -> List[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--executer", entree]
    return [sys.executable, "-m", "nvs_lanceur", "--executer", entree]


def environnement_enfant(dossier_donnees: str, exercice_id: str, version: str) -> Dict[str, str]:
    env = dict(os.environ)
    env.update({
        "NVS_DATA_DIR": dossier_donnees,          # l'exercice y range config/ et session_data/ (chap. 16.4 a)
        "NVS_LANCEUR_VERSION": VERSION,
        "NVS_MOTEUR": str(MOTEUR),
        "NVS_EXERCICE_ID": exercice_id,
        "NVS_EXERCICE_VERSION": version,
    })
    if not getattr(sys, "frozen", False):
        # en mode source, l'enfant doit retrouver le paquet nvs_lanceur
        racine_paquet = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env["PYTHONPATH"] = racine_paquet + os.pathsep + env.get("PYTHONPATH", "")
    return env


def lancer(entree: str, dossier_donnees: str, exercice_id: str, version: str) -> Resultat:
    os.makedirs(dossier_donnees, exist_ok=True)
    debut = time.monotonic()
    proc = subprocess.run(commande_enfant(entree), cwd=dossier_donnees,
                          env=environnement_enfant(dossier_donnees, exercice_id, version))
    return Resultat(code=proc.returncode, duree_s=time.monotonic() - debut)


def executer_dans_ce_processus(entree: str) -> int:
    """Côté enfant : exécute le script comme `python entree`."""
    entree = os.path.abspath(entree)
    sys.argv = [entree]
    sys.path.insert(0, os.path.dirname(entree))
    try:
        runpy.run_path(entree, run_name="__main__")
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else (0 if code is None else 1)
    except (ImportError, SyntaxError):
        traceback.print_exc()
        return CODE_INCOMPATIBLE
    except Exception:
        traceback.print_exc()
        return CODE_EXCEPTION
    return 0


def echec_au_demarrage(res: Resultat, delai_s: float) -> bool:
    if res.code == CODE_INCOMPATIBLE:
        return True
    return res.code == CODE_EXCEPTION and res.duree_s < delai_s
