# backend/routes/tracking.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime
from pydantic import BaseModel
from models.models import Conductor, Ubicacion
import os
from sqlalchemy import desc
from fastapi import Request

REST_LAT = float(os.getenv("RESTAURANTE_LAT"))
REST_LNG = float(os.getenv("RESTAURANTE_LNG"))
print("🌍 Restaurante ubicado en:", REST_LAT, REST_LNG)

router = APIRouter(prefix="/tracking", tags=["Tracking Conductores"])


# ======================================================
# 📦 DTO de entrada para registrar ubicación
# ======================================================
class UbicacionSchema(BaseModel):
    latitud: float
    longitud: float

@router.get("/restaurante")
def obtener_restaurante():
    return {
        "lat": REST_LAT,
        "lng": REST_LNG,
        "nombre": "Restaurante Central"
    }

# ======================================================
# 🔵 VER TODOS LOS CONDUCTORES (PARA MAPA Y PANEL)
# ======================================================
@router.get("/conductores")
def listar_conductores(db: Session = Depends(get_db)):
    conductores = db.query(Conductor).all()
    return [
        {
            "id": c.id,
            "nombre": c.nombre,
            "lat_actual": c.lat_actual,
            "lng_actual": c.lng_actual,
            "disponible": c.disponible
        }
        for c in conductores
    ]


# ======================================================
# 📍 ASIGNAR UBICACIÓN MANUAL + GUARDAR TRACKING HISTÓRICO
# ======================================================
@router.post("/{conductor_id}")
def asignar_ubicacion(conductor_id: int, data: UbicacionSchema, db: Session = Depends(get_db)):

    # 1️⃣ Validar conductor existente
    conductor = db.query(Conductor).filter(Conductor.id == conductor_id).first()
    if not conductor:
        raise HTTPException(404, detail="Conductor no encontrado")

    # 2️⃣ Registrar tracking (HISTORIAL)
    movimiento = Ubicacion(
        conductor_id=conductor_id,
        latitud=data.latitud,
        longitud=data.longitud,
        timestamp=datetime.utcnow()
    )
    db.add(movimiento)

    # 3️⃣ Actualizar coordenadas actuales
    conductor.lat_actual = data.latitud
    conductor.lng_actual = data.longitud

    db.commit()

    return {
        "status": "OK",
        "mensaje": f"Posición del conductor {conductor_id} actualizada",
        "lat": data.latitud,
        "lng": data.longitud,
        "timestamp": movimiento.timestamp
    }


# @router.get("/conductor/{conductor_id}")
# def obtener_ubicacion_conductor(conductor_id: int, db: Session = Depends(get_db)):


#     # último registro de ubicaciones (tracking)
#     ultima_ubicacion = (
#         db.query(Ubicacion)
#         .filter(Ubicacion.conductor_id == conductor_id)
#         .order_by(desc(Ubicacion.timestamp))   # ← SÚPER IMPORTANTE
#         .first()
#     )

#     if not ultima_ubicacion:
#         raise HTTPException(404, "No hay ubicaciones registradas para este conductor")

#     return {
#         "id": conductor_id,
#         "lat": ultima_ubicacion.latitud,
#         "lng": ultima_ubicacion.longitud,
#         "timestamp": ultima_ubicacion.timestamp
#     }

from fastapi import Request

@router.get("/conductor/{conductor_id}")
def obtener_ubicacion_conductor(
    conductor_id: int,
    request: Request,
    db: Session = Depends(get_db)
):

    # 🛡 1) Validar que el ID sea válido
    if conductor_id is None or str(conductor_id) == "undefined":
        print(f"🚫 ID inválido desde {request.client.host} -> conductor_id={conductor_id}")
        raise HTTPException(status_code=400, detail="ID de conductor inválido")

    # 🕵️ 2) Log de request válida
    print(f"📥 Request válida -> {request.client.host} | ID={conductor_id}")

    # 📌 3) Obtener última ubicación registrada
    ultima_ubicacion = (
        db.query(Ubicacion)
        .filter(Ubicacion.conductor_id == conductor_id)
        .order_by(desc(Ubicacion.timestamp))
        .first()
    )

    # ⚠ 4) Si no tiene tracking registrado
    if not ultima_ubicacion:
        print(f"⚠ Sin ubicación previa para conductor {conductor_id}")
        raise HTTPException(status_code=404, detail="No hay ubicaciones registradas")

    # 🚀 5) Respuesta final limpia
    return {
        "id": conductor_id,
        "lat": ultima_ubicacion.latitud,
        "lng": ultima_ubicacion.longitud,
        "timestamp": ultima_ubicacion.timestamp,
        "source_ip": request.client.host  # opcional, útil para debugging
    }











# @router.get("/conductor/{conductor_id}")
# def obtener_ubicacion_conductor(
#     conductor_id: int, 
#     request: Request, 
#     db: Session = Depends(get_db)
# ):

#     print(f"""
#     📥 PETICIÓN DETECTADA
#     🔹 IP: {request.client.host}
#     🔹 conductor_id: {conductor_id}
#     """)

#     # último registro de ubicaciones (tracking)
#     ultima_ubicacion = (
#         db.query(Ubicacion)
#         .filter(Ubicacion.conductor_id == conductor_id)
#         .order_by(desc(Ubicacion.timestamp))
#         .first()
#     )

#     if not ultima_ubicacion:
#         raise HTTPException(404, "No hay ubicaciones registradas para este conductor")

#     return {
#         "id": conductor_id,
#         "lat": ultima_ubicacion.latitud,
#         "lng": ultima_ubicacion.longitud,
#         "timestamp": ultima_ubicacion.timestamp
#     }









