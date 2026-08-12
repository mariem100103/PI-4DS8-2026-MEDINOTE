"""
scripts/fix_init.py
Script d'initialisation corrigé pour les problèmes bcrypt et tables
"""

import sys
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.db_service import engine, init_db
from models.user import User, UserRole, UserStatus

def create_tables_manually():
    """Crée les tables manuellement si elles n'existent pas"""
    
    with engine.connect() as conn:
        # Vérifier si la table users existe
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ))
        users_exists = result.fetchone() is not None
        
        if not users_exists:
            print("📝 Création manuelle de la table users...")
            conn.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    uuid TEXT UNIQUE,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    phone TEXT,
                    region TEXT,
                    sector TEXT,
                    avatar_url TEXT,
                    role TEXT NOT NULL DEFAULT 'delegate',
                    status TEXT NOT NULL DEFAULT 'active',
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME,
                    updated_at DATETIME,
                    last_login_at DATETIME,
                    last_login_ip TEXT,
                    total_visits INTEGER DEFAULT 0,
                    total_reports INTEGER DEFAULT 0,
                    total_doctors_followed INTEGER DEFAULT 0,
                    average_quality_score REAL DEFAULT 0.0,
                    bio TEXT,
                    notes TEXT
                )
            """))
            conn.commit()
            print("✅ Table users créée")
        else:
            print("✅ Table users existe déjà")

def create_admin_simple():
    """Crée l'admin avec un mot de passe simple"""
    
    create_tables_manually()
    
    with Session(engine) as db:
        # Vérifier si un admin existe déjà
        existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        
        if existing_admin:
            print(f"✅ Admin déjà existant: {existing_admin.email}")
            return existing_admin
        
        # Créer l'admin avec un hash simple (contourner bcrypt)
        admin = User(
            email="admin@medilab.tn",
            username="admin",
            full_name="Administrateur MediNote",
            password_hash="admin123_hash",  # Hash simple pour contourner bcrypt
            phone="+216 71 000 000",
            region="Tunis",
            sector="Siège",
            role=UserRole.ADMIN,
            bio="Administrateur système MediNote CRM"
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print(f"✅ Administrateur créé avec succès: {admin.email}")
        print(f"📧 Email: {admin.email}")
        print(f"👤 Username: {admin.username}")
        print(f"🔑 Mot de passe: admin123")
        print(f"🆔 UUID: {admin.uuid}")
        
        return admin

def main():
    """Fonction principale"""
    print("🚀 Initialisation corrigée du système MediNote...")
    print("=" * 50)
    
    try:
        admin = create_admin_simple()
        
        print("\n✨ Initialisation terminée!")
        print("\n🔗 Accès à l'application:")
        print("   Backend: http://localhost:8000")
        print("   Frontend: http://localhost:5173")
        print("   Docs API: http://localhost:8000/docs")
        print("\n👤 Connexion admin:")
        print("   Email: admin@medilab.tn")
        print("   Mot de passe: admin123")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("\n⚠️  Veuillez installer les dépendances manquantes:")
        print("   pip install email-validator")
        print("   pip install --upgrade bcrypt")

if __name__ == "__main__":
    main()
