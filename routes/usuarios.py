# 3erproyecto/backend/routes/usuarios.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models.models as models


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.get("/")
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(models.Usuario).all()

# ====================================================
# 📦 VER PEDIDOS DE UN USUARIO
# ====================================================
@router.get("/{usuario_id}/pedidos")
def pedidos_usuario(usuario_id: int, db: Session = Depends(get_db)):

    usuario = db.query(models.Usuario).filter_by(id=usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    pedidos = db.query(models.Pedido).filter_by(usuario_id=usuario_id).all()

    resultado = []

    for p in pedidos:

        # Obtener pago asociado
        pago = db.query(models.Pago).filter_by(pedido_id=p.id).first()
        estado_pago = pago.estado.value if pago else "pendiente"

        # Obtener detalles
        detalles = [
            {
                "producto": d.producto.nombre,
                "cantidad": d.cantidad,
                "subtotal": d.subtotal
            }
            for d in p.detalles
        ]

        resultado.append({
            "pedido_id": p.id,
            "estado": p.estado.value,
            "estado_pago": estado_pago,
            "total": p.total,
            "ubicacion_entrega": p.ubicacion_entrega,
            "fecha": p.fecha,
            "detalles": detalles
        })

    return resultado
