# Adaptation de `Fba_Training_Tilt_Global.py` au lanceur (chap. 16.4 — préalable à toute distribution)

**À appliquer par UNE seule session** (celle qui fait évoluer l'exercice, ou celle du lanceur avec l'accord de
Thomas). Rétro-compatible : lancé à la main (`python …py`), l'exercice se comporte exactement comme avant.
Repères de lignes : version lot 3 (403 912 o, 06/10).

## (a) CRITIQUE — dossier de données fourni par le lanceur (l. 268)
```python
# avant
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# après
BASE_DIR = os.environ.get("NVS_DATA_DIR") or os.path.dirname(os.path.abspath(__file__))
```
Sans cela, `config/` (profils d'écran, réglages, consentements, `envois_en_attente.json`, calibrations réalisées,
logo) et `session_data/` seraient écrits à côté du script, dans `exercices/<id>/<version>/`, que le lanceur
remplace à chaque mise à jour → **perte des données locales**. Avec la ligne, tout va dans `donnees/tilt_global/`,
que le lanceur ne touche jamais : la sauvegarde locale en cas de coupure Internet est préservée à l'identique
(l'exercice continue d'écrire ses séances et sa file d'envois en attente sur le disque, puis la vide quand le cloud
répond, comme aujourd'hui). Vérifier qu'aucun autre chemin n'est calculé depuis `__file__` (recherche `__file__`).

## (b) Traçabilité — version du lanceur dans chaque résumé (l. ~6840)
```python
"version_logiciel": SOFTWARE_VERSION,
"version_lanceur": os.environ.get("NVS_LANCEUR_VERSION") or None,
```
(+ ajouter `version_lanceur` aux champs conservés par la Lambda dans les résumés allégés si l'Explorateur doit
l'afficher.)

## (c) Message « mise à jour nécessaire » sous le lanceur (l. ~1808 / ~2076, appel l. ~6315)
Sous le lanceur (`NVS_LANCEUR_VERSION` présent), le texte doit dire : « Fermez NeuroVision puis relancez-le : la
mise à jour se fera automatiquement. » / « Close NeuroVision and start it again: the update will install
automatically. » — le texte actuel est conservé hors lanceur.

## Tests à ajouter dans `tests/`
- `NVS_DATA_DIR` défini → `MONITOR_CACHE_FILE`, `SETTINGS_FILE`, `PENDING_UPLOAD_FILE`, `CONSENT_FILE`, journaux et
  sorties de séance sous ce dossier ; non défini → comportement historique.
- `outils/verifier_imports.py Fba_Training_Tilt_Global.py` → `IMPORTS OK` (contrat moteur), à chaque version.
