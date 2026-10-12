# À propos de NeuroVision Solidaire

*English version below.*

## Une initiative individuelle

NeuroVision Solidaire est l'initiative personnelle et bénévole de Thomas Dietrich. L'association du même nom est en cours de création. Aucune entreprise, aucun laboratoire, aucun établissement de santé ni aucun financeur ne publie ou ne garantit ce logiciel. Thomas Dietrich en est l'éditeur et le seul responsable.

## Un outil d'entraînement, pas un dispositif médical

NeuroVision Solidaire est un outil d'entraînement visuel. Il n'est pas un dispositif médical au sens du règlement (UE) 2017/745 : il n'est destiné ni au diagnostic, ni à la prévention, ni au suivi, ni au traitement d'une maladie.

## Un logiciel ouvert

- Le code du lanceur est public : <https://github.com/thomasadietrich-lithem/TrainingLauncher> (licence GPL-3.0-or-later, voir [`LICENSE`](../LICENSE)).
- Le paquet du Microsoft Store est fabriqué par GitHub Actions à partir de ce code ; les journaux de fabrication sont publics.
- Le logiciel repose sur PsychoPy (<https://www.psychopy.org>), logiciel libre développé par Open Science Tools Ltd et sa communauté, sous licence GPL-3.0. PsychoPy n'est pas associé à ce projet.
- Les exercices sont signés avec une clé conservée hors des serveurs du projet : une compromission des serveurs ne permet pas d'exécuter du code sur votre ordinateur.

## Une origine scientifique citée, pas un partenariat

L'exercice « Tilt Global » reprend le principe d'une tâche d'entraînement visuel décrite par le laboratoire de la Pr Krystel Huxlin (Université de Rochester, États-Unis). Ce laboratoire n'a ni conçu, ni validé, ni approuvé ce logiciel.

## Ce que contient l'application

| Élément | Version | Rôle | Licence |
| --- | --- | --- | --- |
| Lanceur NeuroVision (`NeuroVision.exe`, module `nvs_lanceur`) | 1.0.0, moteur 1 | Vérifie les signatures, télécharge et lance les exercices | GPL-3.0-or-later |
| Python | 3.10.11 | Interpréteur embarqué | PSF-2.0 |
| PsychoPy | 2025.1.1 | Affichage des stimulus, son, clavier, réglage d'écran | GPL-3.0 |
| NumPy, SciPy | épinglées | Calculs | BSD-3-Clause |
| pyglet | épinglée | Fenêtre OpenGL | BSD-3-Clause |
| Pillow | épinglée | Images | MIT-CMU |
| pandas, json-tricks, pyserial | épinglées | Dépendances de PsychoPy | BSD-3-Clause |
| openpyxl, xmlschema | épinglées | Dépendances de PsychoPy | MIT |
| psychtoolbox | < 3.0.20 | Son à faible latence | MIT |
| PyQt6 | épinglée | Fenêtres de connexion et de réglage | GPL-3.0 |
| Deux clés publiques de signature (principale, secours) | — | Vérifier que les exercices viennent du projet | — |
| Logo et icônes | — | Identité visuelle | © 2026 Thomas Dietrich |

Liste complète des paquets épinglés : [`THIRD_PARTY_LICENSES.md`](../THIRD_PARTY_LICENSES.md).

**Téléchargé après l'installation** : le manifeste signé du canal `stable` (signature Ed25519, anti-retour) et l'exercice « Tilt Global » 2.15.0 (empreinte SHA-256 revérifiée à chaque lancement), depuis le serveur du projet.

**Échanges réseau** : téléchargement des exercices (aucune donnée personnelle) ; envoi des résultats de séance sous identifiant non nominatif vers le serveur du projet (Amazon Web Services, région Paris).

**Sur votre ordinateur** : le dossier choisi au premier lancement (par défaut `Documents\NeuroVision Solidaire`) contient vos réglages et vos séances ; il n'est jamais effacé par l'application ni par sa désinstallation.

**Ce qu'il n'y a pas** : aucune publicité, aucun traceur ni outil de mesure d'audience, aucun achat intégré, aucune intelligence artificielle générative, aucun accès à la caméra, au micro ou à la localisation, aucun pilote ni service Windows.

## Ce que nous nous engageons à publier

La liste des composants et de leurs licences, l'historique des versions, et toute modification de la manière dont les données sont traitées.

Voir aussi : [Avertissements](AVERTISSEMENTS.md) · [Politique de confidentialité](CONFIDENTIALITE.md)

---

# About NeuroVision Solidaire

## An individual initiative

NeuroVision Solidaire is the personal, volunteer initiative of Thomas Dietrich. The association of the same name is being set up. No company, laboratory, healthcare institution or funder publishes or guarantees this software. Thomas Dietrich is its publisher and solely responsible for it.

## A training tool, not a medical device

NeuroVision Solidaire is a visual training tool. It is not a medical device within the meaning of Regulation (EU) 2017/745: it is not intended for the diagnosis, prevention, monitoring or treatment of any disease.

## Open software

- The launcher source code is public: <https://github.com/thomasadietrich-lithem/TrainingLauncher> (GPL-3.0-or-later, see [`LICENSE`](../LICENSE)).
- The Microsoft Store package is built by GitHub Actions from that code; build logs are public.
- The software relies on PsychoPy (<https://www.psychopy.org>), free software developed by Open Science Tools Ltd and its community under GPL-3.0. PsychoPy is not associated with this project.
- Exercises are signed with a key kept outside the project's servers: compromising the servers does not allow code to run on your computer.

## A cited scientific origin, not a partnership

The "Tilt Global" exercise follows the principle of a visual training task described by Prof. Krystel Huxlin's laboratory (University of Rochester, USA). That laboratory did not design, validate or endorse this software.

## What's inside

The component table above applies as is. Full list of pinned packages: [`THIRD_PARTY_LICENSES.md`](../THIRD_PARTY_LICENSES.md).

**Downloaded after installation**: the signed manifest of the `stable` channel (Ed25519 signature, anti-rollback) and the "Tilt Global" 2.15.0 exercise (SHA-256 fingerprint re-checked at every launch), from the project's server.

**Network traffic**: download of exercises (no personal data); upload of session results under a non-identifying ID to the project's server (Amazon Web Services, Paris region).

**On your computer**: the folder chosen at first launch (default `Documents\NeuroVision Solidaire`) holds your settings and sessions; it is never deleted by the app or by uninstalling it.

**What it does not contain**: no ads, no trackers or analytics, no in-app purchases, no generative AI, no access to camera, microphone or location, no Windows driver or service.

## What we commit to publish

The list of components and their licences, the version history, and any change in how data is processed.

See also: [Warnings](AVERTISSEMENTS.md) · [Privacy policy](CONFIDENTIALITE.md)
