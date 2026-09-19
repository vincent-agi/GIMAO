# Guide d'installation — GIMAO

Ce guide explique comment installer l'application GIMAO sur un ordinateur, sans connaissances techniques particulières.

## 1. Prérequis : installer Docker Desktop

GIMAO fonctionne grâce à un logiciel appelé **Docker Desktop**, qui permet de faire tourner l'application sans installation complexe.

1. Télécharger Docker Desktop depuis le site officiel : https://www.docker.com/products/docker-desktop
2. Installer le logiciel en suivant les instructions à l'écran (redémarrage de l'ordinateur possible).
3. Lancer Docker Desktop et attendre que l'icône de la baleine, en bas à droite de l'écran, soit stable (ne clignote plus). Cela signifie que Docker est prêt.

Cette étape n'est à faire qu'une seule fois.

## 2. Installer GIMAO

### Windows

1. Dézipper le dossier `GIMAO_installation.zip` reçu, à l'endroit de votre choix sur l'ordinateur (par exemple sur le Bureau).
2. Ouvrir le dossier obtenu.
3. Vérifier que Docker Desktop est bien lancé (icône baleine stable).
4. Double-cliquer sur le fichier **`install.bat`**.
5. Une fenêtre noire s'ouvre et affiche la progression de l'installation (téléchargement, démarrage, initialisation de la base de données). Cela peut prendre plusieurs minutes selon la connexion internet, surtout la première fois.
6. À la fin, l'application s'ouvre automatiquement dans le navigateur, à l'adresse **http://localhost**.

Si une fenêtre affiche une erreur mentionnant Docker, cela signifie que Docker Desktop n'est pas lancé : ouvrez-le, attendez que l'icône baleine soit stable, puis relancez `install.bat`.

### Linux / macOS

1. Récupérer le dossier du projet, à l'endroit de votre choix sur l'ordinateur.
2. Ouvrir un terminal dans ce dossier.
3. Vérifier que Docker Desktop (ou le service Docker) est bien lancé.
4. Exécuter :
   ```bash
   ./install.sh
   ```
   Si le script refuse de s'exécuter, le rendre exécutable d'abord : `chmod +x install.sh`.
5. Le terminal affiche la progression de l'installation (téléchargement, démarrage, initialisation de la base de données). Cela peut prendre plusieurs minutes selon la connexion internet, surtout la première fois.
6. À la fin, l'application s'ouvre automatiquement dans le navigateur, à l'adresse **http://localhost**.

Si un message d'erreur mentionne Docker, cela signifie que Docker n'est pas lancé : démarrez-le, attendez qu'il soit prêt, puis relancez `./install.sh`.

## 3. Se connecter

Un seul compte est créé automatiquement lors de l'installation, avec le rôle **Responsable GMAO** (accès complet) :

- Adresse : http://localhost
- Identifiant : `responsable`
- Aucun mot de passe n'est défini au départ : à la première connexion, l'application invite à en créer un.

Aucune autre donnée (équipements, utilisateurs, interventions...) n'est préchargée : la base démarre vide, prête à recevoir les données réelles de l'entreprise.

### Charger un jeu de données de démonstration (optionnel)

Pour une utilisation en formation ou en salle de TP, un jeu de données factices (équipements, utilisateurs, interventions, stocks) peut être chargé depuis l'application elle-même : une fois connecté avec le compte Responsable GMAO, un bouton **« Précharger les données de démo »** est disponible sur le tableau de bord.

Attention : cette action **supprime toutes les données existantes** avant de charger le jeu de démonstration. Une confirmation est demandée avant toute exécution. À ne jamais utiliser sur une base contenant des données réelles.

## 4. Utilisation au quotidien

Une fois installée, l'application reste disponible tant que Docker Desktop est lancé. Il suffit d'ouvrir un navigateur et d'aller sur **http://localhost**, aucun script à relancer.

## 5. Mettre à jour l'application

Quand une nouvelle version est disponible :

**Windows**
1. Vérifier que Docker Desktop est lancé.
2. Double-cliquer sur **`update.bat`**, dans le même dossier.
3. Attendre la fin du message "Mise à jour terminée", puis l'application se rouvre automatiquement dans le navigateur.

**Linux / macOS**
1. Vérifier que Docker est lancé.
2. Dans un terminal, à la racine du dossier, exécuter **`./update.sh`**.
3. Attendre la fin du message "Mise à jour terminée", puis l'application se rouvre automatiquement dans le navigateur.

Les données déjà enregistrées (équipements, interventions, utilisateurs...) sont conservées lors d'une mise à jour, elles ne sont jamais supprimées par ce processus.

## En cas de problème

Contactez la personne qui vous a transmis ce guide en précisant :
- le message d'erreur affiché à l'écran (si possible une capture d'écran) ;
- l'étape du guide à laquelle le problème est survenu.
