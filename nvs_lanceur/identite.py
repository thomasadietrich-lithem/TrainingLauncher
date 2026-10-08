"""Identité visuelle des fenêtres : l'icône NeuroVision (œil) remplace l'icône générique en haut à gauche.

- Fenêtres du lanceur (Tk) : `appliquer_tk(racine)` — `iconbitmap(default=…)` vaut pour toutes les fenêtres filles.
- Fenêtres de l'exercice (boîtes de dialogue PsychoPy = Qt) : `preparer_qt()` est appelé dans le processus enfant
  AVANT l'exercice ; il enveloppe `psychopy.gui.qtgui.ensureQtApp` pour poser l'icône sur l'application Qt dès sa
  création par PsychoPy (on ne crée surtout pas l'application nous-mêmes : PsychoPy y applique son style « Fusion »).
  Ainsi aucun exercice n'a à s'en occuper, et tous les exercices futurs en profitent.
Tout est « au mieux » : une icône absente ou une version de PsychoPy différente ne doit jamais empêcher un lancement.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

NOM_ICONE = "neurovision.ico"


def chemin_icone() -> Optional[str]:
    candidats = []
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        candidats.append(os.path.join(base, "nvs_lanceur", NOM_ICONE))
    ici = os.path.dirname(os.path.abspath(__file__))
    candidats += [os.path.join(ici, NOM_ICONE), os.path.join(os.path.dirname(ici), "installeur", NOM_ICONE)]
    for c in candidats:
        if os.path.isfile(c):
            return c
    return None


def appliquer_tk(racine) -> bool:
    ico = chemin_icone()
    if not ico or os.name != "nt":          # .ico = Windows ; ailleurs on garde l'icône par défaut
        return False
    try:
        racine.iconbitmap(default=ico)
        return True
    except Exception:
        return False


def _envelopper_qtgui(qtgui, ico: str) -> bool:
    origine = getattr(qtgui, "ensureQtApp", None)
    if origine is None or getattr(origine, "_nvs_icone", False):
        return False

    def ensure_qt_app_nvs(*args, **kwargs):
        resultat = origine(*args, **kwargs)
        try:
            app = qtgui.QtWidgets.QApplication.instance()
            if app is not None:
                app.setWindowIcon(qtgui.QtGui.QIcon(ico))
        except Exception:
            pass
        return resultat

    ensure_qt_app_nvs._nvs_icone = True
    qtgui.ensureQtApp = ensure_qt_app_nvs
    return True


class _CrochetQtgui:
    """Chercheur d'import : n'intervient qu'au moment où l'exercice importe lui-même psychopy.gui.qtgui
    (on ne change donc ni l'ordre ni le moment des imports de l'exercice)."""

    CIBLE = "psychopy.gui.qtgui"

    def __init__(self, ico: str):
        self.ico = ico

    def find_spec(self, nom, chemin=None, cible=None):
        if nom != self.CIBLE:
            return None
        for chercheur in sys.meta_path:
            if chercheur is self or not hasattr(chercheur, "find_spec"):
                continue
            spec = chercheur.find_spec(nom, chemin, cible)
            if spec is None:
                continue
            if spec.loader is not None and hasattr(spec.loader, "exec_module"):
                spec.loader = _ChargeurEnveloppe(spec.loader, self.ico)   # le chargeur d'origine reste intact
            return spec
        return None


class _ChargeurEnveloppe:
    def __init__(self, chargeur, ico: str):
        self._chargeur = chargeur
        self._ico = ico

    def create_module(self, spec):
        return self._chargeur.create_module(spec) if hasattr(self._chargeur, "create_module") else None

    def exec_module(self, module):
        self._chargeur.exec_module(module)
        try:
            _envelopper_qtgui(module, self._ico)
        except Exception:
            pass

    def __getattr__(self, nom):
        return getattr(self._chargeur, nom)


def preparer_qt() -> bool:
    """Côté enfant, avant l'exercice : l'icône sera posée dès que PsychoPy créera son application Qt."""
    ico = chemin_icone()
    if not ico:
        return False
    try:
        module = sys.modules.get(_CrochetQtgui.CIBLE)
        if module is not None:
            return _envelopper_qtgui(module, ico)
        if not any(isinstance(c, _CrochetQtgui) for c in sys.meta_path):
            sys.meta_path.insert(0, _CrochetQtgui(ico))
        return True
    except Exception:
        return False
