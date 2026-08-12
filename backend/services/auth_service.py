"""
services/auth_service.py
Service d'authentification JWT pour MediNote
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.user import User, UserRole, UserStatus
from services.db_service import get_db

# Configuration JWT
SECRET_KEY = "vital-labo-medical-jwt-secret-key-2026"  # À mettre dans .env en production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 heures
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Configuration du hash de mot de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash un mot de passe"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Crée un token JWT d'accès"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Crée un token JWT de rafraîchissement"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Vérifie et décode un token JWT"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Vérifier le type de token
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # Vérifier l'expiration
            exp = payload.get("exp")
            if exp is None or datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str, ip_address: str = None) -> Optional[User]:
        """Authentifie un utilisateur avec email et mot de passe"""
        user = User.get_by_email(db, email)
        
        if not user:
            return None
        
        if not user.verify_password(password, user.password_hash):
            return None
        
        # Vérifier si l'utilisateur peut se connecter
        if not user.can_login:
            if user.is_banned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Compte suspendu. Contactez l'administrateur."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Compte inactif. Contactez l'administrateur."
                )
        
        # Mettre à jour la dernière connexion
        user.update_last_login(ip_address)
        db.commit()
        
        return user
    
    @staticmethod
    def get_current_user(token: str, db: Session) -> User:
        """Récupère l'utilisateur courant à partir du token"""
        payload = AuthService.verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Vérifier que l'utilisateur est toujours actif
        if not user.can_login:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )
        
        return user
    
    @staticmethod
    def get_current_admin_user(token: str, db: Session) -> User:
        """Récupère l'utilisateur admin courant"""
        user = AuthService.get_current_user(token, db)
        
        if not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return user
    
    @staticmethod
    def create_user_tokens(user: User) -> Dict[str, str]:
        """Crée les tokens access et refresh pour un utilisateur"""
        access_token = AuthService.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        
        refresh_token = AuthService.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # en secondes
        }
    
    @staticmethod
    def refresh_access_token(refresh_token: str, db: Session) -> Dict[str, str]:
        """Rafraîchit le token d'accès"""
        payload = AuthService.verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or not user.can_login:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Créer un nouveau token d'accès
        access_token = AuthService.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def create_user(db: Session, user_data: Dict[str, Any]) -> User:
        """Crée un nouvel utilisateur"""
        # Vérifier si l'email existe déjà
        if User.get_by_email(db, user_data["email"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Vérifier si le username existe déjà
        if User.get_by_username(db, user_data["username"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Hasher le mot de passe
        hashed_password = AuthService.get_password_hash(user_data.pop("password"))
        
        # Créer l'utilisateur
        user = User(
            password_hash=hashed_password,
            **user_data
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_data: Dict[str, Any], current_user: User) -> User:
        """Met à jour un utilisateur"""
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Seul un admin peut modifier un autre utilisateur
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user"
            )
        
        # Mettre à jour les champs
        updateable_fields = [
            "full_name", "phone", "region", "sector", "avatar_url", 
            "bio", "notes"  # notes seulement pour admin
        ]
        
        for field in updateable_fields:
            if field in user_data:
                # Vérifier permissions pour notes
                if field == "notes" and not current_user.is_admin:
                    continue
                setattr(user, field, user_data[field])
        
        # Gérer le changement de mot de passe
        if "password" in user_data and user_data["password"]:
            user.password_hash = AuthService.get_password_hash(user_data["password"])
        
        # Gérer le changement de rôle (admin seulement)
        if "role" in user_data and current_user.is_admin:
            try:
                user.role = UserRole(user_data["role"])
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role"
                )
        
        # Gérer le changement de statut (admin seulement)
        if "status" in user_data and current_user.is_admin:
            try:
                user.status = UserStatus(user_data["status"])
                user.is_active = (user.status == UserStatus.ACTIVE)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status"
                )
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: int, current_user: User) -> bool:
        """Supprime un utilisateur"""
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Un admin ne peut pas se supprimer lui-même
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete yourself"
            )
        
        # Seul un admin peut supprimer un utilisateur
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        db.delete(user)
        db.commit()
        
        return True
