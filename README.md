# Planning activités hors vacances scolaires

Génère un agenda `.ics` par activité extrascolaire, en retirant automatiquement
les séances qui tombent pendant les vacances scolaires (zones A, B, C) et, au
choix, les jours fériés. Les fichiers s'importent tels quels dans Google
Agenda, Outlook ou Apple Calendrier.

## Structure du projet

```
planning-activites/
├── data/calendars/2026-2027.json   ← dates de vacances, à dupliquer chaque année
├── planning_scolaire/               ← cœur métier, sans dépendance externe
│   ├── calendrier.py                   charge le JSON, calcule les jours exclus
│   ├── activites.py                    modèle Activite + calcul des séances
│   ├── ics.py                          génère les fichiers .ics et le .zip
│   └── cli.py                          interface en ligne de commande
├── webapp/                          ← façade web Flask (réutilise le cœur ci-dessus)
│   ├── app.py
│   ├── templates/index.html
│   └── static/{style.css,app.js}
├── exemples/activites.json          ← exemple pour la CLI
└── tests/test_scheduler.py
```

Le cœur métier (`planning_scolaire/`) ne connaît ni Flask ni le web : c'est ce
qui le rend facile à réutiliser (CLI, app web, script planifié, futur bot...).

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Utilisation en ligne de commande

```bash
python -m planning_scolaire.cli --zone B --activites exemples/activites.json --sortie mes_agendas/
```

Options :
- `--zone` : `A`, `B` ou `C`
- `--annee` : ex. `2026-2027` (par défaut, la plus récente disponible)
- `--activites` : fichier JSON (voir `exemples/activites.json`)
- `--sortie` : dossier où écrire les `.ics`
- `--annees-disponibles` : liste les calendriers connus

## Lancer l'application web

```bash
python webapp/app.py
```

Puis ouvrir `http://localhost:5000`.

## Ajouter une nouvelle année scolaire (l'automatisation demandée)

Aucune ligne de code à modifier. Dès la publication du calendrier officiel
d'une nouvelle année :

1. Copier `data/calendars/2026-2027.json` en `data/calendars/2027-2028.json`.
2. Mettre à jour les dates (`debut_annee`, `fin_annee`, `periodes`, `feries`).
3. C'est tout — la CLI et l'app web listent automatiquement les fichiers
   présents dans `data/calendars/`.

On peut aller plus loin et automatiser entièrement cette étape avec une tâche
planifiée (cron, GitHub Actions) qui récupère le fichier `.ics` officiel du
ministère (`data.education.gouv.fr`) et le convertit en JSON — c'est le seul
morceau qui demanderait un peu de code si vous voulez zéro intervention
manuelle d'une année sur l'autre.

## Tests

```bash
python tests/test_scheduler.py
```

## Fonctionnalités de l'app web

- **Périodes de vacances affichées** : le formulaire liste les dates de
  chaque période de vacances pour la zone choisie, sous les activités.
  Elles se rafraîchissent automatiquement si vous changez de zone ou d'année.
- **Dates de début/fin par activité** : chaque activité peut avoir sa propre
  première et dernière séance (facultatif). Utile pour une activité qui ne
  démarre pas à la rentrée (inscriptions plus tardives) ou qui se termine
  avant la fin de l'année (stage, cycle court). Laissées vides, l'activité
  court sur toute l'année scolaire — comportement déjà présent dans
  `planning_scolaire/activites.py` et la CLI, simplement exposé dans le
  formulaire web.
- **Aperçu d'une semaine type** : un calendrier hebdomadaire (lundi à
  dimanche) se construit en direct au fur et à mesure que vous remplissez
  les activités, pour repérer visuellement les chevauchements d'horaires.
  Cet aperçu ne tient pas compte des vacances — c'est une vue "semaine de
  classe normale", pas un calendrier daté.
- **Sauvegarde / restauration** : un bouton « Exporter (.json) » télécharge
  l'état complet du formulaire (zone, année, fériés cochés, activités, avec
  leurs dates de début/fin) dans un fichier. Le bouton « Importer une
  sauvegarde » recharge ce fichier dans le formulaire. Le navigateur
  conserve aussi automatiquement une copie locale (`localStorage`) : fermer
  l'onglet par erreur ne fait rien perdre. Ce même fichier de sauvegarde est
  directement réutilisable en ligne de commande :

  ```bash
  python -m planning_scolaire.cli --activites sauvegarde-activites.json --sortie mes_agendas/
  ```

  (La CLI lit la zone, l'année et les fériés directement depuis le fichier ;
  `--zone`/`--annee` restent disponibles pour les surcharger.)

## Limites connues

- Corse et outre-mer suivent des calendriers spécifiques, non couverts ici.
- Les interruptions propres à une association (stage, compétition) ne sont
  pas gérées : à ajouter manuellement dans le calendrier après import.
