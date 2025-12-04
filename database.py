# backend/database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ===============================
# 🔐 Cargar variables desde .env (solo local)
# ===============================
load_dotenv()

# ===============================
# 📌 Variables de entorno (DigitalOcean Dev DB)
# ===============================
DB_USER = os.getenv("PGUSER") or os.getenv("DB_USER")
DB_PASSWORD = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("PGHOST") or os.getenv("DB_HOST")
DB_PORT = os.getenv("PGPORT") or os.getenv("DB_PORT")
DB_NAME = os.getenv("PGDATABASE") or os.getenv("DB_NAME")

# ===============================
# 🧪 DEBUG (opcional)
# print(DB_USER, DB_HOST, DB_PORT)  # NO EN PRODUCCIÓN
# ===============================

# =====================================
# 💾 Construir la URL de conexión final
# =====================================
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# =====================================
# ⚙️ Crear motor y sesión
# =====================================
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
