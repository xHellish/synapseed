from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from app.models.audit_log import AuditAction
from app.models.zone import Zone
from app.repositories import AuditRepository, ZoneRepository


@dataclass(frozen=True)
class LocationCoordinate:
    latitude: float
    longitude: float
    label: str
    aliases: tuple[str, ...]


class ZoneValidationError(ValueError):
    """Error de validación de datos de zona."""


class ZoneConflictError(ValueError):
    """Error por conflicto de datos de zona."""


class ZoneNotFoundError(ValueError):
    """Error cuando la zona no existe o no pertenece al usuario."""


class LocationMapper:
    DEFAULT_COORDINATE = LocationCoordinate(
        latitude=9.93,
        longitude=-84.09,
        label="San José, Costa Rica",
        aliases=("san josé", "san jose"),
    )
    LOCATION_REGISTRY: tuple[LocationCoordinate, ...] = (
        LocationCoordinate(9.86, -83.92, "Cartago, Costa Rica", ("cartago",)),
        LocationCoordinate(10.02, -84.21, "Alajuela, Costa Rica", ("alajuela",)),
        LocationCoordinate(10.00, -84.12, "Heredia, Costa Rica", ("heredia",)),
        DEFAULT_COORDINATE,
        LocationCoordinate(10.60, -85.40, "Guanacaste, Costa Rica", ("guanacaste",)),
        LocationCoordinate(9.98, -84.83, "Puntarenas, Costa Rica", ("puntarenas",)),
        LocationCoordinate(10.00, -83.03, "Limón, Costa Rica", ("limón", "limon")),
    )

    @classmethod
    def location_to_coords(cls, location: str | None) -> tuple[float | None, float | None]:
        if not location:
            return None, None

        normalized = location.lower()
        for coordinate in cls.LOCATION_REGISTRY:
            if any(alias in normalized for alias in coordinate.aliases):
                return coordinate.latitude, coordinate.longitude

        return cls.DEFAULT_COORDINATE.latitude, cls.DEFAULT_COORDINATE.longitude

    @classmethod
    def coords_to_location(cls, latitude: float | None, longitude: float | None) -> str:
        if latitude is None or longitude is None:
            return "Costa Rica"

        closest_distance = float("inf")
        closest_label = "Costa Rica"
        for coordinate in cls.LOCATION_REGISTRY:
            distance = (float(latitude) - coordinate.latitude) ** 2 + (
                float(longitude) - coordinate.longitude
            ) ** 2
            if distance < closest_distance:
                closest_distance = distance
                closest_label = coordinate.label

        if closest_distance < 0.05:
            return closest_label
        return f"Costa Rica ({float(latitude):.4f}, {float(longitude):.4f})"


class HumidityMapper:
    HUMIDITY_STR_TO_VAL: ClassVar[dict[str, float]] = {
        "muy baja": 20.0,
        "baja": 40.0,
        "media": 60.0,
        "alta": 80.0,
        "muy alta": 95.0,
    }

    @classmethod
    def to_value(cls, humidity: str | float | None) -> float | None:
        if humidity is None:
            return None
        if isinstance(humidity, int | float):
            return float(humidity)
        try:
            return float(humidity)
        except ValueError:
            pass
        return cls.HUMIDITY_STR_TO_VAL.get(humidity.lower().strip())

    @staticmethod
    def to_label(humidity: float | None) -> str:
        if humidity is None:
            return "Media"
        value = float(humidity)
        if value <= 30.0:
            return "Muy baja"
        if value <= 50.0:
            return "Baja"
        if value <= 70.0:
            return "Media"
        if value <= 90.0:
            return "Alta"
        return "Muy alta"


class TemperatureMapper:
    TEMP_STR_TO_VAL: ClassVar[dict[str, float]] = {
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

    @classmethod
    def to_value(cls, temperature: str | float | None) -> float | None:
        if temperature is None:
            return None
        if isinstance(temperature, int | float):
            return float(temperature)
        try:
            return float(temperature)
        except ValueError:
            pass

        cleaned = temperature.lower().strip()
        if cleaned in cls.TEMP_STR_TO_VAL:
            return cls.TEMP_STR_TO_VAL[cleaned]

        cleaned_alt = cleaned.replace(" ", "")
        for key, value in cls.TEMP_STR_TO_VAL.items():
            if key.replace(" ", "") == cleaned_alt:
                return value
        return None

    @staticmethod
    def to_label(temperature: float | None) -> str:
        if temperature is None:
            return "20°C - 25°C"
        value = float(temperature)
        if value < 10.0:
            return "Menos de 10°C"
        if value < 15.0:
            return "10°C - 15°C"
        if value < 20.0:
            return "15°C - 20°C"
        if value < 25.0:
            return "20°C - 25°C"
        if value < 30.0:
            return "25°C - 30°C"
        return "Más de 30°C"


class ZoneService:
    def __init__(
        self,
        zone_repository: ZoneRepository,
        audit_repository: AuditRepository,
        location_mapper: type[LocationMapper] = LocationMapper,
        humidity_mapper: type[HumidityMapper] = HumidityMapper,
        temperature_mapper: type[TemperatureMapper] = TemperatureMapper,
    ) -> None:
        self.zone_repository = zone_repository
        self.audit_repository = audit_repository
        self.location_mapper = location_mapper
        self.humidity_mapper = humidity_mapper
        self.temperature_mapper = temperature_mapper

    async def list_zones(self, user_id: int, skip: int, limit: int) -> list[dict[str, Any]]:
        zones = await self.zone_repository.get_by_user_id(user_id, skip=skip, limit=limit)
        return [self._serialize_zone(zone) for zone in zones]

    async def get_zone(self, zone_id: int, user_id: int) -> dict[str, Any]:
        zone = await self._get_owned_zone(zone_id, user_id)
        return self._serialize_zone(zone)

    async def create_zone(self, user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        name = str(payload.get("name", "")).strip()
        if not name:
            raise ZoneValidationError("El campo 'name' es obligatorio")

        if await self.zone_repository.exists_name_for_user(user_id, name):
            raise ZoneConflictError(f"Ya tenés una zona llamada '{name}'")

        zone = await self.zone_repository.create_zone(user_id, self._clean_payload(payload))
        await self.audit_repository.log(
            action=AuditAction.CREATE,
            user_id=user_id,
            entity_type="zone",
            entity_id=zone.id,
        )
        return {"id": zone.id, "name": zone.name, "message": "Zona creada"}

    async def update_zone(
        self,
        zone_id: int,
        user_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        zone = await self._get_owned_zone(zone_id, user_id)
        updated = await self.zone_repository.update_zone(zone, self._clean_payload(payload))
        await self.audit_repository.log(
            action=AuditAction.UPDATE,
            user_id=user_id,
            entity_type="zone",
            entity_id=updated.id,
        )
        return {"id": updated.id, "name": updated.name, "message": "Zona actualizada"}

    async def delete_zone(self, zone_id: int, user_id: int) -> dict[str, Any]:
        zone = await self._get_owned_zone(zone_id, user_id)
        await self.audit_repository.log(
            action=AuditAction.DELETE,
            user_id=user_id,
            entity_type="zone",
            entity_id=zone_id,
        )
        await self.zone_repository.delete_zone(zone)
        return {"message": "Zona eliminada", "zone_id": zone_id}

    async def _get_owned_zone(self, zone_id: int, user_id: int) -> Zone:
        zone = await self.zone_repository.get_by_id_and_user(zone_id, user_id)
        if not zone:
            raise ZoneNotFoundError("Zona no encontrada")
        return zone

    def _clean_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        source = dict(payload)
        location = source.pop("location", None)
        latitude, longitude = self.location_mapper.location_to_coords(location)

        cleaned: dict[str, Any] = {}
        for field in ("name", "soil_type", "water_quality"):
            if field in source:
                cleaned[field] = source[field]

        cleaned["latitude"] = source.get("latitude", latitude)
        cleaned["longitude"] = source.get("longitude", longitude)

        if "humidity" in source:
            cleaned["humidity"] = self.humidity_mapper.to_value(source["humidity"])
        if "temperature" in source:
            cleaned["temperature"] = self.temperature_mapper.to_value(source["temperature"])

        return cleaned

    def _serialize_zone(self, zone: Zone) -> dict[str, Any]:
        return {
            "id": zone.id,
            "name": zone.name,
            "location": self.location_mapper.coords_to_location(zone.latitude, zone.longitude),
            "soil_type": zone.soil_type,
            "humidity": self.humidity_mapper.to_label(zone.humidity),
            "temperature": self.temperature_mapper.to_label(zone.temperature),
            "water_quality": zone.water_quality,
            "latitude": float(zone.latitude) if zone.latitude is not None else None,
            "longitude": float(zone.longitude) if zone.longitude is not None else None,
            "created_at": zone.created_at.isoformat(),
            "updated_at": zone.updated_at.isoformat(),
        }
