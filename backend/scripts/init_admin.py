"""
scripts/init_admin.py
Script d'initialisation pour créer l'administrateur par défaut
"""

import sys
from pathlib import Path
from sqlalchemy.orm import Session

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.db_service import engine, init_db
from services.auth_service import AuthService
from models.user import User, UserRole, UserStatus

def create_default_admin():
    """Crée l'administrateur par défaut s'il n'existe pas"""
    
    # Importer tous les modèles pour s'assurer qu'ils sont enregistrés
    from models.user import User
    from models.report_db import Report
    
    # Initialiser la base de données (crée toutes les tables)
    init_db()
    
    # Créer une session
    with Session(engine) as db:
        
        # Vérifier si un admin existe déjà
        existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        
        if existing_admin:
            print(f"✅ Admin déjà existant: {existing_admin.email}")
            return existing_admin
        
        # Créer l'admin par défaut
        admin_data = {
            "email": "admin@medilab.tn",
            "username": "admin",
            "full_name": "Administrateur MediNote",
            "password": "admin123",  # À changer en production!
            "phone": "+216 71 000 000",
            "region": "Tunis",
            "sector": "Siège",
            "role": UserRole.ADMIN,
            "bio": "Administrateur système MediNote CRM"
        }
        
        try:
            admin = AuthService.create_user(db, admin_data)
            print(f"✅ Administrateur créé avec succès: {admin.email}")
            print(f"📧 Email: {admin.email}")
            print(f"👤 Username: {admin.username}")
            print(f"🔑 Mot de passe: admin123 (à changer en production!)")
            print(f"🆔 UUID: {admin.uuid}")
            
            return admin
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de l'admin: {e}")
            return None

def create_sample_delegates():
    """Crée quelques délégués de test"""
    
    with Session(engine) as db:
        
        sample_delegates = [
            {
                "email": "delegate1@medilab.tn",
                "username": "delegate1",
                "full_name": "Ahmed Ben Ali",
                "password": "delegate123",
                "phone": "+216 55 123 456",
                "region": "Tunis",
                "sector": "Nord Tunis",
                "role": UserRole.DELEGATE,
                "bio": "Délégué médical pour la région de Tunis"
            },
            {
                "email": "delegate2@medilab.tn",
                "username": "delegate2",
                "full_name": "Sonia Trabelsi",
                "password": "delegate123",
                "phone": "+216 58 987 654",
                "region": "Sfax",
                "sector": "Centre Sfax",
                "role": UserRole.DELEGATE,
                "bio": "Délégué médical pour la région de Sfax"
            },
            {
                "email": "delegate3@medilab.tn",
                "username": "delegate3",
                "full_name": "Karim Mansouri",
                "password": "delegate123",
                "phone": "+216 97 456 789",
                "region": "Sousse",
                "sector": "Sahel Sousse",
                "role": UserRole.DELEGATE,
                "bio": "Délégué médical pour la région de Sousse"
            }
        ]
        
        created_count = 0
        
        for delegate_data in sample_delegates:
            try:
                # Vérifier si l'utilisateur existe déjà
                existing_user = User.get_by_email(db, delegate_data["email"])
                if existing_user:
                    print(f"⚠️  Délégué déjà existant: {delegate_data['email']}")
                    continue
                
                delegate = AuthService.create_user(db, delegate_data)
                created_count += 1
                print(f"✅ Délégué créé: {delegate.full_name} ({delegate.email})")
                
            except Exception as e:
                print(f"❌ Erreur création délégué {delegate_data['email']}: {e}")
        
        print(f"📊 {created_count} délégués créés avec succès")

def main():
    """Fonction principale d'initialisation"""
    print("🚀 Initialisation du système MediNote...")
    print("=" * 50)
    
    # Créer l'admin par défaut
    admin = create_default_admin()
    
    if admin:
        print("\n📋 Création des délégués de test...")
        create_sample_delegates()
    
    print("\n✨ Initialisation terminée!")
    print("\n🔗 Accès à l'application:")
    print("   Backend: http://localhost:8000")
    print("   Frontend: http://localhost:5173")
    print("   Docs API: http://localhost:8000/docs")
    print("\n👤 Connexion admin:")
    print("   Email: admin@medilab.tn")
    print("   Mot de passe: admin123")

if __name__ == "__main__":
    main()
