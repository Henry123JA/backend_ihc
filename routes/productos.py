# backend/routes/productos.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models.models as models
from fastapi import HTTPException

router = APIRouter(prefix="/productos", tags=["Productos"])

# ====================================================
# 1. Listar MENÚ
# ====================================================
@router.get("/")
def listar_productos(db: Session = Depends(get_db)):
    productos = db.query(models.Producto).all()

    response = []

    for p in productos:
        response.append({
            "id": p.id,
            "nombre": p.nombre,
            "precio": p.precio,
            "descripcion": p.descripcion,
            "imagenes": [f"/assets/{img.archivo}" for img in p.imagenes]
        })

    return response

# ====================================================
# 2. Obtener producto por ID (opcional)
# ====================================================
@router.get("/{producto_id}")
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter_by(id=producto_id).first()
    if not producto:
        raise HTTPException(404, "Producto no encontrado")

    return {
        "id": producto.id,
        "nombre": producto.nombre,
        "precio": producto.precio,
        "descripcion": producto.descripcion,
        "imagenes": [f"/assets/{img.archivo}" for img in producto.imagenes]
    }
