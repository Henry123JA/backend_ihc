from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/bot", tags=["Bot"])

class Mensaje(BaseModel):
    telegram_user_id: int
    mensaje: str

@router.post("/mensaje")
def procesar_mensaje(data: Mensaje):

    texto = data.mensaje.lower()

    if texto == "📋 ver menú" or "menu" in texto:
        return {"respuesta": "Aquí tienes el menú del restaurante 🍽️"}

    if "hola" in texto:
        return {"respuesta": "¡Hola! ¿Qué deseas pedir?"}

    return {"respuesta": "No entiendo, intenta otra vez 😅"}
