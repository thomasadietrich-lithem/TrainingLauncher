# TrainingLauncher — Lanceur NeuroVision Solidaire

Socle installé chez le patient : il télécharge, **vérifie (signature Ed25519)** et exécute les exercices publiés
par l'association, puis se tient à jour seul. Il ne contient aucun exercice. Spécification complète : chapitre 16 du
document directeur du projet (« Module d'installation patient »).

## Principes
- **Plusieurs exercices** : le manifeste en liste autant que nécessaire (aujourd'hui un seul, `tilt_global`).
  Un seul exercice publié → lancé directement ; plusieurs → écran de choix. Un exercice désactivé est masqué,
  ses données restent sur le poste.
- **Sauvegarde locale garantie** : chaque exercice reçoit son dossier `donnees/<id>/` (variable `NVS_DATA_DIR`,
  répertoire courant) pour `config/` et `session_data/`. Le lanceur ne lit, ne déplace ni n'efface jamais ce dossier :
  les séances et réglages survivent aux coupures Internet, aux mises à jour et aux retours arrière.
- **Mises à jour sûres** : téléchargement dans un dossier temporaire, empreinte sha256 vérifiée, bascule en une fois,
  version précédente conservée, retour arrière automatique si la nouvelle version ne démarre pas.
- **Hors ligne** : la dernière version installée et vérifiée est lancée.
- **Contrat moteur** : un exercice n'importe que la bibliothèque standard + les modules de `nvs_lanceur/moteur.json`.
  Nouvelle dépendance tierce ⇒ `MOTEUR`+1 ⇒ nouvel installeur.

## Arborescence sur le poste (`%LOCALAPPDATA%\NeuroVisionSolidaire\`)
```
app\                         lanceur (remplacé par les installeurs)
exercices\<id>\<version>\    exercices vérifiés (version courante + précédente)
donnees\<id>\                config\ + session_data\ de chaque exercice — jamais touché par le lanceur
etat.json  journal_lanceur.log  temp\
```

## Publier (canal `logiciel/` du CloudFront du portail)
```
python outils/verifier_imports.py Fba_Training_Tilt_Global.py
python outils/publier.py --sortie A_DEPLOYER/logiciel --manifeste-precedent A_DEPLOYER/logiciel/canal/stable.json \
    --exercice tilt_global --fichier Fba_Training_Tilt_Global.py --nom-fr "Entraînement visuel" \
    --nom-en "Visual training" --cle <clé privée> --cle-id principale
```
Dépôt S3 : `exercices/` et `installeur/` d'abord, `canal/` **en dernier**. Revenir à un ancien contenu = le republier
sous un numéro de version plus grand (les numéros ne reculent jamais).

## Clés
`python outils/generer_cles.py principale --sortie <dossier HORS dépôt>` puis idem `secours`. Seules les clés
**publiques** entrent dans `nvs_lanceur/cles_publiques.json`. Clé privée : jamais sur AWS ni dans ce dépôt.

## Tests
`python -m unittest discover -s tests -v` (serveur HTTP local, vraies signatures, vrais processus enfants).

## État
Phase P2 (logique du lanceur) : faite, 27 tests. À venir : P3 fabrication Windows (PyInstaller onedir + Inno Setup
via GitHub Actions), P4 canal, P5 pilote. Prérequis côté exercice : `docs/adaptation_exercice.md`.

## Clés : `outils/Creer_cles_NVS.bat` (double-clic, Windows) crée principale + secours et affiche les clés publiques.
