"""Servicio de zonas con mappers especializados — SRP + OCP + DIP.

Extrae la lógica de dominio que antes vivía en ``api/v1/zones.py``:
- ``LocationMapper`` — conversión nombre de provincia ↔ coordenadas GPS.
- ``HumidityMapper`` — conversión etiqueta textual ↔ valor numérico de humedad.
- ``TemperatureMapper`` — conversión etiqueta textual ↔ valor numérico de temperatura.
- ``ZoneService`` — operaciones CRUD de zonas con auditoría.

Cumplimiento SOLID:
- SRP: cada clase tiene una sola responsabilidad de transformación o acceso a datos.
- OCP: añadir una nueva provincia = actualizar ``LOCATION_REGISTRY``, sin modificar la lógica.
- DIP: ``ZoneService`` recibe sus repositorios por constructor (inyección de dependencias).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.audit_log import AuditAction
from app.repositories import AuditRepository, ZoneRepository


# ---------------------------------------------------------------------------
# Tipo de dato de coordenadas
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LocationCoordinate:
    """Par de coordenadas GPS (latitud, longitud)."""
    lat: float
    lon: float


# ---------------------------------------------------------------------------
# LocationMapper — OCP: registro de datos, sin cascada de if/else
# ---------------------------------------------------------------------------

class LocationMapper:
    """Convierte nombres de provincias de Costa Rica a coordenadas GPS y viceversa.

    El registro ``LOCATION_REGISTRY`` actúa como tabla de datos: agregar una
    nueva provincia no requiere modificar ningún método (OCP).
    """

    LOCATION_REGISTRY: dict[str, LocationCoordinate] = {
        "cartago":    LocationCoordinate(9.86,  -83.92),
        "alajuela":   LocationCoordinate(10.02, -84.21),
        "heredia":    LocationCoordinate(10.00, -84.12),
        "san jose":   LocationCoordinate(9.93,  -84.09),
        "san josé":   LocationCoordinate(9.93,  -84.09),
        "guanacaste": LocationCoordinate(10.60, -85.40),
        "puntarenas": LocationCoordinate(9.98,  -84.83),
        "limon":      LocationCoordinate(10.00, -83.03),
        "limón":      LocationCoordinate(10.00, -83.03),
    }

    # Registro inverso: coordenadas -> nombre para display
    _DISPLAY_NAMES: dict[tuple[float, float], str] = {
        (9.86,  -83.92): "Cartago, Costa Rica",
        (10.02, -84.21): "Alajuela, Costa Rica",
        (10.00, -84.12): "Heredia, Costa Rica",
        (9.93,  -84.09): "San José, Costa Rica",
        (10.60, -85.40): "Guanacaste, Costa Rica",
        (9.98,  -84.83): "Puntarenas, Costa Rica",
        (10.00, -83.03): "Limón, Costa Rica",
    }

    @classmethod
    def location_string_to_coords(
        cls, location_str: str | None
    ) -> tuple[float | None, float | None]:
        """Convierte un nombre de provincia a coordenadas GPS.

        Retorna las coordenadas de San José como fallback si no hay coincidencia.
        """
        if not location_str:
            return None, None

        loc_lower = location_str.lower()
        for key, coord in cls.LOCATION_REGISTRY.items():
            if key in loc_lower:
                return coord.lat, coord.lon

        # Fallback: San José
        return 9.93, -84.09

    @classmethod
    def coords_to_location_string(
        cls, lat: float | None, lon: float | None
    ) -> str:
        """Convierte coordenadas GPS al nombre de provincia más cercano."""
        if lat is None or lon is None:
            return "Costa Rica"

        closest_dist = float("inf")
        closest_name = "Costa Rica"

        for (plat, plon), name in cls._DISPLAY_NAMES.items():
            dist = (float(lat) - plat) ** 2 + (float(lon) - plon) ** 2
            if dist < closest_dist:
                closest_dist = dist
                closest_name = name

        if closest_dist < 0.05:
            return closest_name
        return f"Costa Rica ({float(lat):.4f}, {float(lon):.4f})"


# ---------------------------------------------------------------------------
# HumidityMapper
# ---------------------------------------------------------------------------

class HumidityMapper:
    """Convierte entre etiquetas textuales y valores numéricos de humedad."""

    _STR_TO_VAL: dict[str, float] = {
        "muy baja": 20.0,
        "baja":     40.0,
        "media":    60.0,
        "alta":     80.0,
        "muy alta": 95.0,
    }

    @classmethod
    def to_value(cls, hum_str: str | float | None) -> float | None:
        """Convierte etiqueta textual o valor numérico a float."""
        if hum_str is None:
            return None
        if isinstance(hum_str, (int, float)):
            return float(hum_str)
        try:
            return float(hum_str)
        except ValueError:
            pass
        return cls._STR_TO_VAL.get(hum_str.lower().strip())

    @classmethod
    def to_label(cls, hum_val: float | None) -> str:
        """Convierte un valor numérico de humedad a etiqueta textual."""
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


# ---------------------------------------------------------------------------
# TemperatureMapper
# ---------------------------------------------------------------------------

class TemperatureMapper:
    """Convierte entre etiquetas textuales y valores numéricos de temperatura."""

    _STR_TO_VAL: dict[str, float] = {
        "menos de 10°c": 8.0,
        "menos de 10c":  8.0,
        "10°c - 15°c":   12.5,
        "10c - 15c":     12.5,
        "15°c - 20°c":   17.5,
        "15c - 20c":     17.5,
        "20°c - 25°c":   22.5,
        "20c - 25c":     22.5,
        "25°c - 30°c":   27.5,
        "25c - 30c":     27.5,
        "más de 30°c":   35.0,
        "mas de 30c":    35.0,
    }

    @classmethod
    def to_value(cls, temp_str: str | float | None) -> float | None:
        """Convierte etiqueta textual o valor numérico a float."""
        if temp_str is None:
            return None
        if isinstance(temp_str, (int, float)):
            return float(temp_str)
        try:
            return float(temp_str)
        except ValueError:
            pass
        cleaned = temp_str.lower().strip()
        if cleaned in cls._STR_TO_VAL:
            return cls._STR_TO_VAL[cleaned]
        cleaned_alt = cleaned.replace(" ", "")
        for key, val in cls._STR_TO_VAL.items():
            if key.replace(" ", "") == cleaned_alt:
                return val
        return None

    @classmethod
    def to_label(cls, temp_val: float | None) -> str:
        """Convierte un valor numérico de temperatura a etiqueta textual."""
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


# ---------------------------------------------------------------------------
# ZoneService — lógica de negocio de zonas (DIP: recibe repos por constructor)
# ---------------------------------------------------------------------------

class ZoneService:
    """Encapsula todas las operaciones de negocio sobre zonas.

    Recibe ``ZoneRepository`` y ``AuditRepository`` por constructor (DIP):
    la capa de routing no necesita conocer cómo se instancian los repositorios.
    """

    def __init__(
        self,
        zone_repo: ZoneRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self._zones = zone_repo
        self._audit = audit_repo

    # ------------------------------------------------------------------
    # Helpers de payload
    # ------------------------------------------------------------------

    def _clean_payload(self, payload: dict) -> dict:
        """Mapea y sanitiza el payload recibido del cliente."""
        # Extraer y convertir ubicación antes de clonar el payload
        location_str = payload.pop("location", None)
        lat, lon = LocationMapper.location_string_to_coords(location_str)

        cleaned: dict = {}
        for field in ("name", "soil_type", "water_quality"):
            if field in payload:
                cleaned[field] = payload[field]

        cleaned["latitude"] = payload.get("latitude", lat)
        cleaned["longitude"] = payload.get("longitude", lon)

        if "humidity" in payload:
            cleaned["humidity"] = HumidityMapper.to_value(payload["humidity"])
        if "temperature" in payload:
            cleaned["temperature"] = TemperatureMapper.to_value(payload["temperature"])

        return cleaned

    def _serialize_zone(self, z: object) -> dict:
        """Serializa una entidad Zone a un dict de respuesta."""
        return {
            "id": z.id,
            "name": z.name,
            "location": LocationMapper.coords_to_location_string(z.latitude, z.longitude),
            "soil_type": z.soil_type,
            "humidity": HumidityMapper.to_label(z.humidity),
            "temperature": TemperatureMapper.to_label(z.temperature),
            "water_quality": z.water_quality,
            "latitude": float(z.latitude) if z.latitude is not None else None,
            "longitude": float(z.longitude) if z.longitude is not None else None,
            "created_at": z.created_at.isoformat(),
            "updated_at": z.updated_at.isoformat(),
        }

    # ------------------------------------------------------------------
    # Operaciones de negocio
    # ------------------------------------------------------------------

    async def list_zones(
        self, user_id: int, skip: int, limit: int
    ) -> list[dict]:
        """Retorna la lista de zonas del usuario serializada."""
        zones = await self._zones.get_by_user_id(user_id, skip=skip, limit=limit)
        return [self._serialize_zone(z) for z in zones]

    async def get_zone(self, zone_id: int, user_id: int) -> dict | None:
        """Retorna el detalle de una zona, o ``None`` si no existe / no pertenece al usuario."""
        zone = await self._zones.get_by_id_and_user(zone_id, user_id)
        if not zone:
            return None
        return self._serialize_zone(zone)

    async def create_zone(self, user_id: int, payload: dict) -> dict:
        """Crea una zona validando nombre y registrando auditoría.

        Raises:
            ValueError: Si el nombre está vacío o ya existe para el usuario.
        """
        name = payload.get("name", "").strip()
        if not name:
            raise ValueError("El campo 'name' es obligatorio")

        if await self._zones.exists_name_for_user(user_id, name):
            raise ValueError(f"Ya tenés una zona llamada '{name}'")

        cleaned = self._clean_payload(payload)
        zone = await self._zones.create_zone(user_id, cleaned)

        await self._audit.log(
            action=AuditAction.CREATE,
            user_id=user_id,
            entity_type="zone",
            entity_id=zone.id,
        )

        return {"id": zone.id, "name": zone.name, "message": "Zona creada"}

    async def update_zone(
        self, zone_id: int, user_id: int, payload: dict
    ) -> dict | None:
        """Actualiza una zona y registra auditoría.

        Retorna ``None`` si la zona no existe o no pertenece al usuario.
        """
        zone = await self._zones.get_by_id_and_user(zone_id, user_id)
        if not zone:
            return None

        cleaned = self._clean_payload(payload)
        updated = await self._zones.update_zone(zone, cleaned)

        await self._audit.log(
            action=AuditAction.UPDATE,
            user_id=user_id,
            entity_type="zone",
            entity_id=updated.id,
        )

        return {"id": updated.id, "name": updated.name, "message": "Zona actualizada"}

    async def delete_zone(self, zone_id: int, user_id: int) -> bool:
        """Elimina una zona y registra auditoría.

        Retorna ``False`` si la zona no existe o no pertenece al usuario.
        """
        zone = await self._zones.get_by_id_and_user(zone_id, user_id)
        if not zone:
            return False

        await self._audit.log(
            action=AuditAction.DELETE,
            user_id=user_id,
            entity_type="zone",
            entity_id=zone_id,
        )

        await self._zones.delete_zone(zone)
        return True
