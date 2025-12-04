import time
from sqlalchemy.orm import Session
import models.models as models

TIEMPO_ESPERA = 25  # segundos

# def asignar_cascada(pedido_id, lista, db: Session):

#     for item in lista:
#         c = item["conductor"]

#         # Asignar a este conductor
#         db.add(models.ConductorPedidoEstado(
#             conductor_id=c.id,
#             pedido_id=pedido_id,
#             estado="pendiente"
#         ))
#         db.commit()

#         # 🔔 Notificación
#         db.add(models.Notificacion(
#             pedido_id=pedido_id,
#             mensaje=f"📍 Nuevo pedido #{pedido_id} disponible ({item['distancia']:.1f} km)",
#             tipo="conductor"
#         ))
#         db.commit()

#         print(f"⏳ Esperando respuesta conductor {c.id}...")
#         time.sleep(TIEMPO_ESPERA)

#         estado = db.query(models.ConductorPedidoEstado)\
#             .filter_by(conductor_id=c.id, pedido_id=pedido_id).first()

#         if estado.estado == "aceptado":
#             print("🟢 Pedido aceptado -> FIN")
#             return True

#         # no respondió → pasamos al siguiente
#         estado.estado = "rechazado"
#         db.commit()

#     print("⚠ Ningún conductor aceptó → vuelve a pendiente")
#     return False
def asignar_cascada(pedido_id, lista, db: Session):

    for item in lista:
        c = item["conductor"]

        # Verificar si ya se notificó antes al mismo conductor
        existe = db.query(models.ConductorPedidoEstado).filter_by(
            conductor_id=c.id, 
            pedido_id=pedido_id
        ).first()

        if existe:
            print(f"⛔ Conductor {c.id} ya fue notificado antes, siguiente...")
            continue

        # 1️⃣ Crear estado + notificación SOLO PARA EL ACTUAL
        estado = models.ConductorPedidoEstado(
            conductor_id=c.id,
            pedido_id=pedido_id,
            estado="pendiente"
        )

        notif = models.Notificacion(
            pedido_id=pedido_id,
            mensaje=f"📍 Nuevo pedido #{pedido_id} a {item['distancia']:.1f} km",
            tipo="conductor"
        )

        db.add_all([estado, notif])
        db.commit()
        print(f"📨 Notificado conductor {c.id} (dist {item['distancia']:.1f} km)")

        # 2️⃣ Esperar respuesta ⏳
        time.sleep(TIEMPO_ESPERA)

        estado = db.query(models.ConductorPedidoEstado).filter_by(
            conductor_id=c.id,
            pedido_id=pedido_id
        ).first()

        if estado.estado == "aceptado":
            print("🟢 Pedido aceptado por ", c.id)
            return True

        # 3️⃣ Si no respondió → rechazar y pasar al siguiente
        estado.estado = "rechazado"
        db.commit()
        print(f"❌ Conductor {c.id} no aceptó. Probando siguiente...")

    print("⚠ Ninguno aceptó → pedido vuelve a tienda.")
    return False
