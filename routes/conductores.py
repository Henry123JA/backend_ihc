# backend/routes/conductores.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models.models as models
from datetime import datetime
from pydantic import BaseModel
router = APIRouter(prefix="/conductores", tags=["Conductores"])


# ======================================================
# 📌 1. Listar conductores
# ======================================================
@router.get("/")
def listar_conductores(db: Session = Depends(get_db)):
    return db.query(models.Conductor).all()



# ======================================================
# 📌 2. Cambiar estado del conductor (disponible / no disponible)
# ======================================================
@router.put("/{conductor_id}/estado")
def actualizar_estado_conductor(conductor_id: int, disponible: int, db: Session = Depends(get_db)):

    conductor = db.query(models.Conductor).filter_by(id=conductor_id).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")

    conductor.disponible = disponible
    db.commit()

    estado_texto = "disponible" if disponible == 1 else "no disponible"
    return {"mensaje": f"Estado del conductor actualizado a {estado_texto}"}



# ======================================================
# 📌 3. Ver pedidos pendientes para este conductor
# ======================================================
@router.get("/{conductor_id}/notificaciones")
def notificaciones_conductor(conductor_id: int, db: Session = Depends(get_db)):

    # Buscar SOLO pedidos que:
    # - fueron enviados a este conductor
    # - aún están marcados como pendientes para él
    pendientes = (
        db.query(models.ConductorPedidoEstado)
        .filter_by(conductor_id=conductor_id, estado="pendiente")
        .all()
    )

    resultado = []

    for rel in pendientes:
        pedido = db.query(models.Pedido).filter_by(id=rel.pedido_id).first()
        if not pedido:
            continue

        # ❌ Si el pedido YA NO está pendiente globalmente → NO enviar
        if pedido.estado != models.EstadoPedido.pendiente:
            continue

        resultado.append({
            "id": pedido.id,
            "cliente": pedido.usuario.nombre if pedido.usuario else "Cliente",
            "direccion": pedido.ubicacion_entrega,
        })

    return resultado


# ======================================================
# 📌 4. Conductor ACEPTA un pedido
# ======================================================
@router.post("/{conductor_id}/aceptar_pedido/{pedido_id}")
def aceptar_pedido(conductor_id: int, pedido_id: int, db: Session = Depends(get_db)):

    pedido = db.query(models.Pedido).filter_by(id=pedido_id).first()
    if not pedido:
        raise HTTPException(404, "Pedido no encontrado")

    # Si ya no está pendiente → otro conductor lo tomó
    if pedido.estado != models.EstadoPedido.pendiente:
        raise HTTPException(400, "El pedido ya fue aceptado por otro conductor")

    # 1) Asignar conductor
    pedido.conductor_id = conductor_id
    pedido.estado = models.EstadoPedido.aceptado  # ← CORRECTO

    # 2) Cambiar estado del conductor seleccionado
    rel = db.query(models.ConductorPedidoEstado).filter_by(
        conductor_id=conductor_id,
        pedido_id=pedido_id
    ).first()
    if rel:
        rel.estado = "aceptado"

    # 3) Rechazar al resto
    otros = db.query(models.ConductorPedidoEstado).filter(
        models.ConductorPedidoEstado.pedido_id == pedido_id,
        models.ConductorPedidoEstado.conductor_id != conductor_id,
        models.ConductorPedidoEstado.estado == "pendiente"
    ).all()

    for o in otros:
        o.estado = "rechazado"

    # 4) Registrar historial
    historial = models.HistorialEstado(
        pedido_id=pedido_id,
        estado_anterior="pendiente",
        nuevo_estado="aceptado"
    )
    db.add(historial) 

    # 5) Notificación al cliente
    notif = models.Notificacion(
        pedido_id=pedido_id,
        mensaje=f"Tu pedido #{pedido_id} fue aceptado por un conductor",
        tipo="cliente"
    )
    db.add(notif)

    db.commit()

    return {
        "mensaje": "Pedido aceptado correctamente",
        "pedido_id": pedido_id
    }


# ======================================================
# 📌 5. Conductor RECHAZA un pedido
# ======================================================
@router.post("/{conductor_id}/rechazar_pedido/{pedido_id}")
def rechazar_pedido(conductor_id: int, pedido_id: int, db: Session = Depends(get_db)):

    relacion = db.query(models.ConductorPedidoEstado).filter_by(
        conductor_id=conductor_id,
        pedido_id=pedido_id
    ).first()

    if not relacion:
        raise HTTPException(status_code=404, detail="Este pedido no fue enviado a este conductor")

    # Si ya está aceptado por otro → NO HACEMOS NADA
    pedido = db.query(models.Pedido).filter_by(id=pedido_id).first()
    if pedido.estado != models.EstadoPedido.pendiente:
        relacion.estado = "rechazado"
        db.commit()
        return {"mensaje": "El pedido ya fue tomado por otro conductor"}

    # Rechazar
    relacion.estado = "rechazado"
    db.commit()

    return {"mensaje": "Pedido rechazado", "pedido_id": pedido_id}

# ======================================================
# 📌 6. Conductor CANCELA su aceptación (liberar pedido)
# ======================================================
@router.post("/{conductor_id}/cancelar_pedido/{pedido_id}")
def cancelar_pedido(conductor_id: int, pedido_id: int, db: Session = Depends(get_db)):

    pedido = db.query(models.Pedido).filter_by(id=pedido_id).first()
    if not pedido:
        raise HTTPException(404, "Pedido no encontrado")

    # Solo puede cancelar si *él mismo* lo aceptó
    if pedido.conductor_id != conductor_id:
        raise HTTPException(403, "No puedes cancelar un pedido que no aceptaste")

    # Solo si estaba aceptado o en camnio
    if pedido.estado not in [models.EstadoPedido.aceptado, models.EstadoPedido.en_camino]:
        raise HTTPException(400, "El pedido no puede ser cancelado en este estado")

    # 🔥 1) Liberar el pedido para que OTRO lo tome
    pedido.conductor_id = None
    pedido.estado = models.EstadoPedido.pendiente

    # 🔥 2) Marcar SOLO a este conductor como rechazado
    rel = db.query(models.ConductorPedidoEstado).filter_by(
        conductor_id=conductor_id,
        pedido_id=pedido_id
    ).first()

    if rel:
        rel.estado = "rechazado"

    # 🔥 3) REACTIVAR A LOS DEMÁS conductores
    otros = db.query(models.ConductorPedidoEstado).filter(
        models.ConductorPedidoEstado.pedido_id == pedido_id,
        models.ConductorPedidoEstado.conductor_id != conductor_id
    ).all()

    for o in otros:
        o.estado = "pendiente"   # ← quedan disponibles nuevamente

    # 🔥 4) Registrar historial
    historial = models.HistorialEstado(
        pedido_id=pedido_id,
        estado_anterior="aceptado",
        nuevo_estado="pendiente"
    )
    db.add(historial)

    # 🔥 5) Notificar al cliente
    notif = models.Notificacion(
        pedido_id=pedido_id,
        mensaje=f"El conductor canceló la entrega. Estamos asignando otro conductor.",
        tipo="cliente"
    )
    db.add(notif)

    db.commit()

    return {
        "mensaje": "El pedido fue liberado correctamente",
        "pedido_id": pedido_id
    }

 
# ======================================================
# 📌 7. Conductor INICIA RUTA (ACEPTA → EN_CAMINO)
# ======================================================
@router.post("/{conductor_id}/iniciar_ruta/{pedido_id}")
def iniciar_ruta(conductor_id: int, pedido_id: int, db: Session = Depends(get_db)):

    print("\n================ DEBUG INICIAR RUTA ================")
    print(f"📥 Datos recibidos → conductor_id: {conductor_id}, pedido_id: {pedido_id}")

    pedido = db.query(models.Pedido).filter_by(id=pedido_id).first()

    if not pedido:
        print("❌ Pedido no existe en BD")
        raise HTTPException(404, "Pedido no encontrado")

    print(f"🔎 Pedido encontrado. Estado actual: {pedido.estado.value}, asignado a conductor: {pedido.conductor_id}")

    if pedido.conductor_id != conductor_id:
        print(f"🚨 Error: El pedido pertenece a {pedido.conductor_id} no a {conductor_id}")
        raise HTTPException(403, "No tienes permiso para iniciar este pedido")

    if pedido.estado != models.EstadoPedido.aceptado:
        print(f"⚠ Pedido no está aceptado, está en {pedido.estado.value}")
        raise HTTPException(400, "El pedido debe estar aceptado para iniciar la ruta")

    estado_anterior = pedido.estado.value
    print(f"🟡 Cambiando estado → {estado_anterior} → en_camino")

    pedido.estado = models.EstadoPedido.en_camino

    historial = models.HistorialEstado(
        pedido_id=pedido_id,
        estado_anterior=estado_anterior,
        nuevo_estado=models.EstadoPedido.en_camino.value
    )
    db.add(historial)

    notif = models.Notificacion(
        pedido_id=pedido_id,
        mensaje=f"🚗 Tu pedido #{pedido_id} HA SIDO RECOGIDO 🛵",
        tipo="cliente"
    )
    db.add(notif)

    db.commit()
    db.refresh(pedido)

    print(f"💾 Estado guardado correctamente → {pedido.estado.value}")
    print("=====================================================\n")

    return {
        "mensaje": "Ruta iniciada correctamente",
        "pedido_id": pedido_id,
        "nuevo_estado": pedido.estado.value
    }


# ======================================================
# 📌 8. ENTREGAR PEDIDO (Conductor confirma entrega)
# ======================================================
@router.post("/{conductor_id}/entregar_pedido/{pedido_id}")
def entregar_pedido(conductor_id: int, pedido_id: int, db: Session = Depends(get_db)):

    pedido = db.query(models.Pedido).filter_by(id=pedido_id).first()
    if not pedido:
        raise HTTPException(404, "Pedido no encontrado")

    if pedido.conductor_id != conductor_id:
        raise HTTPException(403, "No tienes permiso para finalizar este pedido")

    # 🚨 Validación importante:
    if pedido.estado != models.EstadoPedido.en_camino:
        raise HTTPException(400, "El pedido debe estar EN CAMINO para entregarse")

    estado_anterior = pedido.estado.value
    pedido.estado = models.EstadoPedido.entregado   # 💥 Nuevo estado

    # Guardar historial
    historial = models.HistorialEstado(
        pedido_id=pedido_id,
        estado_anterior=estado_anterior,
        nuevo_estado=models.EstadoPedido.entregado.value
    )
    db.add(historial)

    # Notificar al cliente
    notif = models.Notificacion(
        pedido_id=pedido_id,
        mensaje=f"📦 Pedido #{pedido_id} ha sido ENTREGADO con éxito.",
        tipo="cliente"
    )
    db.add(notif)

    db.commit()
    db.refresh(pedido)

    return {
        "mensaje": "Pedido marcado como ENTREGADO",
        "pedido_id": pedido_id,
        "nuevo_estado": pedido.estado.value
    }



class Ubicacion(BaseModel):
    lat: float
    lng: float

@router.put("/{conductor_id}/ubicacion_conductor")
def actualizar_ubicacion_conductor(
    conductor_id: int,
    ubicacion: Ubicacion,
    db: Session = Depends(get_db)
):

    conductor = db.query(models.Conductor).filter_by(id=conductor_id).first()

    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")

    conductor.lat_actual = ubicacion.lat
    conductor.lng_actual = ubicacion.lng
    db.commit()

    return {"mensaje": "Ubicación actualizada"}

