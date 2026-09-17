# Planning activités — version Flutter/Dart

Réécriture en Dart du projet Python `planning-activites`, pour pouvoir
compiler vers Android, le web, et Windows depuis la même base de code.

## ⚠️ Avant toute chose : à vérifier de votre côté

Ce code a été écrit sans pouvoir compiler ni lancer `flutter analyze` /
`flutter test` — l'environnement qui l'a généré n'a pas le SDK Flutter
installé. La logique a été relue attentivement et suit fidèlement le
comportement du projet Python (mêmes règles de calcul, mêmes tests), mais
la toute première chose à faire en ouvrant ce projet est :

```bash
flutter pub get
flutter analyze
flutter test
```

`flutter analyze` signalera immédiatement toute erreur de syntaxe ou d'API
(les noms de paramètres des widgets Flutter changent parfois d'une version
à l'autre). `flutter test` vérifie que le calcul des séances se comporte
comme attendu — ce sont les mêmes cas que `tests/test_scheduler.py` côté
Python.

## Prérequis

- [Flutter SDK](https://docs.flutter.dev/get-started/install) (inclut Dart)
- Pour Android : Android Studio + SDK Android
- Pour Windows : rien de plus, `flutter build windows` fonctionne avec Flutter seul sous Windows

Vérifiez votre installation :
```bash
flutter doctor
```

## Structure du projet

```
planning_activites_flutter/
├── assets/calendars/2026-2027.json  ← mêmes données que le projet Python
├── lib/
│   ├── models/                         cœur métier, Dart pur (sans Flutter)
│   │   ├── calendrier_scolaire.dart       zones, périodes, fériés
│   │   └── activite.dart                  Activite + calcul des séances
│   ├── services/
│   │   ├── calendrier_loader.dart         charge le JSON (seul fichier Flutter du cœur)
│   │   ├── ics_service.dart               génère .ics et .zip, Dart pur
│   │   ├── export_service.dart            enregistre via la boîte de dialogue native
│   │   └── sauvegarde_service.dart        sauvegarde locale + export/import .json
│   ├── widgets/                        composants d'interface réutilisables
│   ├── screens/accueil_screen.dart     écran principal
│   └── main.dart
└── test/scheduler_test.dart          tests du cœur métier
```

Comme côté Python, `models/` et `services/ics_service.dart` ne dépendent
pas de Flutter — testables indépendamment de l'interface.

## Lancer l'application

```bash
flutter run -d chrome     # dans le navigateur
flutter run -d windows    # application Windows native
flutter run                # choisit un appareil/émulateur Android connecté
```

## Générer les livrables

```bash
flutter build apk --release       # build/app/outputs/flutter-apk/app-release.apk
flutter build web                 # build/web/  (à servir via un serveur HTTP, voir ci-dessous)
flutter build windows --release   # build/windows/x64/runner/Release/
```

Pour tester la version web localement sans tout héberger :
```bash
cd build/web && python3 -m http.server
```

## Ajouter une nouvelle année scolaire

1. Copier `assets/calendars/2026-2027.json` en `assets/calendars/2027-2028.json`, mettre à jour les dates.
2. Déclarer le nouveau fichier dans `pubspec.yaml` sous `flutter: assets:`.
3. Ajouter `'2027-2028'` à la liste `anneesDisponibles` dans `lib/services/calendrier_loader.dart`.

## Différences avec la version Python

- Le calcul des séances et la génération `.ics` suivent exactement la même
  logique (mêmes tests, mêmes cas limites).
- Le format de sauvegarde `.json` exporté est compatible avec celui de la
  CLI Python (`planning_scolaire/cli.py`) : les champs sont identiques.
- Il n'y a pas d'équivalent du plafond "gratuit / premium" de l'app Flask
  ici — à ajouter si vous voulez reproduire cette logique de monétisation
  dans l'appli mobile/desktop.
- La persistance automatique utilise `shared_preferences` (équivalent du
  `localStorage` du navigateur) plutôt qu'un fichier sur disque.
