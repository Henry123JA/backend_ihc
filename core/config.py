from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # ============================
    # 📌 BASE DE DATOS (DigitalOcean Dev DB)
    # ============================
    DB_USER: str = Field(..., env="PGUSER")
    DB_PASSWORD: str = Field(..., env="PGPASSWORD")
    DB_HOST: str = Field(..., env="PGHOST")
    DB_PORT: int = Field(..., env="PGPORT")
    DB_NAME: str = Field(..., env="PGDATABASE")

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
