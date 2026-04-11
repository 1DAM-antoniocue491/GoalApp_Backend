from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload

from app.database.connection import SessionLocal
from app.api.services.usuario_service import obtener_usuario_por_id_con_roles
from app.schemas.usuario import UsuarioResponse
from app.config import settings

# ============================================================
# CONFIGURACIÓN GLOBAL
# ============================================================

# Importar configuración desde settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ============================================================
# DEPENDENCIA: SESIÓN DE BASE DE DATOS
# ============================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# DEPENDENCIA: OBTENER USUARIO ACTUAL DESDE JWT
# ============================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db=Depends(get_db)
):
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")

        if user_id_str is None:
            raise credenciales_invalidas

        user_id = int(user_id_str)

    except (JWTError, ValueError):
        raise credenciales_invalidas

    # Cargar usuario con roles de forma explícita usando joinedload
    usuario = obtener_usuario_por_id_con_roles(db, user_id)

    if usuario is None:
        raise credenciales_invalidas

    return usuario

# ============================================================
# DEPENDENCIA: VERIFICAR ROLES
# ============================================================

def require_role(role_name: str):
    def role_checker(current_user = Depends(get_current_user)):
        roles = [rol.nombre for rol in current_user.roles]

        if role_name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permisos para realizar esta acción (se requiere rol '{role_name}')"
            )
        return True

    return role_checker

# ============================================================
# FUNCIÓN AUXILIAR: CREAR TOKEN JWT
# (la usarás en el login)
# ============================================================

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
