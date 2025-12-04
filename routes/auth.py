from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from database import get_db
from models import models
from core.auth import crear_token, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Autenticación"])

class LoginTelegram(BaseModel):
    telegram_user_id: str
    username: str | None = None
    first_name: str | None = None

# ======================================
# 🚗 LOGIN CONDUCTOR → RETORNA TOKEN JWT
# ======================================
@router.post("/login_conductor")
def login_json(data: dict, db: Session = Depends(get_db)):
    """
    Versión más simple: recibe JSON {"email": "...", "password": "..."}.
    Útil para Postman o apps móviles sin OAuth2.
    """
    email = data.get("email")
    password = data.get("password")

    conductor = db.query(models.Conductor).filter_by(email=email).first()
    if not conductor or not verify_password(password, conductor.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = crear_token(data={"sub": str(conductor.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
        "conductor_id": conductor.id,
        "nombre": conductor.nombre,
        "mensaje": "Inicio de sesión exitoso 🚗"
    }

@router.post("/login_telegram_cliente")
def login_telegram(data: LoginTelegram, db: Session = Depends(get_db)):

    # Buscar usuario EXISTENTE por telegram_user_id
    usuario = db.query(models.Usuario).filter_by(
        telegram_user_id=data.telegram_user_id
    ).first()

    # Si no existe → crearlo automáticamente
    if not usuario:
        usuario = models.Usuario(
            telegram_user_id=data.telegram_user_id,
            username=data.username,
            nombre=data.first_name
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    return {
        "usuario_id": usuario.id,
        "nombre": usuario.nombre,
        "username": usuario.username,
        "mensaje": "Usuario validado vía Telegram"
    }