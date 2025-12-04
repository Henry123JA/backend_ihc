# backend/utils/geolocalizacion.py

import requests
import math

def obtener_direccion(lat, lng):
    """
    Convierte coordenadas a una dirección de texto usando Nominatim (OpenStreetMap).
    GRATIS – No requiere API Key.
    """
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
    headers = {"User-Agent": "MiApp/1.0"}

    try:
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        return data.get("display_name", "Dirección no disponible")

    except Exception:
        return "Dirección no disponible"

def calcular_distancia_km(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros usando la fórmula Haversine.
    """
    R = 6371  # Radio de la Tierra en km

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    distancia = R * c
    return round(distancia, 3)

def calcular_eta_minutos(distancia_km, velocidad_kmh=30):
    """
    Calcula el tiempo estimado de llegada en minutos.
    - velocidad_kmh: velocidad promedio (30 km/h para moto)
    """
    if velocidad_kmh <= 0:
        velocidad_kmh = 30

    tiempo_horas = distancia_km / velocidad_kmh
    tiempo_min = tiempo_horas * 60
    return max(1, round(tiempo_min))  # Nunca menos de 1 minuto
