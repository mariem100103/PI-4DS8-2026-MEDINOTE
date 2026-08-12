"""
routers/auth.py
Routes API pour l'authentification et la gestion des utilisateurs
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from sqlalchemy.orm import Session

from services.db_service import get_db
from services.auth_service import AuthService
from models.user import User, UserRole, UserStatus

# Router
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Security
security = HTTPBearer()

# Pydantic Models
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    phone: Optional[str] = None
    region: Optional[str] = None
    sector: Optional[str] = None
    role: Optional[str] = "delegate"

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    phone: Optional[str] = None
    region: Optional[str] = None
    sector: Optional[str] = None
    role: str = "delegate"
    bio: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    region: Optional[str] = None
    sector: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    notes: Optional[str] = None  # Admin only
    password: Optional[str] = None
    role: Optional[str] = None  # Admin only
    status: Optional[str] = None  # Admin only

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class UserResponse(BaseModel):
    id: int
    uuid: str
    email: str
    username: str
    full_name: str
    phone: Optional[str]
    region: Optional[str]
    sector: Optional[str]
    avatar_url: Optional[str]
    role: str
    status: str
    is_active: bool
    created_at: str
    updated_at: str
    last_login_at: Optional[str]
    last_login_ip: Optional[str]
    total_visits: int
    total_reports: int
    total_doctors_followed: int
    average_quality_score: float
    bio: Optional[str]

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int

# Dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dépendance pour obtenir l'utilisateur courant"""
    return AuthService.get_current_user(credentials.credentials, db)

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dépendance pour obtenir l'utilisateur admin courant"""
    return AuthService.get_current_admin_user(credentials.credentials, db)

# Routes
@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Connexion d'un utilisateur"""
    try:
        # Récupérer l'IP du client
        client_ip = request.client.host
        
        # Authentifier l'utilisateur
        user = AuthService.authenticate_user(
            db, user_data.email, user_data.password, client_ip
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Créer les tokens
        tokens = AuthService.create_user_tokens(user)
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Inscription d'un nouvel utilisateur"""
    try:
        # Créer l'utilisateur
        user = AuthService.create_user(db, user_data.dict())
        
        return UserResponse(**user.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/refresh", response_model=dict)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Rafraîchir le token d'accès"""
    try:
        tokens = AuthService.refresh_access_token(credentials.credentials, db)
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Obtenir les informations de l'utilisateur courant"""
    return UserResponse(**current_user.to_dict())

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mettre à jour les informations de l'utilisateur courant"""
    try:
        # Filtrer les champs modifiables par l'utilisateur lui-même
        update_data = user_data.dict(exclude_unset=True)
        # Exclure les champs admin-only
        admin_only_fields = ["role", "status", "notes"]
        for field in admin_only_fields:
            update_data.pop(field, None)
        
        updated_user = AuthService.update_user(db, current_user.id, update_data, current_user)
        
        return UserResponse(**updated_user.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update failed"
        )

# Routes Admin
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Créer un nouvel utilisateur (admin seulement)"""
    try:
        user = AuthService.create_user(db, user_data.dict())
        return UserResponse(**user.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )

@router.get("/users", response_model=UserListResponse)
async def get_users(
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    region: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Lister les utilisateurs avec filtres (admin seulement)"""
    try:
        # Convertir les filtres
        role_filter = None
        if role:
            try:
                role_filter = UserRole(role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role filter"
                )
        
        status_filter = None
        if status:
            try:
                status_filter = UserStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status filter"
                )
        
        # Rechercher les utilisateurs
        users = User.search_users(
            db, search or "", role_filter, status_filter, region
        )
        
        # Pagination
        total = len(users)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_users = users[start:end]
        
        return UserListResponse(
            users=[UserResponse(**user.to_dict()) for user in paginated_users],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Obtenir les détails d'un utilisateur (admin seulement)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**user.to_dict(include_sensitive=True))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user"
        )

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Mettre à jour un utilisateur (admin seulement)"""
    try:
        update_data = user_data.dict(exclude_unset=True)
        updated_user = AuthService.update_user(db, user_id, update_data, current_admin)
        
        return UserResponse(**updated_user.to_dict(include_sensitive=True))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Supprimer un utilisateur (admin seulement)"""
    try:
        success = AuthService.delete_user(db, user_id, current_admin)
        
        return {"message": "User deleted successfully", "success": success}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Bannir un utilisateur (admin seulement)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Un admin ne peut pas se bannir lui-même
        if current_admin.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot ban yourself"
            )
        
        user.ban()
        db.commit()
        
        return {"message": "User banned successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ban user"
        )

@router.post("/users/{user_id}/unban")
async def unban_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Débannir un utilisateur (admin seulement)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.unban()
        db.commit()
        
        return {"message": "User unbanned successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unban user"
        )

@router.get("/stats")
async def get_user_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Obtenir les statistiques des utilisateurs (admin seulement)"""
    try:
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.status == UserStatus.ACTIVE).count()
        banned_users = db.query(User).filter(User.status == UserStatus.BANNED).count()
        inactive_users = db.query(User).filter(User.status == UserStatus.INACTIVE).count()
        
        admin_users = db.query(User).filter(User.role == UserRole.ADMIN).count()
        delegate_users = db.query(User).filter(User.role == UserRole.DELEGATE).count()
        
        # Stats par région
        regions = db.query(User.region, db.func.count(User.id)).filter(
            User.region.isnot(None)
        ).group_by(User.region).all()
        
        # Stats d'activité
        total_visits = db.query(db.func.sum(User.total_visits)).scalar() or 0
        total_reports = db.query(db.func.sum(User.total_reports)).scalar() or 0
        avg_quality = db.query(db.func.avg(User.average_quality_score)).scalar() or 0
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "banned_users": banned_users,
            "inactive_users": inactive_users,
            "admin_users": admin_users,
            "delegate_users": delegate_users,
            "regions": [{"region": r, "count": c} for r, c in regions],
            "activity": {
                "total_visits": total_visits,
                "total_reports": total_reports,
                "average_quality_score": float(avg_quality)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch stats"
        )
