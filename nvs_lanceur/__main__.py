"""Point d'entrée : `NeuroVision.exe` (gelé) ou `python -m nvs_lanceur`.

  (sans argument)        démarrage normal patient
  --executer <entree>    processus enfant : exécute un exercice (usage interne)
  --auto-test [fichier]  vérification de fabrication (CI) : modules du moteur importables, clés lisibles
                         (résultat aussi écrit dans <fichier> : l'exécutable gelé n'a pas de console)
  --version              affiche version du lanceur et moteur
"""

from __future__ import annotations

import importlib
import json
import os
import sys


def _auto_test(sortie=None) -> int:
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
    lignes = [f"lanceur {VERSION}, moteur {MOTEUR}, python {sys.version.split()[0]}"]
    try:
        import psychopy
        lignes.append(f"psychopy {psychopy.__version__}")
    except Exception:
        pass
    lignes += [f"ÉCHEC {e}" for e in erreurs]
    lignes.append("AUTO-TEST " + ("OK" if not erreurs else "ÉCHEC"))
    if sys.stdout is not None:
        print("\n".join(lignes))
    if sortie:
        with open(sortie, "w", encoding="utf-8") as f:
            f.write("\n".join(lignes) + "\n")
    return 0 if not erreurs else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--executer"] and len(argv) >= 2:
        from .execution import executer_dans_ce_processus
        return executer_dans_ce_processus(argv[1])
    if argv[:1] == ["--auto-test"]:
        return _auto_test(argv[1] if len(argv) > 1 else None)
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
