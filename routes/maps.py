from fastapi import APIRouter
from services.maps_fake import fake_geocode, fake_directions

router = APIRouter(prefix="/maps", tags=["Maps Fake"])

# --------------------------
# 1) FAKE GEOCODING
# --------------------------
@router.get("/geocode")
def geocode(direccion: str):
    return fake_geocode(direccion)

# --------------------------
# 2) FAKE DIRECTIONS
# --------------------------
@router.get("/ruta")
def ruta(lat1: float, lng1: float, lat2: float, lng2: float):
    origen = {"lat": lat1, "lng": lng1}
    destino = {"lat": lat2, "lng": lng2}
    
    return fake_directions(origen, destino)
