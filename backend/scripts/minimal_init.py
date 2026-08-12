"""
scripts/minimal_init.py
Script d'initialisation minimal sans dépendances complexes
"""

import sys
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text
import hashlib
import uuid
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.db_service import engine

def hash_password_simple(password: str) -> str:
    """Hash simple avec SHA-256 (temporaire)"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_minimal_admin():
    """Crée un admin minimal sans dépendances complexes"""
    
    with engine.connect() as conn:
        # Créer la table users si elle n'existe pas
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ))
        users_exists = result.fetchone() is not None
        
        if not users_exists:
            print("📝 Création de la table users...")
            conn.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT UNIQUE NOT NULL,
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
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
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
        
        # Vérifier si un admin existe déjà
        result = conn.execute(text(
            "SELECT * FROM users WHERE role = 'admin' LIMIT 1"
        ))
        existing_admin = result.fetchone()
        
        if existing_admin:
            print(f"✅ Admin déjà existant: {existing_admin[2]}")  # email est à l'index 2
            return existing_admin
        
        # Créer l'admin
        admin_uuid = str(uuid.uuid4())
        admin_hash = hash_password_simple("admin123")
        
        conn.execute(text("""
            INSERT INTO users (
                uuid, email, username, full_name, password_hash, 
                phone, region, sector, role, status, is_active, bio
            ) VALUES (
                :uuid, :email, :username, :full_name, :password_hash,
                :phone, :region, :sector, :role, :status, :is_active, :bio
            )
        """), {
            'uuid': admin_uuid,
            'email': 'admin@medilab.tn',
            'username': 'admin',
            'full_name': 'Administrateur MediNote',
            'password_hash': admin_hash,
            'phone': '+216 71 000 000',
            'region': 'Tunis',
            'sector': 'Siège',
            'role': 'admin',
            'status': 'active',
            'is_active': 1,
            'bio': 'Administrateur système MediNote CRM'
        })
        
        conn.commit()
        
        print(f"✅ Administrateur créé avec succès!")
        print(f"📧 Email: admin@medilab.tn")
        print(f"👤 Username: admin")
        print(f"🔑 Mot de passe: admin123")
        print(f"🆔 UUID: {admin_uuid}")
        
        return True

def main():
    """Fonction principale"""
    print("🚀 Initialisation minimale du système MediNote...")
    print("=" * 50)
    
    try:
        create_minimal_admin()
        
        print("\n✨ Initialisation terminée!")
        print("\n🔗 Accès à l'application:")
        print("   Backend: http://localhost:8000")
        print("   Frontend: http://localhost:5173")
        print("\n👤 Connexion admin:")
        print("   Email: admin@medilab.tn")
        print("   Mot de passe: admin123")
        print("\n⚠️  Note: Utilise un hash SHA-256 temporaire")
        print("   Pour une sécurité complète, installez bcrypt plus tard")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
