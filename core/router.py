# backend/core/router.py
from fastapi import FastAPI
from routes import productos, usuarios, conductores, pedidos, pagos, historial, ubicaciones, auth
from routes import notificaciones
from routes import maps
from routes import bot
from routes import tracking

def include_routers(app: FastAPI):
    app.include_router(productos.router)
    app.include_router(usuarios.router)
    app.include_router(conductores.router)
    app.include_router(pedidos.router)
    app.include_router(pagos.router)
    app.include_router(historial.router)
    app.include_router(ubicaciones.router)
    app.include_router(auth.router)  
    app.include_router(notificaciones.router)
    app.include_router(maps.router)
    app.include_router(bot.router)
    app.include_router(tracking.router)