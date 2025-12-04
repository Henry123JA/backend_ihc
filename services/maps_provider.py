from core.config import settings
from services.maps_fake import fake_geocode, fake_directions
from services.maps_google import google_geocode, google_directions


def geocode(direccion):
    if settings.USE_FAKE_MAPS:
        return fake_geocode(direccion)
    return google_geocode(direccion)


def directions(origen, destino):
    if settings.USE_FAKE_MAPS:
        return fake_directions(origen, destino)
    return google_directions(origen, destino)
