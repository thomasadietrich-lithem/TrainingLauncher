"""Lanceur NeuroVision Solidaire.

Socle stable installé chez le patient : il télécharge, vérifie (signature Ed25519) et exécute
les exercices publiés par l'association. Il ne contient AUCUN exercice.
Spécification : document directeur du projet, chapitre 16.
"""

VERSION = "1.0.0"   # version du lanceur (comparée à lanceur.version_min du manifeste)
MOTEUR = 1          # ensemble figé des bibliothèques embarquées (voir moteur/moteur.json)
SCHEMA_MANIFESTE = 1
