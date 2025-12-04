from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum


# ======================================================
# 🧩 ENUMS
# ======================================================

class EstadoPedido(enum.Enum):
    pendiente = "pendiente"      # Pedido creado pero SIN pagar
    aceptado = "aceptado"        # Conductor lo aceptó
    en_camino = "en_camino"      # Conductor yendo al cliente
    entregado = "entregado"      # Pedido finalizado
    cancelado = "cancelado"      # Pedido cancelado


class EstadoPago(enum.Enum):
    pendiente = "pendiente"
    confirmado = "confirmado"
    rechazado = "rechazado"


# ======================================================
# 👤 USUARIO (CLIENTE)
# ======================================================
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)

    # DATOS DE TELEGRAM
    telegram_user_id = Column(String(50), unique=True, index=True)
    username = Column(String(100))

    # DATOS OPCIONALES
    nombre = Column(String(100), nullable=True)
    direccion = Column(String(200), nullable=True)
    telefono = Column(String(20), nullable=True)

    pedidos = relationship("Pedido", back_populates="usuario")

# ======================================================
# 👤 CONDUCTOR
# ======================================================
class Conductor(Base):
    __tablename__ = "conductores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    telefono = Column(String(20))
    vehiculo = Column(String(100))
    disponible = Column(Integer, default=1)
    # 🔥 Ubicación actual del conductor
    lat_actual = Column(Float, nullable=True)
    lng_actual = Column(Float, nullable=True)
    # 🔗 Relación 1:N → un conductor puede tener varios pedidos
    pedidos = relationship("Pedido", back_populates="conductor")

    # 🔗 Relación opcional (si manejas tracking)
    ubicaciones = relationship("Ubicacion", back_populates="conductor")
    
# ======================================================
# 📍 UBICACIÓN (TRACKING)
# ======================================================
class Ubicacion(Base):
    __tablename__ = "ubicaciones"

    id = Column(Integer, primary_key=True, index=True)
    conductor_id = Column(Integer, ForeignKey("conductores.id"))
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    conductor = relationship("Conductor", back_populates="ubicaciones")

# ======================================================
# 🍕 PRODUCTO
# ======================================================
class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    precio = Column(Float, nullable=False)
    descripcion = Column(String(200), nullable=True)

    imagenes = relationship("ProductoImagen", back_populates="producto")
    

class ProductoImagen(Base):
    __tablename__ = "producto_imagenes"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    archivo = Column(String(255), nullable=False)   # nombre como "hamburger1.jpg"

    producto = relationship("Producto", back_populates="imagenes")

# ======================================================
# 📦 PEDIDO
# ======================================================
class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    total = Column(Float, nullable=False)
    estado = Column(Enum(EstadoPedido), default=EstadoPedido.pendiente)
    
    ubicacion_entrega = Column(String(200))

    # 🔥 Ubicación REAL del cliente (Telegram)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    # NUEVOS CAMPOS (se calculan al crear el pedido)
    distancia_km = Column(Float, nullable=True)      # Restaurante → Cliente
    costo_envio = Column(Float, nullable=True)       # Calculado 1 vez
    tiempo_estimado = Column(Integer, nullable=True) # ETA inicial en minutos

    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    conductor_id = Column(Integer, ForeignKey("conductores.id"))

    usuario = relationship("Usuario", back_populates="pedidos")
    conductor = relationship("Conductor", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido")
    pagos = relationship("Pago", back_populates="pedido")
    historial = relationship("HistorialEstado", back_populates="pedido")
    notificaciones = relationship("Notificacion", back_populates="pedido")


# ======================================================
# 🧾 DETALLE DE PEDIDO
# ======================================================
class DetallePedido(Base):
    __tablename__ = "detalles_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)

    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto")


# ======================================================
# 💳 PAGO
# ======================================================
class Pago(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    monto = Column(Float, nullable=False)
    metodo = Column(String(50), nullable=False)  # QR, Efectivo, Transferencia, etc.
    estado = Column(Enum(EstadoPago), default=EstadoPago.pendiente)  # 🔹 CORREGIDO
    fecha_pago = Column(DateTime, default=datetime.utcnow)

    pedido = relationship("Pedido", back_populates="pagos")



# ======================================================
# 🕒 HISTORIAL DE ESTADOS
# ======================================================
class HistorialEstado(Base):
    __tablename__ = "historial_estados"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    estado_anterior = Column(String(50))
    nuevo_estado = Column(String(50))
    fecha_cambio = Column(DateTime, default=datetime.utcnow)

    pedido = relationship("Pedido", back_populates="historial")


# ======================================================
# 🔔 NOTIFICACIÓN
# ======================================================
class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    mensaje = Column(String(200), nullable=False)
    tipo = Column(String(50), nullable=False)  # "cliente" o "conductor"
    fecha = Column(DateTime, default=datetime.utcnow)

    pedido = relationship("Pedido", back_populates="notificaciones")

# ======================================================
# 🚚 CONDUCTOR – ESTADO DEL PEDIDO (Control por conductor)
# ======================================================
class ConductorPedidoEstado(Base):
    __tablename__ = "conductor_pedido_estado"

    id = Column(Integer, primary_key=True)
    conductor_id = Column(Integer, ForeignKey("conductores.id"))
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))

    # Estado específico de este conductor respecto al pedido:
    # - "pendiente" → el conductor aún no respondió
    # - "aceptado" → este conductor tomó el pedido
    # - "rechazado" → el conductor lo descartó
    estado = Column(String(20))
    fecha = Column(DateTime, default=datetime.utcnow)


