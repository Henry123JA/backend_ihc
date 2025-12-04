from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from utils.geolocalizacion import obtener_direccion
from services.maps_provider import geocode
import requests
import models.models as models
from dotenv import load_dotenv
import os
from services.asignacion_cascada import asignar_cascada
load_dotenv()

RESTAURANTE_LAT = float(os.getenv("RESTAURANTE_LAT"))
RESTAURANTE_LNG = float(os.getenv("RESTAURANTE_LNG"))
from math import radians, sin, cos, sqrt, atan2

def distancia_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1-a))



router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


# ====================================================
# 🧾0) Listar pedidos
# ====================================================
@router.get("/")
def listar_pedidos(db: Session = Depends(get_db)):
    return db.query(models.Pedido).all()

 
@router.post("/calcular_costos")
def calcular_costos_pedido(payload: dict, db: Session = Depends(get_db)):

    items = payload.get("items", [])
    ubicacion = payload.get("ubicacion")

    if not items:
        raise HTTPException(400, "items no puede estar vacío")

    if not ubicacion:
        raise HTTPException(400, "ubicacion es requerida")

    lat = ubicacion["lat"]
    lng = ubicacion["lng"]

    # 1) Calcular total de productos
    total_productos = 0
    for item in items:
        producto = db.query(models.Producto).filter_by(id=item["producto_id"]).first()
        if not producto:
            raise HTTPException(404, f"Producto {item['producto_id']} no existe")

        total_productos += producto.precio * item["cantidad"]

    # 2) Calcular distancia, envío y ETA
    from core.config import settings
    from utils.geolocalizacion import calcular_distancia_km, calcular_eta_minutos

    REST_LAT = settings.restaurante_lat
    REST_LNG = settings.restaurante_lng

    distancia_km = calcular_distancia_km(REST_LAT, REST_LNG, lat, lng)
    costo_envio = round(5 + distancia_km * 1.5, 2)
    tiempo_estimado = calcular_eta_minutos(distancia_km)

    # 3) Convertir ubicación a texto
    direccion_texto = obtener_direccion(lat, lng)

    return {
        "total_productos": total_productos,
        "costo_envio": costo_envio,
        "total_final": total_productos + costo_envio,
        "direccion": direccion_texto,
        "distancia_km": distancia_km,
        "tiempo_estimado_min": tiempo_estimado
    }


@router.post("/crear_pedido")
def crear_pedido(payload: dict, db: Session = Depends(get_db)):

    print(">>> Payload crear_pedido:", payload)
    usuario_id = payload.get("usuario_id")
    items = payload.get("items", [])
    ubicacion = payload.get("ubicacion_entrega")

    total_productos = payload.get("total_productos")
    costo_envio = payload.get("costo_envio")
    total_final = payload.get("total_final")
    distancia_km = payload.get("distancia_km")
    tiempo_estimado = payload.get("tiempo_estimado_min")
    direccion_texto = payload.get("direccion")

    # 1) Validación
    if not usuario_id:
        raise HTTPException(400, "usuario_id es requerido")

    if not items:
        raise HTTPException(400, "items no puede estar vacío")

    if not ubicacion:
        raise HTTPException(400, "ubicacion_entrega es requerida")

    lat = ubicacion["lat"]
    lng = ubicacion["lng"]

    usuario = db.query(models.Usuario).filter_by(id=usuario_id).first()
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado")

    # 2) Crear pedido
    pedido = models.Pedido(
        usuario_id=usuario_id,
        total=total_final,
        estado=models.EstadoPedido.pendiente,
        ubicacion_entrega=direccion_texto,
        lat=lat,
        lng=lng,
        distancia_km=distancia_km,
        costo_envio=costo_envio,
        tiempo_estimado=tiempo_estimado,
        fecha=datetime.utcnow()
    )

    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    # 3) Crear detalles
    for item in items:
        producto = db.query(models.Producto).filter_by(id=item["producto_id"]).first()
        subtotal = producto.precio * item["cantidad"]

        det = models.DetallePedido(
            pedido_id=pedido.id,
            producto_id=item["producto_id"],
            cantidad=item["cantidad"],
            subtotal=subtotal
        )
        db.add(det)

    # 4) Crear pago pendiente
    pago = models.Pago(
        pedido_id=pedido.id,
        monto=total_final,
        metodo="qr",
        estado=models.EstadoPago.pendiente
    )

    db.add(pago)
    db.commit()

    return {
        "mensaje": "Pedido creado exitosamente",
        "pedido_id": pedido.id
    }


# ====================================================
# 4. Generar QR para pago
# ====================================================
@router.get("/{pedido_id}/qr")
def obtener_qr_pago(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.query(models.Pedido).filter_by(id=pedido_id).first()
    if not pedido:
        raise HTTPException(404, "Pedido no encontrado")

    # Aquí puedes generar un QR real, pero por ahora devuelve un link de ejemplo
    return {
        "qr_url": f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=pedido_{pedido_id}"
    }



# ====================================================
# 5. Confirmar pago (pago QR aceptado)
# ====================================================
@router.post("/{pedido_id}/confirmar_pago")
def confirmar_pago(pedido_id: int, db: Session = Depends(get_db)):

    pago = db.query(models.Pago).filter_by(pedido_id=pedido_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    pedido = db.query(models.Pedido).filter_by(id=pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    # Cambiar el estado del pago
    pago.estado = models.EstadoPago.confirmado

    # El pedido está pagado pero NO tiene conductor
    pedido.estado = models.EstadoPedido.pendiente

    # Registrar historial
    historial = models.HistorialEstado(
        pedido_id=pedido_id,
        estado_anterior="pendiente_pago",
        nuevo_estado="pago_confirmado"
    )
    db.add(historial)

    # # ============================
    # # 📢 Notificar A CADA CONDUCTOR
    # # ============================
    # conductores = db.query(models.Conductor).filter_by(disponible=1).all()

    # for c in conductores:

    #     # Crear notificación
    #     notif = models.Notificacion(
    #         pedido_id=pedido.id,
    #         mensaje=f"Nuevo pedido #{pedido.id} disponible",
    #         tipo="conductor"
    #     )
    #     db.add(notif)

    #     # 🔥 Registrar estado individual del conductor en este pedido
    #     estado = models.ConductorPedidoEstado(
    #         conductor_id=c.id,
    #         pedido_id=pedido.id,
    #         estado="pendiente"  # todavía no aceptó/rechazó
    #     )
    #     db.add(estado)

    # db.commit()

    # return {"mensaje": "Pago confirmado y notificado a conductores", "pedido_id": pedido_id}
    # ============================
    # 📢 Notificar A CONDUCTORES POR DISTANCIA
    # ============================

    conductores = db.query(models.Conductor).filter_by(disponible=1).all()

    conductores_dist = []

    for c in conductores:
        if c.lat_actual and c.lng_actual:
            dist = distancia_km(RESTAURANTE_LAT, RESTAURANTE_LNG, c.lat_actual, c.lng_actual)
        else:
            dist = 9999  # sin GPS → último de la lista

        conductores_dist.append({"conductor": c, "distancia": dist})

    # 🔥 ordenar → más cerca primero
    conductores_dist.sort(key=lambda x: x["distancia"])

    # # 🚨 Notificar SOLO 1 conductor más cercano
    # for item in conductores_dist[:1]:
    #     c = item["conductor"]

    #     notif = models.Notificacion(
    #         pedido_id=pedido.id,
    #         mensaje=f"📍 Nuevo pedido #{pedido.id} a {item['distancia']:.2f} km del restaurante",
    #         tipo="conductor"
    #     )
    #     db.add(notif)

    #     estado = models.ConductorPedidoEstado(
    #         conductor_id=c.id,
    #         pedido_id=pedido.id,
    #         estado="pendiente"
    #     )
    #     db.add(estado)

    # db.commit()
    # return {"mensaje": "Pago confirmado y notificado al conductor más cercano"}
# Ejecutar asignación en cascada
    resultado = asignar_cascada(pedido.id, conductores_dist, db)

    if resultado:
        return {"mensaje": "Conductor asignado con éxito"}
    else:
        pedido.estado = models.EstadoPedido.pendiente
        db.commit()
        return {"mensaje": "Ningún conductor aceptó. Pedido devuelto a la tienda."}







# ====================================================
# 6. Pago rechazado
# ====================================================
@router.post("/{pedido_id}/pago_rechazado")
def pago_rechazado(pedido_id: int, db: Session = Depends(get_db)):

    pago = db.query(models.Pago).filter_by(pedido_id=pedido_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    pedido = db.query(models.Pedido).filter_by(id=pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    pago.estado = models.EstadoPago.rechazado
    pedido.estado = models.EstadoPedido.cancelado

    historial = models.HistorialEstado(
        pedido_id=pedido_id,
        estado_anterior="pendiente_pago",
        nuevo_estado="pago_rechazado"
    )
    db.add(historial)

    db.commit()

    return {"mensaje": "Pago rechazado, pedido cancelado", "pedido_id": pedido_id}


# ====================================================
# 7. Obtener detalle completo del pedido
# ====================================================
@router.get("/{pedido_id}/detalle_completo")
def obtener_detalle_completo(pedido_id: int, db: Session = Depends(get_db)):

    pedido = db.query(models.Pedido).filter_by(id=pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    usuario = pedido.usuario  # relación
    detalles = pedido.detalles  # relación

    # Convertir productos
    items = []
    for d in detalles:
        items.append({
            "producto": d.producto.nombre,
            "cantidad": d.cantidad,
            "subtotal": d.subtotal
        })

    # ===== COORDENADAS (IMPORTANTE) =====
    # Si NO tienes lat/lng en BD, luego lo agrego.
    lat = pedido.latitud if hasattr(pedido, "latitud") else None
    lng = pedido.longitud if hasattr(pedido, "longitud") else None

    # =======================
    # OBJETO COMPLETO
    # =======================
    respuesta = {
        "id": pedido.id,
        "estado": pedido.estado.value,
        "direccion": pedido.ubicacion_entrega,
        "lat": lat,
        "lng": lng,
        "total": pedido.total,

        "cliente": usuario.nombre if usuario else "Cliente",
        "telefono": usuario.telefono if usuario else "",

        "detalles": items,
    }

    return respuesta
