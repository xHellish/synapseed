from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditAction
from app.repositories import AuditRepository, ZoneRepository

router = APIRouter(prefix="/zones", tags=["zones"])


# Tablas de equivalencia: el frontend usa nombres/rangos, la DB guarda numeros (lat/lon, %, °C).
# Estos diccionarios traducen en ambos sentidos.
COORDINATES_TO_LOCATION = {
    (9.86, -83.92): "Cartago, Costa Rica",
    (10.02, -84.21): "Alajuela, Costa Rica",
    (10.00, -84.12): "Heredia, Costa Rica",
    (9.93, -84.09): "San José, Costa Rica",
    (10.60, -85.40): "Guanacaste, Costa Rica",
    (9.98, -84.83): "Puntarenas, Costa Rica",
    (10.00, -83.03): "Limón, Costa Rica",
}

HUMIDITY_STR_TO_VAL = {
    "muy baja": 20.0,
    "baja": 40.0,
    "media": 60.0,
    "alta": 80.0,
    "muy alta": 95.0,
}

TEMP_STR_TO_VAL = {
    "menos de 10°c": 8.0,
    "menos de 10c": 8.0,
    "10°c - 15°c": 12.5,
    "10c - 15c": 12.5,
    "15°c - 20°c": 17.5,
    "15c - 20c": 17.5,
    "20°c - 25°c": 22.5,
    "20c - 25c": 22.5,
    "25°c - 30°c": 27.5,
    "25c - 30c": 27.5,
    "más de 30°c": 35.0,
    "mas de 30c": 35.0,
}


# Nombre de provincia -> coordenadas aproximadas (para guardar lat/lon en la DB)
def map_location_to_coords(location_str: str | None) -> tuple[float | None, float | None]:
    if not location_str:
        return None, None
    loc_lower = location_str.lower()
    if "cartago" in loc_lower:
        return 9.86, -83.92
    if "alajuela" in loc_lower:
        return 10.02, -84.21
    if "heredia" in loc_lower:
        return 10.00, -84.12
    if "san josé" in loc_lower or "san jose" in loc_lower:
        return 9.93, -84.09
    if "guanacaste" in loc_lower:
        return 10.60, -85.40
    if "puntarenas" in loc_lower:
        return 9.98, -84.83
    if "limón" in loc_lower or "limon" in loc_lower:
        return 10.00, -83.03
    return 9.93, -84.09


# Coordenadas -> nombre de provincia mas cercana (para mostrar en el frontend)
def map_coords_to_location(lat: float | None, lon: float | None) -> str:
    if lat is None or lon is None:
        return "Costa Rica"
    closest_dist = float("inf")
    closest_name = "Costa Rica"
    # Distancia euclidiana simple: elige la provincia cuyo punto este mas cerca
    for (plat, plon), name in COORDINATES_TO_LOCATION.items():
        dist = (float(lat) - plat) ** 2 + (float(lon) - plon) ** 2
        if dist < closest_dist:
            closest_dist = dist
            closest_name = name
    if closest_dist < 0.05:
        return closest_name
    return f"Costa Rica ({float(lat):.4f}, {float(lon):.4f})"


# "Alta"/"Media"/... -> numero (%) para guardar; acepta tambien un numero directo
def map_humidity_to_val(hum_str: str | float | None) -> float | None:
    if hum_str is None:
        return None
    if isinstance(hum_str, (int, float)):
        return float(hum_str)
    try:
        return float(hum_str)
    except ValueError:
        pass
    cleaned = hum_str.lower().strip()
    return HUMIDITY_STR_TO_VAL.get(cleaned, None)


# Numero (%) -> etiqueta de humedad para mostrar al usuario
def map_val_to_humidity_str(hum_val: float | None) -> str:
    if hum_val is None:
        return "Media"
    val = float(hum_val)
    if val <= 30.0:
        return "Muy baja"
    if val <= 50.0:
        return "Baja"
    if val <= 70.0:
        return "Media"
    if val <= 90.0:
        return "Alta"
    return "Muy alta"


# Rango "20°C - 25°C" -> numero (punto medio) para guardar; tolera variantes sin °/espacios
def map_temp_to_val(temp_str: str | float | None) -> float | None:
    if temp_str is None:
        return None
    if isinstance(temp_str, (int, float)):
        return float(temp_str)
    try:
        return float(temp_str)
    except ValueError:
        pass
    cleaned = temp_str.lower().strip()
    if cleaned in TEMP_STR_TO_VAL:
        return TEMP_STR_TO_VAL[cleaned]
    cleaned_alt = cleaned.replace(" ", "")
    for key, val in TEMP_STR_TO_VAL.items():
        if key.replace(" ", "") == cleaned_alt:
            return val
    return None


# Numero (°C) -> etiqueta de rango de temperatura para mostrar al usuario
def map_val_to_temp_str(temp_val: float | None) -> str:
    if temp_val is None:
        return "20°C - 25°C"
    val = float(temp_val)
    if val < 10.0:
        return "Menos de 10°C"
    if val < 15.0:
        return "10°C - 15°C"
    if val < 20.0:
        return "15°C - 20°C"
    if val < 25.0:
        return "20°C - 25°C"
    if val < 30.0:
        return "25°C - 30°C"
    return "Más de 30°C"


def clean_payload(payload: dict) -> dict:
    """Prepara y limpia el payload recibido para evitar errores de ORM/Base de datos."""
    location_str = payload.pop("location", None)
    lat, lon = map_location_to_coords(location_str)

    cleaned = {}
    if "name" in payload:
        cleaned["name"] = payload["name"]
    if "soil_type" in payload:
        cleaned["soil_type"] = payload["soil_type"]
    if "water_quality" in payload:
        cleaned["water_quality"] = payload["water_quality"]

    # Coordenadas
    cleaned["latitude"] = payload.get("latitude", lat)
    cleaned["longitude"] = payload.get("longitude", lon)

    # Conversión de strings de selección a valores numéricos
    if "humidity" in payload:
        cleaned["humidity"] = map_humidity_to_val(payload["humidity"])
    if "temperature" in payload:
        cleaned["temperature"] = map_temp_to_val(payload["temperature"])

    return cleaned


# Lista las zonas del usuario, convirtiendo los numeros de la DB a etiquetas legibles
@router.get("", summary="Listar zonas del usuario")
async def list_zones(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    zones = ZoneRepository(db)
    result = await zones.get_by_user_id(int(current_user["id"]), skip=skip, limit=limit)
    return [
        {
            "id": z.id,
            "name": z.name,
            "location": map_coords_to_location(z.latitude, z.longitude),
            "soil_type": z.soil_type,
            "humidity": map_val_to_humidity_str(z.humidity),
            "temperature": map_val_to_temp_str(z.temperature),
            "water_quality": z.water_quality,
            "latitude": float(z.latitude) if z.latitude is not None else None,
            "longitude": float(z.longitude) if z.longitude is not None else None,
            "created_at": z.created_at.isoformat(),
            "updated_at": z.updated_at.isoformat(),
        }
        for z in result
    ]


@router.get("/{zone_id}", summary="Detalle de una zona")
async def get_zone(
    zone_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    zones = ZoneRepository(db)
    # Valida que la zona exista y pertenezca al usuario
    zone = await zones.get_by_id_and_user(zone_id, int(current_user["id"]))
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zona no encontrada")
    return {
        "id": zone.id,
        "name": zone.name,
        "location": map_coords_to_location(zone.latitude, zone.longitude),
        "soil_type": zone.soil_type,
        "humidity": map_val_to_humidity_str(zone.humidity),
        "temperature": map_val_to_temp_str(zone.temperature),
        "water_quality": zone.water_quality,
        "latitude": float(zone.latitude) if zone.latitude is not None else None,
        "longitude": float(zone.longitude) if zone.longitude is not None else None,
        "created_at": zone.created_at.isoformat(),
        "updated_at": zone.updated_at.isoformat(),
    }


# Crea una zona: valida nombre, evita duplicados por usuario y sanitiza el payload
@router.post("", status_code=status.HTTP_201_CREATED, summary="Crear una zona")
async def create_zone(
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    zones = ZoneRepository(db)
    audit = AuditRepository(db)

    name = payload.get("name", "").strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El campo 'name' es obligatorio",
        )

    # Verificar nombre duplicado para el mismo usuario
    if await zones.exists_name_for_user(int(current_user["id"]), name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya tenés una zona llamada '{name}'",
        )

    # Sanitizar y mapear el payload
    cleaned = clean_payload(payload)

    zone = await zones.create_zone(int(current_user["id"]), cleaned)

    await audit.log(
        action=AuditAction.CREATE,
        user_id=int(current_user["id"]),
        entity_type="zone",
        entity_id=zone.id,
    )

    return {"id": zone.id, "name": zone.name, "message": "Zona creada"}


@router.put("/{zone_id}", summary="Actualizar una zona")
async def update_zone(
    zone_id: int,
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    zones = ZoneRepository(db)
    audit = AuditRepository(db)

    zone = await zones.get_by_id_and_user(zone_id, int(current_user["id"]))
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zona no encontrada")

    # Sanitizar y mapear el payload
    cleaned = clean_payload(payload)

    updated = await zones.update_zone(zone, cleaned)

    await audit.log(
        action=AuditAction.UPDATE,
        user_id=int(current_user["id"]),
        entity_type="zone",
        entity_id=updated.id,
    )

    return {"id": updated.id, "name": updated.name, "message": "Zona actualizada"}


@router.delete("/{zone_id}", summary="Eliminar una zona")
async def delete_zone(
    zone_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    zones = ZoneRepository(db)
    audit = AuditRepository(db)

    zone = await zones.get_by_id_and_user(zone_id, int(current_user["id"]))
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zona no encontrada")

    await audit.log(
        action=AuditAction.DELETE,
        user_id=int(current_user["id"]),
        entity_type="zone",
        entity_id=zone_id,
    )

    await zones.delete_zone(zone)

    return {"message": "Zona eliminada", "zone_id": zone_id}

