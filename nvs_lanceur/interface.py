"""Textes FR/EN et fenêtres de secours du lanceur (Tk) ; les fenêtres normales sont en Qt (interface_qt.py)..
Les tests utilisent une interface factice ; ici, aucune logique métier."""

from __future__ import annotations

import locale
import os
from typing import List, Optional, Sequence, Tuple

TEXTES = {
    "fr": {
        "titre": "NeuroVision Solidaire Training Platform",
        "verif": "Recherche de mises à jour…",
        "accueil_titre": "Bienvenue",
        "accueil_identifiant": "Cette application nécessite un identifiant fourni par le projet NeuroVision Solidaire.",
        "accueil_contact": "Vous n'avez pas d'identifiant ? Écrivez à {contact}.",
        "accueil_sans_contact": "Vous n'avez pas d'identifiant ? Adressez-vous à la personne qui vous a proposé "
                                "cet entraînement.",
        "accueil_lire": "Avant de commencer, lisez attentivement ce texte :",
        "accueil_case": "J'ai lu l'avertissement santé et la limitation de responsabilité, et je les accepte.",
        "accueil_accepter": "Accepter et continuer",
        "maj_exercice": "Mise à jour de l'exercice en cours…\nMerci de patienter.",
        "maj_lanceur": "Installation d'une nouvelle version de NeuroVision…\nLe programme va redémarrer tout seul.",
        "choisir": "Quel exercice voulez-vous faire ?",
        "premiere_install": "La première installation demande une connexion Internet.\n\n"
                            "Vérifiez votre connexion, puis relancez NeuroVision.",
        "aucun": "Aucun exercice n'est disponible pour le moment.\n\nContactez l'association.",
        "echec_retour": "La nouvelle version de l'exercice n'a pas pu démarrer.\n"
                        "L'ancienne version va être relancée.",
        "echec_total": "L'exercice n'a pas pu démarrer.\n\nContactez l'association en indiquant le code {code}.",
        "quitter": "Quitter",
        "ok": "OK",
        "dossier_titre": "Où ranger vos séances ?",
        "dossier_texte": "NeuroVision va ranger vos séances et vos réglages dans ce dossier.\n"
                         "Ils y restent même si NeuroVision est désinstallé.\n"
                         "Ne supprimez pas ce dossier.",
        "dossier_continuer": "Continuer",
        "dossier_autre": "Choisir un autre dossier…",
        "dossier_impossible": "Impossible d'écrire dans ce dossier. Choisissez-en un autre.",
        "nom_langue": "Français",
        "exercice": "Exercice",
    },
    "en": {
        "titre": "NeuroVision Solidaire Training Platform",
        "verif": "Checking for updates…",
        "accueil_titre": "Welcome",
        "accueil_identifiant": "This application requires an ID provided by the NeuroVision Solidaire project.",
        "accueil_contact": "You don't have an ID? Write to {contact}.",
        "accueil_sans_contact": "You don't have an ID? Please ask the person who suggested this training to you.",
        "accueil_lire": "Before you start, please read this text carefully:",
        "accueil_case": "I have read the health warning and the disclaimer of liability, and I accept them.",
        "accueil_accepter": "Accept and continue",
        "maj_exercice": "Updating the exercise…\nPlease wait.",
        "maj_lanceur": "Installing a new version of NeuroVision…\nThe program will restart by itself.",
        "choisir": "Which exercise would you like to do?",
        "premiere_install": "The first installation requires an Internet connection.\n\n"
                            "Please check your connection, then start NeuroVision again.",
        "aucun": "No exercise is available at the moment.\n\nPlease contact the association.",
        "echec_retour": "The new version of the exercise could not start.\nThe previous version will be started.",
        "echec_total": "The exercise could not start.\n\nPlease contact the association and give code {code}.",
        "quitter": "Quit",
        "ok": "OK",
        "dossier_titre": "Where should your sessions be kept?",
        "dossier_texte": "NeuroVision will keep your sessions and settings in this folder.\n"
                         "They stay there even if NeuroVision is uninstalled.\n"
                         "Do not delete this folder.",
        "dossier_continuer": "Continue",
        "dossier_autre": "Choose another folder…",
        "dossier_impossible": "This folder cannot be written to. Please choose another one.",
        "nom_langue": "English",
        "exercice": "Exercise",
    },
}

# Écran de choix de la langue (premier lancement) : bilingue, avant que la langue soit connue.
LANGUE_TITRE = "Langue / Language"
LANGUE_TEXTE = "Choisissez la langue de NeuroVision.\nChoose the language of NeuroVision."
LANGUE_QUITTER = "Quitter / Quit"

# Aspect commun des fenêtres (celui de « Où ranger vos séances ? »).
BLEU = "#1D55AD"
BLEU_FONCE = "#16458f"
BLEU_INACTIF = "#a9bde0"
BANDE = "#eef3fb"
GRIS_TEXTE = "#4a5568"
LARGEUR = 640                                 # largeur du contenu, en pixels


def langue_systeme() -> str:
    env = os.environ.get("NVS_LANGUE")
    if env in TEXTES:
        return env
    try:
        loc = (locale.getlocale()[0] or "").lower()
    except Exception:
        loc = ""
    return "fr" if loc.startswith(("fr", "french")) else ("en" if loc else "fr")


class Interface:
    """Interface de base : console (utile hors Windows et en diagnostic)."""

    def __init__(self, langue: Optional[str] = None):
        self.langue = langue or langue_systeme()

    def t(self, cle: str, **kw) -> str:
        texte = TEXTES[self.langue][cle].format(**kw)
        if cle == "titre":                     # 1.2.3 (07/11, demande de Thomas) : version visible dans chaque fenêtre
            from . import VERSION
            texte += " — version " + VERSION
        return texte

    def definir_langue(self, langue: str) -> None:
        if langue in TEXTES:
            self.langue = langue

    def choisir_langue(self, defaut: str) -> Optional[str]:
        """Premier lancement : langue de l'application ("fr" / "en"). None = quitter."""
        return defaut if defaut in TEXTES else "fr"

    def progression(self, cle: str) -> None:
        print(self.t(cle))

    def fermer_progression(self) -> None:
        pass

    def message(self, cle: str, **kw) -> None:
        print(self.t(cle, **kw))

    def choisir(self, options: Sequence[Tuple[str, str]]) -> Optional[str]:
        """options = [(id, nom affiché)] ; retourne l'id choisi ou None (quitter)."""
        return options[0][0] if options else None

    def accueil(self, lignes, contact: str) -> bool:
        """Premier lancement : identifiant requis + avertissement santé. True = accepté, False = quitter."""
        print(self.t("accueil_identifiant"))
        for _, texte in lignes:
            print(texte)
        return True

    def choisir_dossier(self, defaut: str) -> Optional[str]:
        """Premier lancement : confirme (ou change) le dossier des données. None = quitter."""
        print(self.t("dossier_texte"), defaut)
        return defaut


class InterfaceTk(Interface):  # pragma: no cover - testée sur Windows (P3/P5)
    def __init__(self, langue: Optional[str] = None):
        super().__init__(langue)
        import tkinter as tk
        if os.name == "nt":               # sinon Windows agrandit la fenêtre en image floue sur les écrans à 125-150 %
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass
        self.tk = tk
        self.racine = tk.Tk()
        self.racine.withdraw()
        self.racine.title(self.t("titre"))
        from .identite import appliquer_tk
        appliquer_tk(self.racine)         # icône NeuroVision (œil) au lieu de la plume Tk, pour toutes les fenêtres
        self._prog = None

    def _fenetre(self):
        w = self.tk.Toplevel(self.racine)
        w.title(self.t("titre"))
        w.configure(bg="white", padx=40, pady=30)
        w.resizable(False, False)
        w.attributes("-topmost", True)
        return w

    def _centrer(self, w):
        w.update_idletasks()
        x = (w.winfo_screenwidth() - w.winfo_width()) // 2
        y = (w.winfo_screenheight() - w.winfo_height()) // 3
        w.geometry(f"+{x}+{y}")

    def progression(self, cle: str) -> None:
        self.fermer_progression()
        w = self._fenetre()
        self.tk.Label(w, text=self.t(cle), font=("Segoe UI", 18), bg="white", fg="#1D55AD",
                      justify="center").pack()
        self._centrer(w)
        w.update()
        self._prog = w

    def fermer_progression(self) -> None:
        if self._prog is not None:
            self._prog.destroy()
            self._prog = None
            self.racine.update()

    def message(self, cle: str, **kw) -> None:
        self.fermer_progression()
        w = self._fenetre()
        self.tk.Label(w, text=self.t(cle, **kw), font=("Segoe UI", 16), bg="white", justify="center",
                      wraplength=640).pack(pady=(0, 24))
        self.tk.Button(w, text=self.t("ok"), font=("Segoe UI", 16, "bold"), width=12,
                       command=w.destroy).pack()
        self._centrer(w)
        w.grab_set()
        self.racine.wait_window(w)

    def choisir(self, options: Sequence[Tuple[str, str]]) -> Optional[str]:
        self.fermer_progression()
        choix: List[Optional[str]] = [None]
        w = self._fenetre()
        self.tk.Label(w, text=self.t("choisir"), font=("Segoe UI", 18, "bold"), bg="white").pack(pady=(0, 20))
        for oid, nom in options:
            def _pris(o=oid):
                choix[0] = o
                w.destroy()
            self.tk.Button(w, text=nom, font=("Segoe UI", 18), width=28, pady=10, bg="#1D55AD", fg="white",
                           command=_pris).pack(pady=8)
        self.tk.Button(w, text=self.t("quitter"), font=("Segoe UI", 14), command=w.destroy).pack(pady=(20, 0))
        self._centrer(w)
        w.grab_set()
        self.racine.wait_window(w)
        return choix[0]

    # ------------------------------------------------ éléments communs
    def _titre(self, w, texte):
        self.tk.Label(w, text=texte, font=("Segoe UI", 18, "bold"), bg="white", fg=BLEU,
                      justify="center").pack(pady=(0, 12))

    def _texte(self, w, texte, taille=14, couleur="black", pady=(0, 12)):
        self.tk.Label(w, text=texte, font=("Segoe UI", taille), bg="white", fg=couleur, justify="center",
                      wraplength=LARGEUR).pack(pady=pady)

    def _bouton_principal(self, w, texte, commande, largeur=18):
        b = self.tk.Button(w, text=texte, font=("Segoe UI", 16, "bold"), width=largeur, pady=6, bg=BLEU, fg="white",
                           activebackground=BLEU_FONCE, activeforeground="white", disabledforeground="white",
                           cursor="hand2", command=commande)
        b.pack(pady=4)
        return b

    def _bouton_quitter(self, w, texte=None):
        self.tk.Button(w, text=texte or self.t("quitter"), font=("Segoe UI", 12),
                       command=w.destroy).pack(pady=(14, 0))

    def definir_langue(self, langue: str) -> None:
        super().definir_langue(langue)
        self.racine.title(self.t("titre"))

    # ------------------------------------------------ écrans
    def choisir_langue(self, defaut: str) -> Optional[str]:
        self.fermer_progression()
        choix: List[Optional[str]] = [None]
        w = self._fenetre()
        self._titre(w, LANGUE_TITRE)
        self._texte(w, LANGUE_TEXTE, pady=(0, 20))
        ordre = [defaut] + [l for l in ("fr", "en") if l != defaut] if defaut in TEXTES else ["fr", "en"]
        premier = None
        for code in ordre:
            def _pris(c=code):
                choix[0] = c
                w.destroy()
            b = self._bouton_principal(w, TEXTES[code]["nom_langue"], _pris)
            premier = premier or b
        self._bouton_quitter(w, LANGUE_QUITTER)
        w.bind("<Return>", lambda _e: premier.invoke())
        self._centrer(w)
        w.grab_set()
        premier.focus_set()
        self.racine.wait_window(w)
        return choix[0]

    def accueil(self, lignes, contact: str) -> bool:
        self.fermer_progression()
        accepte = [False]
        w = self._fenetre()
        self._titre(w, self.t("accueil_titre"))
        self._texte(w, self.t("accueil_identifiant"), pady=(0, 4))
        aide = self.t("accueil_contact", contact=contact) if contact else self.t("accueil_sans_contact")
        self._texte(w, aide, taille=12, couleur=GRIS_TEXTE, pady=(0, 16))
        self._texte(w, self.t("accueil_lire"), taille=13, pady=(0, 8))
        # Le texte des avertissements, dans la même bande claire que le chemin du dossier (sans cadre ni relief).
        bande = self.tk.Frame(w, bg=BANDE, width=LARGEUR, height=280)
        bande.pack_propagate(False)
        bande.pack(pady=(0, 16))
        barre = self.tk.Scrollbar(bande)
        barre.pack(side="right", fill="y")
        zone = self.tk.Text(bande, wrap="word", font=("Segoe UI", 11), bg=BANDE, fg="black", relief="flat", bd=0,
                            highlightthickness=0, padx=16, pady=12, spacing2=2, yscrollcommand=barre.set,
                            cursor="arrow")
        zone.tag_configure("section", font=("Segoe UI", 12, "bold"), foreground=BLEU, spacing1=10, spacing3=4)
        zone.tag_configure("texte", spacing3=6)
        debut = True
        for style, texte in lignes:
            if style == "titre":                 # « Avertissements — NeuroVision Solidaire » : déjà dit par la fenêtre
                continue
            if debut and style == "section":
                zone.tag_configure("section1", font=("Segoe UI", 12, "bold"), foreground=BLEU, spacing3=4)
                style = "section1"
            debut = False
            zone.insert("end", texte + "\n", style)
        zone.configure(state="disabled")
        zone.pack(side="left", fill="both", expand=True)
        barre.configure(command=zone.yview)
        coche = self.tk.BooleanVar(value=False)

        def _coche():
            bouton.configure(state="normal" if coche.get() else "disabled",
                             bg=BLEU if coche.get() else BLEU_INACTIF,
                             cursor="hand2" if coche.get() else "arrow")

        def _accepter():
            accepte[0] = True
            w.destroy()

        self.tk.Checkbutton(w, text=self.t("accueil_case"), variable=coche, command=_coche, font=("Segoe UI", 13),
                            bg="white", activebackground="white", highlightthickness=0, bd=0,
                            wraplength=LARGEUR - 40, justify="left", cursor="hand2").pack(pady=(0, 16))
        bouton = self._bouton_principal(w, self.t("accueil_accepter"), _accepter, largeur=22)
        _coche()
        self._bouton_quitter(w)
        self._centrer(w)
        w.grab_set()
        self.racine.wait_window(w)
        return accepte[0]

    def choisir_dossier(self, defaut: str) -> Optional[str]:
        from tkinter import filedialog
        self.fermer_progression()
        resultat: List[Optional[str]] = [None]
        courant = [defaut]
        w = self._fenetre()
        self._titre(w, self.t("dossier_titre"))
        self._texte(w, self.t("dossier_texte"))
        chemin = self.tk.Label(w, text=defaut, font=("Segoe UI", 13, "bold"), bg=BANDE, padx=12, pady=8,
                               wraplength=LARGEUR)
        chemin.pack(pady=(0, 18), fill="x")

        def _continuer():
            resultat[0] = courant[0]
            w.destroy()

        def _autre():
            d = filedialog.askdirectory(parent=w, initialdir=os.path.dirname(courant[0]) or courant[0],
                                        mustexist=False)
            if d:
                courant[0] = os.path.normpath(d)
                chemin.configure(text=courant[0])

        self._bouton_principal(w, self.t("dossier_continuer"), _continuer)
        self.tk.Button(w, text=self.t("dossier_autre"), font=("Segoe UI", 13), command=_autre).pack(pady=4)
        self._bouton_quitter(w)
        self._centrer(w)
        w.grab_set()
        self.racine.wait_window(w)
        return resultat[0]


def interface_par_defaut() -> Interface:
    """Qt d'abord (mêmes fenêtres que l'exercice), puis Tk, puis console. Le choix est écrit dans le journal :
    une fenêtre de secours (Tk) doit rester l'exception et se voir."""
    import logging
    log = logging.getLogger("nvs_lanceur")
    try:
        from .interface_qt import InterfaceQt
        ui = InterfaceQt()
        log.info("fenêtres : Qt")
        return ui
    except Exception as exc:
        log.warning("fenêtres Qt indisponibles (%s : %s) : fenêtres de secours", exc.__class__.__name__, exc)
    try:
        ui = InterfaceTk()
        log.info("fenêtres : Tk (secours)")
        return ui
    except Exception:
        log.warning("fenêtres Tk indisponibles : console")
        return Interface()
