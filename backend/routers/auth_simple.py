"""
routers/auth_simple.py
Routeur d'authentification simplifié sans Pydantic
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
try:
    from jose import JWTError, jwt
except ImportError:
    import jwt
    JWTError = jwt.exceptions.InvalidTokenError
import hashlib
import uuid
from datetime import datetime, timedelta

from services.db_service import get_db, engine
from models.user import User, UserRole, UserStatus

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Configuration JWT
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 heures

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def hash_password_simple(password: str) -> str:
    """Hash simple avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password_simple(plain_password: str, hashed_password: str) -> bool:
    """Vérification simple"""
    return hash_password_simple(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Créer un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Récupérer l'utilisateur courant"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Connexion utilisateur"""
    try:
        # Chercher l'utilisateur par email ou username
        user = db.query(User).filter(
            (User.email == form_data.username) | (User.username == form_data.username)
        ).first()
        
        if not user or not verify_password_simple(form_data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Identifiants incorrects")
        
        if user.status == UserStatus.BANNED:
            raise HTTPException(status_code=403, detail="Compte suspendu")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Compte inactif")
        
        # Créer le token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        # Mettre à jour la dernière connexion
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
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
