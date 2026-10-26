"""Fenêtres minimales du lanceur (Tk, présent dans Python Windows). Grand texte, gros boutons, FR/EN.
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
        "accueil_lire": "Avant de commencer, lisez l'avertissement santé ci-dessous.",
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
    },
    "en": {
        "titre": "NeuroVision Solidaire Training Platform",
        "verif": "Checking for updates…",
        "accueil_titre": "Welcome",
        "accueil_identifiant": "This application requires an ID provided by the NeuroVision Solidaire project.",
        "accueil_contact": "You don't have an ID? Write to {contact}.",
        "accueil_sans_contact": "You don't have an ID? Please ask the person who suggested this training to you.",
        "accueil_lire": "Before you start, please read the health warning below.",
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
    },
}


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
        return TEXTES[self.langue][cle].format(**kw)

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

    def accueil(self, lignes, contact: str) -> bool:
        self.fermer_progression()
        accepte = [False]
        w = self._fenetre()
        self.tk.Label(w, text=self.t("accueil_titre"), font=("Segoe UI", 20, "bold"), bg="white",
                      fg="#1D55AD").pack(pady=(0, 10))
        self.tk.Label(w, text=self.t("accueil_identifiant"), font=("Segoe UI", 14, "bold"), bg="white",
                      justify="center", wraplength=680).pack()
        aide = self.t("accueil_contact", contact=contact) if contact else self.t("accueil_sans_contact")
        self.tk.Label(w, text=aide, font=("Segoe UI", 12), bg="white", justify="center",
                      wraplength=680).pack(pady=(4, 14))
        self.tk.Label(w, text=self.t("accueil_lire"), font=("Segoe UI", 12), bg="white").pack(anchor="w")
        cadre = self.tk.Frame(w, bg="white", highlightthickness=1, highlightbackground="#c8d3e6")
        cadre.pack(fill="both", pady=(4, 10))
        barre = self.tk.Scrollbar(cadre)
        barre.pack(side="right", fill="y")
        zone = self.tk.Text(cadre, width=78, height=15, wrap="word", font=("Segoe UI", 11), bg="#f7f9fc",
                            relief="flat", padx=12, pady=10, yscrollcommand=barre.set, cursor="arrow")
        zone.tag_configure("titre", font=("Segoe UI", 14, "bold"), foreground="#1D55AD", spacing3=6)
        zone.tag_configure("section", font=("Segoe UI", 12, "bold"), spacing1=8, spacing3=4)
        zone.tag_configure("texte", spacing3=4)
        for style, texte in lignes:
            zone.insert("end", texte + "\n", style)
        zone.configure(state="disabled")
        zone.pack(side="left", fill="both")
        barre.configure(command=zone.yview)
        coche = self.tk.BooleanVar(value=False)
        bouton = self.tk.Button(w, text=self.t("accueil_accepter"), font=("Segoe UI", 15, "bold"), width=22,
                                pady=6, bg="#1D55AD", fg="white", state="disabled")

        def _coche():
            bouton.configure(state="normal" if coche.get() else "disabled")

        def _accepter():
            accepte[0] = True
            w.destroy()

        self.tk.Checkbutton(w, text=self.t("accueil_case"), variable=coche, command=_coche, font=("Segoe UI", 12),
                            bg="white", wraplength=660, justify="left").pack(anchor="w", pady=(0, 12))
        bouton.configure(command=_accepter)
        bouton.pack(pady=4)
        self.tk.Button(w, text=self.t("quitter"), font=("Segoe UI", 12), command=w.destroy).pack(pady=(10, 0))
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
        self.tk.Label(w, text=self.t("dossier_titre"), font=("Segoe UI", 18, "bold"), bg="white",
                      fg="#1D55AD").pack(pady=(0, 12))
        self.tk.Label(w, text=self.t("dossier_texte"), font=("Segoe UI", 14), bg="white", justify="center",
                      wraplength=640).pack(pady=(0, 12))
        chemin = self.tk.Label(w, text=defaut, font=("Segoe UI", 13, "bold"), bg="#eef3fb", padx=12, pady=8,
                               wraplength=640)
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

        self.tk.Button(w, text=self.t("dossier_continuer"), font=("Segoe UI", 16, "bold"), width=18, pady=6,
                       bg="#1D55AD", fg="white", command=_continuer).pack(pady=4)
        self.tk.Button(w, text=self.t("dossier_autre"), font=("Segoe UI", 13), command=_autre).pack(pady=4)
        self.tk.Button(w, text=self.t("quitter"), font=("Segoe UI", 12), command=w.destroy).pack(pady=(14, 0))
        self._centrer(w)
        w.grab_set()
        self.racine.wait_window(w)
        return resultat[0]


def interface_par_defaut() -> Interface:
    try:
        return InterfaceTk()
    except Exception:
        return Interface()
