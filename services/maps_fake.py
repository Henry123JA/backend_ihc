# backend/services/maps_fake.py

import random
import math

# Santa Cruz como centro (para fake)
SC_LAT = -17.7833
SC_LNG = -63.1821

# ------------------------------------
# Generar coordenadas falsas cercanas
# ------------------------------------
def fake_geocode(direccion: str):
    """Simula conversión de dirección → coordenadas (lat, lng)"""
    lat = SC_LAT + random.uniform(-0.02, 0.02)
    lng = SC_LNG + random.uniform(-0.02, 0.02)

    return {
        "direccion": direccion,
        "lat": lat,
        "lng": lng,
        "fuente": "FAKE_GEOCODER"
    }

# ------------------------------------
# Distancia Haversine (real)
# ------------------------------------
def calcular_distancia(lat1, lng1, lat2, lng2):
    """Cálculo real de distancia sin Google"""
    R = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlng/2)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c  # distancia en km

# ------------------------------------
# Fake Directions
# ------------------------------------
def fake_directions(origen, destino):
    """Simula ruta Google Maps"""
    dist = calcular_distancia(
        origen["lat"], origen["lng"], destino["lat"], destino["lng"]
    )

    # tiempo promedio 30 km/h
    tiempo = (dist / 30) * 60  # minutos

    return {
        "distancia_km": round(dist, 2),
        "tiempo_min": round(tiempo, 1),
        "ruta": [
            {"lat": origen["lat"], "lng": origen["lng"]},
            {"lat": destino["lat"], "lng": destino["lng"]}
        ],
        "fuente": "FAKE_DIRECTIONS"
    }
