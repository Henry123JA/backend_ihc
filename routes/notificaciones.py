from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models.models as models

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


# ======================================================
# 📌 1. Obtener todas las notificaciones PARA EL CLIENTE
# ======================================================
@router.get("/cliente")
def obtener_notificaciones_cliente(db: Session = Depends(get_db)):

    notifs = (
        db.query(models.Notificacion)
        .filter(models.Notificacion.tipo == "cliente")
        .all()
    )

    resultado = []
    for n in notifs:
        usuario = (
            db.query(models.Usuario)
            .filter(models.Usuario.id == models.Pedido.usuario_id)
            .first()
        )

        if not usuario:
            continue

        resultado.append({
            "id": n.id,
            "mensaje": n.mensaje,
            "pedido_id": n.pedido_id,
            "chat_id": usuario.telegram_user_id
        })

    return resultado


# ======================================================
# 📌 2. Marcar notificación como leída
# ======================================================
@router.post("/marcar_leida/{notif_id}")
def marcar_leida(notif_id: int, db: Session = Depends(get_db)):

    notif = db.query(models.Notificacion).filter_by(id=notif_id).first()

    if not notif:
        raise HTTPException(404, "Notificación no encontrada")

    db.delete(notif)
    db.commit()

    return {"status": "OK", "id": notif_id}
