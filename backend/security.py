import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Cargar variables de entorno del archivo .env
load_dotenv()

# Configuración de JWT sin valor por omisión
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "Falta JWT_SECRET_KEY en backend/.env. Genera una con:\n"
        "python -c \"import secrets; print(secrets.token_hex(32))\""
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas de sesión

# Configuración de hashing con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security_scheme = HTTPBearer()

def hash_password(password: str) -> str:
    """Genera un hash seguro bcrypt para la contraseña en texto plano."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña ingresada coincide con el hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Genera un token JWT firmado."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """Valida el token JWT enviado en el encabezado Authorization Header."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales o el token ha expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extraer sub y asegurarnos de que se convierta correctamente
        sub = payload.get("sub")
        rol: str = payload.get("rol")

        if sub is None or rol is None:
            raise credentials_exception

        # Convertir sub a int de forma segura
        usuario_id = int(sub)

        return {"id": usuario_id, "rol": rol, "email": payload.get("email")}

    except (JWTError, ValueError):
        raise credentials_exception

def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Verifica que el usuario autenticado tenga rol de administrador de RH."""
    if current_user.get("rol") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Se requieren permisos de administrador de RH."
        )
    return current_user


def exigir_mismo_usuario(current_user: dict, usuario_id: int) -> None:
    """
    Lanza un 403 Forbidden si el usuario autenticado no es 'admin'
    y su ID no coincide con el usuario_id solicitado.
    """
    if current_user.get("rol") != "admin" and int(current_user.get("id")) != int(usuario_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes ver datos de otro usuario."
        )