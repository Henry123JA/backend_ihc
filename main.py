from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import Base, engine
from core.router import include_routers
import models.models as models
import os
from dotenv import load_dotenv
load_dotenv() 
# ===========================================
# 🧩 CREAR / REINICIAR TABLAS EN POSTGRESQL
# ===========================================
if os.getenv("DEBUG") == "True":
    print("⚠️ Reiniciando tablas (modo desarrollo)...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
else:
    print("✅ Verificando tablas existentes...")
    Base.metadata.create_all(bind=engine)

# ===========================================
# 🌱 CARGAR DATOS INICIALES (SEED)
# ===========================================
try:
    import seeds.seed_data as seed_data
    from database import SessionLocal

    db = SessionLocal()
    seed_data.insertar_datos_iniciales(db)
    db.close()
    print("🌱 Datos iniciales cargados correctamente.")
except Exception as e:
    print(f"⚠️ Error al insertar datos iniciales: {e}")

# ===========================================
# ⚙️ CONFIGURAR LA APLICACIÓN FASTAPI
# ===========================================
app = FastAPI(
    title="Sistema de Pedidos y Entregas",
    version="1.0",
    description="""
    Backend principal del Sistema de Pedidos y Entregas.
    Gestiona la comunicación entre el Bot de Telegram (cliente),
    la base de datos y la aplicación móvil de los conductores.
    """,
)
#app.mount("/assets", StaticFiles(directory="assets"), name="assets")
# ===========================================
# 🧭 SERVIR ARCHIVOS ESTÁTICOS
# ===========================================
app.mount("/public", StaticFiles(directory="public"), name="public")

include_routers(app)

@app.get("/", tags=["Estado del Servidor"])
def root():
    return {"status": "ok", "mensaje": "Backend funcionando correctamente 🚀"}
