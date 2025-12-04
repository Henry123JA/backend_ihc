from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import get_db
from models import models

# ==============================
# 🔐 CONFIGURACIÓN JWT
# ==============================
SECRET_KEY = "super_secret_key_cambia_esto"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login_conductor")


# ==============================
# 🔑 FUNCIONES DE PASSWORD
# ==============================
def hash_password(password: str):
    """Cifra la contraseña en formato bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    """Verifica una contraseña con su hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ==============================
# 📦 CREAR TOKEN
# ==============================
def crear_token(data: dict, expires_delta: timedelta | None = None):
    """Genera un token JWT con expiración."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ==============================
# ✅ VERIFICAR TOKEN
# ==============================
def verificar_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Verifica y decodifica el token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        conductor_id: int = payload.get("sub")
        if conductor_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expirado o inválido")

    conductor = db.query(models.Conductor).filter(models.Conductor.id == conductor_id).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")

    return conductor
