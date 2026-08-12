# 🏥 MediNote CRM - Guide d'Installation et d'Utilisation du Système d'Administration

## 📋 Vue d'ensemble

Ce guide explique comment installer et utiliser le système complet de gestion des utilisateurs avec authentification JWT pour la plateforme MediNote CRM.

## 🚀 Installation

### 1. Prérequis

- Python 3.9+
- Node.js 18+
- SQLite (inclus dans Python)

### 2. Backend

```bash
# Naviguer vers le dossier backend
cd backend

# Installer les dépendances
pip install -r requirements.txt

# Initialiser la base de données et créer l'admin par défaut
python scripts/init_admin.py

# Démarrer le serveur backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend

```bash
# Naviguer vers le dossier frontend
cd frontend

# Installer les dépendances
npm install

# Démarrer le serveur de développement
npm run dev
```

## 🔐 Comptes par Défaut

### Administrateur
- **Email**: `admin@medilab.tn`
- **Mot de passe**: `admin123`
- **Rôle**: Administrateur

### Délégués de Test
- **Email**: `delegate1@medilab.tn` | **Mot de passe**: `delegate123`
- **Email**: `delegate2@medilab.tn` | **Mot de passe**: `delegate123`
- **Email**: `delegate3@medilab.tn` | **Mot de passe**: `delegate123`

## 🎯 Fonctionnalités du Système

### 📊 Tableau de Bord Admin (`/admin/dashboard`)

#### Statistiques en Temps Réel
- **Total utilisateurs**: Nombre total de comptes créés
- **Utilisateurs actifs**: Comptes actuellement actifs
- **Utilisateurs bannis**: Comptes suspendus
- **Délégués**: Nombre de délégués médicaux

#### Gestion des Utilisateurs
- **Liste complète** avec pagination
- **Recherche** par nom, email, username
- **Filtres** par rôle (admin/délégué)
- **Filtres** par statut (actif/banni/inactif)
- **Filtres** par région (Tunis, Sfax, Sousse...)

#### Actions Admin
- **👁️ Voir détails**: Modal avec informations complètes
- **✏️ Modifier**: Mettre à jour profil, rôle, statut
- **🚫 Bannir**: Suspendre l'accès à la plateforme
- **✅ Débannir**: Réactiver un compte suspendu
- **🗑️ Supprimer**: Suppression définitive

### 👤 Page Profil (`/profile`)

#### Informations Personnelles
- **Photo de profil** (avec upload)
- **Nom complet**, email, téléphone
- **Région** et secteur d'affectation
- **Biographie** et description

#### Statistiques d'Activité
- **📊 Visites**: Nombre total de visites effectuées
- **📄 Rapports**: Rapports créés et gérés
- **👥 Médecins**: Nombre de médecins suivis
- **⭐ Score qualité**: Score moyen de performance

#### Modifications du Profil
- **Mode édition** avec validation
- **Sauvegarde automatique** des modifications
- **Messages de confirmation** d'erreurs

## 🔧 Configuration Technique

### Architecture Backend

#### Modèle Utilisateur (`models/user.py`)
```python
class User(Base):
    # Champs principaux
    id, uuid, email, username, full_name, password_hash
    
    # Informations enrichies
    phone, region, sector, avatar_url, bio
    
    # Gestion des accès
    role (admin/delegate), status (active/banned/inactive)
    
    # Statistiques
    total_visits, total_reports, total_doctors_followed, average_quality_score
```

#### Authentification JWT (`services/auth_service.py`)
- **Tokens d'accès**: 24 heures de validité
- **Tokens de refresh**: 7 jours de validité
- **Hash bcrypt** pour les mots de passe
- **Validation automatique** des tokens expirés

#### API REST (`routers/auth.py`)
- **POST /api/auth/login**: Connexion
- **POST /api/auth/register**: Inscription
- **GET /api/auth/me**: Profil utilisateur
- **PUT /api/auth/me**: Mise à jour profil
- **GET /api/auth/users**: Liste utilisateurs (admin)
- **POST /api/auth/users/{id}/ban**: Bannir (admin)
- **POST /api/auth/users/{id}/unban**: Débannir (admin)

### Architecture Frontend

#### Contexte d'Authentification (`context/AuthContext.jsx`)
- **Gestion automatique** des tokens
- **Rafraîchissement automatique** des tokens expirés
- **État global** de l'utilisateur
- **Hook useAuth()** pour les composants

#### API Client (`api/authApi.js`)
- **Requêtes authentifiées** automatiques
- **Gestion des erreurs** centralisée
- **Refresh token** transparent
- **Typescript-ready** avec JSDoc

#### Pages Principales
- **AdminDashboardPage**: Gestion complète des utilisateurs
- **ProfilePage**: Profil personnel et statistiques
- **LoginPage**: Connexion avec JWT
- **RegisterPage**: Inscription des nouveaux utilisateurs

## 🛡️ Sécurité

### Authentification
- **Mots de passe hashés** avec bcrypt
- **Tokens JWT** signés avec clé secrète
- **Expiration automatique** des tokens
- **Refresh tokens** pour sessions prolongées

### Autorisations
- **Rôles basés** sur les tokens JWT
- **Protection des routes** avec ProtectedRoute
- **Vérification automatique** du rôle admin
- **Séparation claire** admin/délégué

### Validation
- **Email unique** lors de l'inscription
- **Username unique** pour chaque utilisateur
- **Validation des entrées** côté serveur
- **Messages d'erreur** sécurisés

## 📝 Utilisation Quotidienne

### Pour l'Administrateur

1. **Connexion**: Utiliser le compte admin@medilab.tn
2. **Tableau de bord**: Accéder à `/admin/dashboard`
3. **Surveiller les utilisateurs**: Consulter les statistiques
4. **Gérer les comptes**: Modifier, bannir, supprimer
5. **Créer des délégués**: Via le formulaire d'inscription

### Pour le Délégué

1. **Connexion**: Utiliser son email et mot de passe
2. **Profil**: Accéder à `/profile` pour voir ses infos
3. **Modification**: Mettre à jour ses informations personnelles
4. **Statistiques**: Consulter son activité et performance

## 🔍 Dépannage

### Problèmes Communs

#### "Compte suspendu"
- **Cause**: L'utilisateur a été banni par un admin
- **Solution**: Contacter l'administrateur pour débannir

#### "Token expired"
- **Cause**: Token JWT expiré
- **Solution**: Reconnexion automatique gérée par le frontend

#### "Invalid credentials"
- **Cause**: Email ou mot de passe incorrect
- **Solution**: Vérifier les identifiants ou demander une réinitialisation

#### Logs Utiles
```bash
# Backend logs
uvicorn main:app --reload

# Frontend console (F12)
# Vérifier les erreurs réseau dans l'onglet Network
```

## 🚀 Maintenance

### Sauvegarde de la Base de Données
```bash
# Sauvegarder la base SQLite
cp backend/database.db backend/database_backup_$(date +%Y%m%d).db
```

### Mise à Jour des Dépendances
```bash
# Backend
pip install -r requirements.txt --upgrade

# Frontend
npm update
```

### Nettoyage des Tokens
Les tokens expirés sont automatiquement nettoyés lors de la déconnexion.

## 📞 Support

Pour toute question technique ou problème d'utilisation:
1. Consulter les logs du backend et du frontend
2. Vérifier la configuration des variables d'environnement
3. S'assurer que tous les prérequis sont installés
4. Contacter l'équipe de développement MediNote

---

**🎉 Félicitations! Votre système MediNote CRM est maintenant opérationnel avec une gestion complète des utilisateurs!**
