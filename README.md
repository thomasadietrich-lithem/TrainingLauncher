# TrainingLauncher — Lanceur NeuroVision Solidaire

Socle installé chez l'utilisateur : il télécharge, **vérifie (signature Ed25519)** et exécute les exercices publiés
par le projet, puis se tient à jour seul. Il ne contient aucun exercice. Spécification complète : chapitre 16 du
document directeur du projet (« Module d'installation »).

**Initiative individuelle de Thomas Dietrich.** NeuroVision Solidaire est un outil d'entraînement visuel ; ce n'est pas
un dispositif médical. Distribution limitée aux personnes invitées.

- [À propos / About](docs/A_PROPOS.md) — transparence, contenu de l'application
- [Avertissements / Warnings](docs/AVERTISSEMENTS.md) — santé, limitation de responsabilité
- [Confidentialité / Privacy](docs/CONFIDENTIALITE.md)
- Licence : GPL-3.0-or-later ([`LICENSE`](LICENSE)) · composants tiers : [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md)

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

## Publier sans Python : `outils/Publier_NVS.html`
Page à ouvrir dans Edge ou Chrome (générée par `outils/generer_page_publication.py` depuis `outils/modele_publier.html`,
avec les clés publiques et le contrat moteur inscrits dedans). Elle vérifie la publication précédente, contrôle les
imports, refuse une version non croissante, signe avec `principale.cle_privee` et écrit `canal/` + `exercices/` dans
le dossier choisi (`A_DEPLOYER\logiciel`). Même format que `publier.py` (interopérables, testé de bout en bout).

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
P2 (logique du lanceur) : faite, 27 tests. P3 (fabrication Windows) : faite — workflow « Fabriquer l'installeur
Windows » (tests sous Windows, PyInstaller dossier, auto-test du gelé, Inno Setup, installation/désinstallation
silencieuses) ; installeur ~103 Mo (zip). À venir : P4 canal de publication signé, P5 pilote. Prérequis côté exercice : `docs/adaptation_exercice.md`.

## Premier lancement (exigences Microsoft Store)
`nvs_lanceur/accueil.py` : écran « identifiant requis » (avec l'adresse `CONTACT_EMAIL` de `config.py` si renseignée)
et avertissement santé + limitation de responsabilité à accepter (case à cocher). Texte unique = `docs/AVERTISSEMENTS.md`,
embarqué dans le lanceur ; acceptation mémorisée avec l'empreinte du texte (`accord_avertissements.json`) → redemandée
si le texte change. Refus → sortie (code 41), rien d'autre n'est fait.

## Icône des fenêtres
`nvs_lanceur/identite.py` : l'œil NeuroVision remplace l'icône générique en haut à gauche des fenêtres du lanceur (Tk)
et de celles de l'exercice (boîtes de dialogue PsychoPy/Qt, posée par le lanceur dans le processus enfant au moment où
PsychoPy crée son application Qt — aucun exercice n'a à s'en occuper). Vérifié par l'auto-test de fabrication.

## Création des clés
Ouvrir `outils/Creer_cles_NVS.html` dans Edge ou Chrome (aucune installation, Python non requis) : crée principale +
secours, les écrit dans le dossier choisi et affiche les clés publiques. Variante si Python est installé :
`outils/Creer_cles_NVS.bat`.
