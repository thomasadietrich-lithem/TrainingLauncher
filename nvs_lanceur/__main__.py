"""Point d'entrée : `NeuroVision.exe` (gelé) ou `python -m nvs_lanceur`.

  (sans argument)        démarrage normal patient
  --executer <entree>    processus enfant : exécute un exercice (usage interne)
  --auto-test            vérification de fabrication (CI) : modules du moteur importables, clés lisibles
  --version              affiche version du lanceur et moteur
"""

from __future__ import annotations

import importlib
import json
import os
import sys


def _auto_test() -> int:
    from . import MOTEUR, VERSION
    from .config import _dossier_ressources, charger_cles_publiques
    erreurs = []
    try:
        cles = charger_cles_publiques()
        print(f"clés publiques : {len(cles)}")
    except Exception as exc:
        erreurs.append(f"clés publiques : {exc}")
    chemin = os.path.join(_dossier_ressources(), "moteur.json")
    try:
        with open(chemin, encoding="utf-8") as f:
            moteur = json.load(f)
        if moteur.get("moteur") != MOTEUR:
            erreurs.append(f"moteur.json = {moteur.get('moteur')} mais MOTEUR = {MOTEUR}")
        for mod in moteur.get("modules_a_verifier", []):
            try:
                importlib.import_module(mod)
            except Exception as exc:
                erreurs.append(f"import {mod} : {exc.__class__.__name__}: {exc}")
    except OSError as exc:
        erreurs.append(f"moteur.json : {exc}")
    print(f"lanceur {VERSION}, moteur {MOTEUR}")
    for e in erreurs:
        print("ÉCHEC", e)
    print("AUTO-TEST", "OK" if not erreurs else "ÉCHEC")
    return 0 if not erreurs else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--executer"] and len(argv) >= 2:
        from .execution import executer_dans_ce_processus
        return executer_dans_ce_processus(argv[1])
    if argv[:1] == ["--auto-test"]:
        return _auto_test()
    if argv[:1] == ["--version"]:
        from . import MOTEUR, VERSION
        print(f"{VERSION} (moteur {MOTEUR})")
        return 0
    from .config import Reglages, charger_cles_publiques
    from .interface import interface_par_defaut
    from .lanceur import Lanceur, configurer_journal
    reglages = Reglages(cles_publiques=charger_cles_publiques())
    configurer_journal(reglages)
    return Lanceur(reglages, interface_par_defaut()).demarrer()


if __name__ == "__main__":
    sys.exit(main())
