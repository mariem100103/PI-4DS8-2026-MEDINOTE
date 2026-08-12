"""
models/user.py
Modèle SQLAlchemy pour la gestion des utilisateurs MediNote
"""

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from .base import Base

class UserRole(str, Enum):
    ADMIN = "admin"
    DELEGATE = "delegate"

class UserStatus(str, Enum):
    ACTIVE = "active"
    BANNED = "banned"
    INACTIVE = "inactive"

class User(Base):
    __tablename__ = "users"
    
    # Champs principaux
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Informations personnelles enrichies
    phone = Column(String(20))
    region = Column(String(100))  # Tunis, Sfax, Sousse, etc.
    sector = Column(String(100))  # Secteur spécifique dans la région
    avatar_url = Column(String(500))  # URL de la photo de profil
    
    # Gestion des accès
    role = Column(SQLEnum(UserRole), default=UserRole.DELEGATE, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime(timezone=True))
    last_login_ip = Column(String(45))  # IPv6 compatible
    
    # Statistiques d'activité
    total_visits = Column(Integer, default=0)
    total_reports = Column(Integer, default=0)
    total_doctors_followed = Column(Integer, default=0)
    average_quality_score = Column(Float, default=0.0)
    
    # Informations supplémentaires
    bio = Column(Text)
    notes = Column(Text)  # Notes admin internes
    
    def __repr__(self):
        return f"<User(email='{self.email}', role='{self.role}', status='{self.status}')>"
    
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    @property
    def is_delegate(self):
        return self.role == UserRole.DELEGATE
    
    @property
    def is_banned(self):
        return self.status == UserStatus.BANNED
    
    @property
    def can_login(self):
        return self.is_active and self.status == UserStatus.ACTIVE
    
    def update_last_login(self, ip_address: str = None):
        """Met à jour la date et IP de dernière connexion"""
        self.last_login_at = datetime.now(timezone.utc)
        if ip_address:
            self.last_login_ip = ip_address
        self.updated_at = datetime.now(timezone.utc)
    
    def ban(self):
        """Bannit l'utilisateur"""
        self.status = UserStatus.BANNED
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
    
    def unban(self):
        """Débannit l'utilisateur"""
        self.status = UserStatus.ACTIVE
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)
    
    def update_stats(self, visits: int = None, reports: int = None, 
                    doctors: int = None, quality_score: float = None):
        """Met à jour les statistiques d'activité"""
        if visits is not None:
            self.total_visits = visits
        if reports is not None:
            self.total_reports = reports
        if doctors is not None:
            self.total_doctors_followed = doctors
        if quality_score is not None:
            self.average_quality_score = quality_score
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self, include_sensitive: bool = False):
        """Convertit l'utilisateur en dictionnaire"""
        data = {
            'id': self.id,
            'uuid': self.uuid,
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'phone': self.phone,
            'region': self.region,
            'sector': self.sector,
            'avatar_url': self.avatar_url,
            'role': self.role.value,
            'status': self.status.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'last_login_ip': self.last_login_ip,
            'total_visits': self.total_visits,
            'total_reports': self.total_reports,
            'total_doctors_followed': self.total_doctors_followed,
            'average_quality_score': self.average_quality_score,
            'bio': self.bio,
        }
        
        if include_sensitive:
            data.update({
                'notes': self.notes,
            })
            
        return data
    
    @classmethod
    def get_by_email(cls, session, email: str):
        """Récupère un utilisateur par email"""
        return session.query(cls).filter(cls.email == email.lower()).first()
    
    @classmethod
    def get_by_username(cls, session, username: str):
        """Récupère un utilisateur par username"""
        return session.query(cls).filter(cls.username == username).first()
    
    @classmethod
    def get_active_users(cls, session):
        """Récupère tous les utilisateurs actifs"""
        return session.query(cls).filter(cls.is_active == True).all()
    
    @classmethod
    def get_by_role(cls, session, role: UserRole):
        """Récupère les utilisateurs par rôle"""
        return session.query(cls).filter(cls.role == role).all()
    
    @classmethod
    def search_users(cls, session, query: str, role: UserRole = None, 
                    status: UserStatus = None, region: str = None):
        """Recherche d'utilisateurs avec filtres"""
        query_filter = session.query(cls)
        
        if query:
            query_filter = query_filter.filter(
                (cls.full_name.ilike(f"%{query}%")) |
                (cls.email.ilike(f"%{query}%")) |
                (cls.username.ilike(f"%{query}%"))
            )
        
        if role:
            query_filter = query_filter.filter(cls.role == role)
        
        if status:
            query_filter = query_filter.filter(cls.status == status)
        
        if region:
            query_filter = query_filter.filter(cls.region.ilike(f"%{region}%"))
        
        return query_filter.all()
