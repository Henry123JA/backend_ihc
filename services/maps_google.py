import requests
from core.config import settings

def google_geocode(direccion):
    params = {
        "address": direccion,
        "key": settings.GOOGLE_API_KEY
    }
    r = requests.get(settings.GOOGLE_GEOCODE_URL, params=params).json()

    loc = r["results"][0]["geometry"]["location"]

    return {
        "direccion": r["results"][0]["formatted_address"],
        "lat": loc["lat"],
        "lng": loc["lng"],
        "fuente": "GOOGLE_GEOCODING"
    }


def google_directions(origen, destino):
    params = {
        "origin": f"{origen['lat']},{origen['lng']}",
        "destination": f"{destino['lat']},{destino['lng']}",
        "key": settings.GOOGLE_API_KEY
    }

    r = requests.get(settings.GOOGLE_DIRECTIONS_URL, params=params).json()
    leg = r["routes"][0]["legs"][0]

    return {
        "distancia_km": leg["distance"]["value"] / 1000,
        "tiempo_min": leg["duration"]["value"] / 60,
        "ruta": leg["steps"],
        "fuente": "GOOGLE_DIRECTIONS"
    }
