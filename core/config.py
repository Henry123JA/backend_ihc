# core/config.py
import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ============================
    # 📌 BASE DE DATOS
    # ============================
    # DigitalOcean Dev DB variables
    DB_USER: str = Field(default=None, env="PGUSER")
    DB_PASSWORD: str = Field(default=None, env="PGPASSWORD")
    DB_HOST: str = Field(default=None, env="PGHOST")
    DB_PORT: int = Field(default=None, env="PGPORT")
    DB_NAME: str = Field(default=None, env="PGDATABASE")

    # ============================
    # 🔐 CONFIGURACIONES DE SEGURIDAD
    # ============================
    SECRET_KEY: str = Field(..., env="SECRET_KEY")

    # ============================
    # ⚙️ ENTORNO
    # ============================
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")

    # ============================
    # 🗺️ GOOGLE MAPS / FAKE MAPS
    # ============================
    USE_FAKE_MAPS: bool = Field(True, env="USE_FAKE_MAPS")
    GOOGLE_API_KEY: str = Field("", env="GOOGLE_API_KEY")

    GOOGLE_GEOCODE_URL: str = Field(
        "https://maps.googleapis.com/maps/api/geocode/json",
        env="GOOGLE_GEOCODE_URL"
    )
    GOOGLE_DIRECTIONS_URL: str = Field(
        "https://maps.googleapis.com/maps/api/directions/json",
        env="GOOGLE_DIRECTIONS_URL"
    )

    # ============================
    # 🟢 UBICACIÓN FIJA DEL RESTAURANTE
    # ============================
    restaurante_lat: float = Field(..., env="RESTAURANTE_LAT")
    restaurante_lng: float = Field(..., env="RESTAURANTE_LNG")

    # ============================
    # ⚙️ CONFIG LOCAL .env
    # ============================
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# ============================
# 🔄 FALLBACK PARA LOCAL
# Si estamos en local y PG* no existe, usar DB_*
# ============================
settings = Settings()

if settings.DB_USER is None:
    settings.DB_USER = os.getenv("DB_USER")
    settings.DB_PASSWORD = os.getenv("DB_PASSWORD")
    settings.DB_HOST = os.getenv("DB_HOST")
    settings.DB_PORT = int(os.getenv("DB_PORT"))
    settings.DB_NAME = os.getenv("DB_NAME")
