"""
routers/auth_basic.py
Routeur d'authentification ultra-simple sans JWT
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import hashlib
import uuid
from datetime import datetime

from services.db_service import get_db, engine
from models.user import User, UserRole, UserStatus

router = APIRouter(prefix="/api/auth", tags=["auth"])

security = HTTPBasic()

def hash_password_simple(password: str) -> str:
    """Hash simple avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password_simple(plain_password: str, hashed_password: str) -> bool:
    """Vérification simple"""
    return hash_password_simple(plain_password) == hashed_password

def get_current_user(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    """Récupérer l'utilisateur courant avec Basic Auth"""
    try:
        # Chercher l'utilisateur par email ou username
        user = db.query(User).filter(
            (User.email == credentials.username) | (User.username == credentials.username)
        ).first()
        
        if not user or not verify_password_simple(credentials.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Identifiants incorrects")
        
        if user.status == UserStatus.BANNED:
            raise HTTPException(status_code=403, detail="Compte suspendu")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Compte inactif")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.post("/login")
async def login(email: str, password: str, db: Session = Depends(get_db)):
    """Connexion utilisateur simple"""
    try:
        # Chercher l'utilisateur par email
        user = db.query(User).filter(User.email == email).first()
        
        if not user or not verify_password_simple(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Identifiants incorrects")
        
        if user.status == UserStatus.BANNED:
            raise HTTPException(status_code=403, detail="Compte suspendu")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Compte inactif")
        
        # Mettre à jour la dernière connexion
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
                "phone": user.phone,
                "region": user.region,
                "sector": user.sector,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "total_visits": user.total_visits,
                "total_reports": user.total_reports,
                "total_doctors_followed": user.total_doctors_followed,
                "average_quality_score": user.average_quality_score
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Récupérer les infos de l'utilisateur courant"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "phone": current_user.phone,
        "region": current_user.region,
        "sector": current_user.sector,
        "avatar_url": current_user.avatar_url,
        "bio": current_user.bio,
        "status": current_user.status.value,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        "total_visits": current_user.total_visits,
        "total_reports": current_user.total_reports,
        "total_doctors_followed": current_user.total_doctors_followed,
        "average_quality_score": current_user.average_quality_score
    }

@router.get("/users")
async def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lister tous les utilisateurs (admin seulement)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    users = db.query(User).all()
    return [{
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value,
        "phone": user.phone,
        "region": user.region,
        "sector": user.sector,
        "status": user.status.value,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "total_visits": user.total_visits,
        "total_reports": user.total_reports,
        "total_doctors_followed": user.total_doctors_followed,
        "average_quality_score": user.average_quality_score
    } for user in users]

@router.get("/test")
async def test_endpoint():
    """Endpoint de test simple"""
    return {"message": "API MediNote fonctionne!", "status": "ok"}
