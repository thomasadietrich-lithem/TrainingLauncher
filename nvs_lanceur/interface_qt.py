"""Fenêtres du lanceur en Qt, construites comme les boîtes de dialogue de l'exercice (demande de Thomas, 03/11).

Même moteur graphique que les fenêtres de l'exercice (PyQt du moteur, style « Fusion » posé par PsychoPy), même
construction que `_new_dlg` / `_habiller_fenetre` du script : largeur fixe 680 px, grille espacée de 10 px, texte riche
(titre <h3>, paragraphes), logo de l'association en tête, bouton « Quitter » / « ‹ Retour » à GAUCHE et bouton
d'action à DROITE. On n'importe PAS PsychoPy ici (le lanceur reste léger) : seulement PyQt, déjà dans le moteur.

Le lanceur et l'exercice tournent dans deux processus distincts : l'application Qt créée ici n'est jamais vue par
l'exercice. Aucune logique métier ici ; repli sur Tk puis console si Qt est indisponible (interface_par_defaut).
"""

from __future__ import annotations

import html
import os
import sys
from typing import List, Optional, Sequence, Tuple

from .interface import LANGUE_QUITTER, TEXTES, Interface

QtWidgets = QtGui = QtCore = None
for _nom in ("PyQt6", "PyQt5"):
    try:
        QtWidgets = __import__(_nom + ".QtWidgets", fromlist=["QtWidgets"])
        QtGui = __import__(_nom + ".QtGui", fromlist=["QtGui"])
        QtCore = __import__(_nom + ".QtCore", fromlist=["QtCore"])
        break
    except Exception:
        QtWidgets = QtGui = QtCore = None

LARGEUR_FENETRE = 680          # DLG_WIDTH_PX de l'exercice
LARGEUR_TEXTE = 620            # MESSAGE_BOX_MAX_WIDTH_PX de l'exercice
LOGO_PX = (300, 76)            # LOGO_DISPLAY_PX de l'exercice
NOM_LOGO = "logo.png"


def qt_disponible() -> bool:
    return QtWidgets is not None


def chemin_logo() -> Optional[str]:
    candidats = []
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        candidats.append(os.path.join(base, "nvs_lanceur", NOM_LOGO))
    candidats.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), NOM_LOGO))
    for c in candidats:
        if os.path.isfile(c):
            return c.replace("\\", "/")
    return None


def _enum(classe, groupe: str, nom: str):
    """PyQt6 : énumérations imbriquées (QDialogButtonBox.ButtonRole.ResetRole) ; PyQt5 : attributs directs."""
    return getattr(getattr(classe, groupe, classe), nom)


def html_avertissements(lignes) -> str:
    """Lignes (style, texte) de accueil.mettre_en_forme → texte riche Qt (sans le grand titre, déjà dans la fenêtre)."""
    morceaux = []
    for style, texte in lignes:
        t = html.escape(texte)
        if style == "titre":
            continue
        if style == "section":
            morceaux.append(f"<p style='margin-top:10px; margin-bottom:4px'><b>{t}</b></p>")
        else:
            morceaux.append(f"<p style='margin-top:0; margin-bottom:6px'>{t}</p>")
    return "".join(morceaux)


class InterfaceQt(Interface):
    def __init__(self, langue: Optional[str] = None):
        if QtWidgets is None:
            raise RuntimeError("PyQt indisponible")
        super().__init__(langue)
        self.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv[:1])
        self.app.setStyle("Fusion")              # comme psychopy.gui.qtgui.ensureQtApp (fenêtres de l'exercice)
        from .identite import chemin_icone
        ico = chemin_icone()
        if ico:
            self.app.setWindowIcon(QtGui.QIcon(ico))
        self._prog = None

    # ---------------------------------------------- construction commune
    def _dlg(self, action: Optional[str], retour: Optional[str]):
        """Fenêtre vide habillée comme celles de l'exercice. Retourne (fenêtre, grille, bouton action, bouton retour)."""
        w = QtWidgets.QDialog(None)
        w.setWindowTitle(self.t("titre"))
        w.setFixedWidth(LARGEUR_FENETRE)
        grille = QtWidgets.QGridLayout()
        grille.setSpacing(10)
        grille.setColumnMinimumWidth(1, 250)
        grille.setColumnStretch(1, 1)          # liste déroulante aussi large que les champs de la connexion
        w.setLayout(grille)
        w._ligne = 0
        boite = QtWidgets.QDialogButtonBox(parent=w)
        b_action = b_retour = None
        if action:
            b_action = boite.addButton(action, _enum(QtWidgets.QDialogButtonBox, "ButtonRole", "AcceptRole"))
            b_action.clicked.connect(w.accept)
            b_action.setDefault(True)
        if retour:
            # rôle « Reset » : la disposition le met tout à gauche (comme _boutons_retour_puis_suivant)
            b_retour = boite.addButton(retour, _enum(QtWidgets.QDialogButtonBox, "ButtonRole", "ResetRole"))
            b_retour.clicked.connect(w.reject)
        w._boite = boite
        return w, grille, b_action, b_retour

    def _texte(self, w, grille, contenu: str, logo: bool = False):
        if logo:
            chemin = chemin_logo()
            if chemin:
                lx, ly = LOGO_PX
                contenu = (f'<p align="center"><img src="{html.escape(chemin, quote=True)}" width="{lx}" '
                           f'height="{ly}" alt="NeuroVision Solidaire"></p>') + contenu
        lab = QtWidgets.QLabel(contenu, parent=w)
        lab.setWordWrap(True)
        lab.setMaximumWidth(LARGEUR_TEXTE)
        grille.addWidget(lab, w._ligne, 0, 1, 2)
        w._ligne += 1
        return lab

    def _champ(self, w, grille, libelle: str, widget):
        grille.addWidget(QtWidgets.QLabel(libelle, parent=w), w._ligne, 0, 1, 1)
        grille.addWidget(widget, w._ligne, 1, 1, 1)
        w._ligne += 1

    def _ouvrir(self, w) -> bool:
        """Ressort vertical puis boutons en bas (comme _ressort_avant_affichage), affichage modal. True = action."""
        politique = QtWidgets.QSizePolicy
        p = getattr(politique, "Policy", politique)
        grille = w.layout()
        grille.addItem(QtWidgets.QSpacerItem(0, 0, p.Minimum, p.Expanding), w._ligne, 0, 1, -1)
        grille.addWidget(w._boite, w._ligne + 1, 0, 1, 2)
        self.fermer_progression()
        w.raise_()
        w.activateWindow()
        executer = getattr(w, "exec", None) or getattr(w, "exec_")
        accepte = executer() == _enum(QtWidgets.QDialog, "DialogCode", "Accepted")
        w.deleteLater()
        return bool(accepte)

    @staticmethod
    def _h3(texte: str) -> str:
        return f"<h3>{html.escape(texte)}</h3>"

    @staticmethod
    def _p(texte: str, petit: bool = False) -> str:
        corps = html.escape(texte).replace("\n", "<br>")
        return f"<p><small>{corps}</small></p>" if petit else f"<p>{corps}</p>"

    # ---------------------------------------------------------- écrans
    def progression(self, cle: str) -> None:
        self.fermer_progression()
        w = QtWidgets.QDialog(None)
        w.setWindowTitle(self.t("titre"))
        w.setFixedWidth(LARGEUR_FENETRE)
        grille = QtWidgets.QGridLayout()
        grille.setSpacing(10)
        w.setLayout(grille)
        w._ligne = 0
        lignes = self.t(cle).split("\n")
        self._texte(w, grille, self._h3(lignes[0]) + "".join(self._p(l) for l in lignes[1:] if l), logo=True)
        w.show()
        w.raise_()
        self.app.processEvents()
        self._prog = w

    def fermer_progression(self) -> None:
        if self._prog is not None:
            self._prog.close()
            self._prog.deleteLater()
            self._prog = None
            self.app.processEvents()

    def message(self, cle: str, **kw) -> None:
        w, grille, _, _ = self._dlg(self.t("ok"), None)
        parties = self.t(cle, **kw).split("\n\n")
        self._texte(w, grille, "".join(self._p(p) for p in parties))
        self._ouvrir(w)

    def choisir_langue(self, defaut: str) -> Optional[str]:
        codes = [defaut] + [c for c in ("fr", "en") if c != defaut] if defaut in TEXTES else ["fr", "en"]
        w, grille, _, _ = self._dlg("Continuer / Continue", LANGUE_QUITTER)
        self._texte(w, grille, self._h3("Langue / Language")
                    + "<p>Choisissez la langue de NeuroVision.<br>Choose the language of NeuroVision.</p>", logo=True)
        liste = QtWidgets.QComboBox(parent=w)
        liste.addItems([TEXTES[c]["nom_langue"] for c in codes])
        self._champ(w, grille, "Langue / Language", liste)
        if not self._ouvrir(w):
            return None
        return codes[liste.currentIndex()]

    def accueil(self, lignes, contact: str) -> bool:
        w, grille, b_ok, _ = self._dlg(self.t("accueil_accepter"), self.t("quitter"))
        aide = self.t("accueil_contact", contact=contact) if contact else self.t("accueil_sans_contact")
        self._texte(w, grille, self._h3(self.t("accueil_titre")) + self._p(self.t("accueil_identifiant"))
                    + self._p(aide, petit=True) + self._p(self.t("accueil_lire")), logo=True)
        zone = QtWidgets.QTextBrowser(parent=w)
        zone.setOpenExternalLinks(False)
        zone.setHtml(html_avertissements(lignes))
        zone.setMinimumHeight(260)
        zone.setMaximumHeight(260)
        grille.addWidget(zone, w._ligne, 0, 1, 2)
        w._ligne += 1
        case = QtWidgets.QCheckBox(self.t("accueil_case"), parent=w)
        grille.addWidget(case, w._ligne, 0, 1, 2)
        w._ligne += 1
        b_ok.setEnabled(False)
        case.toggled.connect(b_ok.setEnabled)
        return self._ouvrir(w) and case.isChecked()

    def choisir_dossier(self, defaut: str) -> Optional[str]:
        w, grille, _, _ = self._dlg(self.t("dossier_continuer"), self.t("quitter"))
        self._texte(w, grille, self._h3(self.t("dossier_titre")) + self._p(self.t("dossier_texte")))
        chemin = QtWidgets.QLineEdit(defaut, parent=w)
        chemin.setReadOnly(True)
        chemin.setCursorPosition(0)
        grille.addWidget(chemin, w._ligne, 0, 1, 2)
        w._ligne += 1
        autre = QtWidgets.QPushButton(self.t("dossier_autre"), parent=w)
        autre.setAutoDefault(False)
        ligne = QtWidgets.QHBoxLayout()
        ligne.addStretch(1)
        ligne.addWidget(autre)
        grille.addLayout(ligne, w._ligne, 0, 1, 2)
        w._ligne += 1

        def _autre():
            courant = chemin.text()
            d = QtWidgets.QFileDialog.getExistingDirectory(w, self.t("dossier_autre"),
                                                           os.path.dirname(courant) or courant)
            if d:
                chemin.setText(os.path.normpath(d))
                chemin.setCursorPosition(0)

        autre.clicked.connect(_autre)
        if not self._ouvrir(w):
            return None
        return chemin.text()

    def choisir(self, options: Sequence[Tuple[str, str]]) -> Optional[str]:
        if not options:
            return None
        w, grille, _, _ = self._dlg(self.t("dossier_continuer"), self.t("quitter"))
        self._texte(w, grille, self._h3(self.t("choisir")))
        liste = QtWidgets.QComboBox(parent=w)
        liste.addItems([nom for _, nom in options])
        self._champ(w, grille, self.t("exercice"), liste)
        if not self._ouvrir(w):
            return None
        return options[liste.currentIndex()][0]
