# Installation sous Windows 11

Ce guide détaille l'installation de tout ce qu'il faut pour ouvrir et
lancer ce projet dans VS Code sous Windows 11, en utilisant le SDK Flutter
directement depuis VS Code (pas besoin de modifier le PATH à la main).
Comptez 30 à 60 minutes selon la vitesse de votre connexion — l'essentiel
du temps est le téléchargement d'Android Studio.

Si vous voulez seulement tester la version web dans un premier temps,
arrêtez-vous après l'étape 3 (`flutter doctor`) et passez directement à
« Lancer l'application » avec `flutter run -d chrome`. Android Studio n'est
nécessaire que pour compiler un APK Android.

## 1. Installer l'extension Flutter dans VS Code

1. Ouvrez VS Code.
2. Allez dans l'onglet **Extensions** (`Ctrl+Shift+X`).
3. Cherchez **Flutter**, cliquez sur **Installer**. L'extension **Dart**
   s'installe automatiquement avec.

## 2. Installer le SDK Flutter depuis VS Code

C'est VS Code qui télécharge et configure le SDK à votre place — plus besoin
de modifier le PATH à la main.

1. Ouvrez la palette de commandes : `Ctrl+Shift+P`.
2. Tapez `flutter` et sélectionnez **Flutter: New Project**.
3. VS Code demande de localiser le SDK Flutter. Cliquez sur **Download SDK**.
4. Dans la boîte de dialogue **Select Folder for Flutter SDK**, choisissez
   où installer le SDK — par exemple `C:\src`. Évitez les chemins avec
   espaces ou accents, et évitez `Program Files`.
5. Cliquez sur **Clone Flutter**. Le téléchargement prend quelques minutes ;
   si ça semble bloqué, cliquez sur **Cancel** et relancez l'installation.
6. Cliquez sur **Add SDK to PATH** quand VS Code le propose.
7. Si une notice Google Analytics apparaît, validez par **OK**.
8. **Fermez tous les terminaux ouverts et redémarrez VS Code** pour que le
   PATH mis à jour soit pris en compte partout.
9. Une fois le SDK installé, vous pouvez fermer l'assistant **Flutter: New
   Project** sans créer de projet — on va ouvrir le vôtre directement à
   l'étape 7.

## 3. Vérifier l'installation

Dans un nouveau terminal (PowerShell ou l'invite de commandes) :

```powershell
flutter doctor
```

Cette commande liste précisément ce qui manque, avec des instructions pour
chaque `✗` rouge : licences Android non acceptées, Android Studio absent,
Git manquant, etc. Ne passez pas à l'étape suivante tant qu'il reste des
erreurs bloquantes (les avertissements sur des IDE non installés — par
exemple Visual Studio pour le C++ desktop — peuvent être ignorés si vous ne
comptez pas cibler Windows natif).

## 4. Installer Android Studio (nécessaire pour cibler Android)

Ignorez cette étape si vous ne visez que la version web ou Windows natif.

1. Téléchargez Android Studio depuis
   [developer.android.com/studio](https://developer.android.com/studio).
2. Lancez l'installeur, laissez les options par défaut (elles installent le
   SDK Android nécessaire).
3. Une fois Android Studio ouvert, allez dans **More Actions → SDK
   Manager** et vérifiez qu'au moins une version du SDK Android est cochée.

## 5. Accepter les licences Android

Toujours nécessaire si vous ciblez Android, même avec Android Studio déjà
installé :

```powershell
flutter doctor --android-licenses
```

Répondez `y` à chaque question posée.

## 6. Relancer flutter doctor

```powershell
flutter doctor
```

Tous les points pertinents pour vos cibles (web, Android, éventuellement
Windows desktop) doivent afficher `✓`.

## 7. Ouvrir le projet dans VS Code

L'extension Flutter est déjà installée depuis l'étape 1. Il ne reste qu'à
ouvrir le projet : **Fichier → Ouvrir le dossier**, sélectionnez
`planning_activites_flutter`.

## 8. Installer les dépendances du projet

Dans le terminal intégré de VS Code (`` Ctrl+ù `` ou **Terminal → Nouveau
terminal**), à la racine du projet :

```powershell
flutter pub get
```

## 9. Vérifier que tout fonctionne

```powershell
flutter analyze
flutter test
```

`flutter analyze` doit ne remonter aucune erreur. `flutter test` doit
afficher que tous les tests du dossier `test/` passent — ce sont les mêmes
cas que côté Python (`test_scheduler.py`) : une séance de Toussaint
retirée, la première séance conservée hors vacances, une activité
entièrement pendant les vacances qui ne produit rien.

Si l'une de ces deux commandes échoue, gardez le message d'erreur complet
affiché dans le terminal : c'est ce qu'il faut fournir pour corriger le
problème.

## 10. Lancer l'application

```powershell
flutter run -d chrome     # dans le navigateur, le plus rapide à tester
flutter run                 # sur un appareil ou émulateur Android connecté
flutter run -d windows      # application Windows native (nécessite les
                             # "Desktop development with C++" via Visual
                             # Studio Build Tools, voir flutter doctor)
```

## 11. Générer les livrables

```powershell
flutter build apk --release       # → build\app\outputs\flutter-apk\app-release.apk
flutter build web                 # → build\web\
flutter build windows --release   # → build\windows\x64\runner\Release\
```

Pour tester la version web générée sans l'héberger en ligne :

```powershell
cd build\web
python -m http.server
```

Puis ouvrez `http://localhost:8000` dans le navigateur.

## Problèmes fréquents

**`flutter : le terme n'est pas reconnu`** — le PATH n'a pas été mis à jour
correctement, ou le terminal a été ouvert avant l'étape 2. Revérifiez le
PATH et ouvrez un terminal tout neuf.

**`Unable to locate Android SDK`** — Android Studio n'a pas terminé son
installation du SDK, ou `flutter doctor` ne trouve pas son emplacement.
Relancez Android Studio, ouvrez **SDK Manager**, notez le chemin du SDK
affiché en haut de la fenêtre, puis :

```powershell
flutter config --android-sdk "chemin-copié-ici"
```

**Licences Android non acceptées malgré l'étape 5** — relancez la commande
depuis un terminal ouvert après l'installation d'Android Studio, pas avant.

**Erreur liée à un package lors de `flutter pub get`** — vérifiez votre
connexion internet ; le SDK télécharge les dépendances depuis pub.dev à ce
moment-là.
