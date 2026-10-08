# -*- mode: python ; coding: utf-8 -*-
# PyInstaller — NeuroVision.exe en mode DOSSIER (onedir), sans console. Document directeur, chapitre 16.2 / 16.7 P3.
# Le lanceur ne contient AUCUN exercice : on embarque le « moteur » (modules_a_verifier + modules_autorises de
# nvs_lanceur/moteur.json) pour que les exercices téléchargés puissent les importer.
import json, os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

RACINE = os.path.abspath(os.path.join(SPECPATH, ".."))
with open(os.path.join(RACINE, "nvs_lanceur", "moteur.json"), encoding="utf-8") as f:
    MOTEUR = json.load(f)

caches = set(MOTEUR["modules_a_verifier"])
for m in MOTEUR["modules_autorises"]:
    caches.add(m)
    if m.startswith("psychopy.") or m in ("pyglet",):
        caches.update(collect_submodules(m))         # chargements dynamiques (stimuli, plateformes pyglet)
caches.update(collect_submodules("psychtoolbox"))
caches.update(["tkinter", "tkinter.ttk"])

donnees = [
    (os.path.join(RACINE, "nvs_lanceur", "moteur.json"), "nvs_lanceur"),
    (os.path.join(RACINE, "nvs_lanceur", "cles_publiques.json"), "nvs_lanceur"),
    (os.path.join(RACINE, "installeur", "neurovision.ico"), "nvs_lanceur"),   # icône des fenêtres (identite.py)
]
donnees += collect_data_files("psychopy", excludes=["**/demos/**", "**/app/**", "**/tests/**", "**/experiment/**"])
binaires = collect_dynamic_libs("psychtoolbox") + collect_dynamic_libs("pyglet")

a = Analysis(
    [os.path.join(RACINE, "NeuroVision.py")],
    pathex=[RACINE],
    binaries=binaires,
    datas=donnees,
    hiddenimports=sorted(caches),
    excludes=["psychopy.app", "psychopy.experiment", "psychopy.demos", "psychopy.tests", "wx", "IPython",
              "jedi", "notebook", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="NeuroVision",
          icon=os.path.join(RACINE, "installeur", "neurovision.ico"),
          console=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, name="NeuroVision", upx=False)
