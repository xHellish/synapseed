"""Routing de zonas — capa delgada que delega a ZoneService.

Los handlers solo se ocupan de:
1. Recibir la request HTTP.
2. Extraer dependencias via ``Depends()``.
3. Llamar a ``ZoneService``.
4. Convertir errores de dominio a excepciones HTTP.

La lógica de mapeo, validación y acceso a datos vive en
``app.services.zone_service.ZoneService``.

Cumplimiento SOLID:
- SRP: el router solo maneja routing HTTP.
- DIP: los repositorios se inyectan a través de ``get_zone_service``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.repositories import AuditRepository, ZoneRepository
from app.services.zone_service import ZoneService

router = APIRouter(prefix="/zones", tags=["zones"])


# ---------------------------------------------------------------------------
# Proveedor de dependencia — instancia ZoneService con repositorios concretos
# ---------------------------------------------------------------------------

def get_zone_service(db: AsyncSession = Depends(get_db)) -> ZoneService:
    """Fabrica una instancia de ``ZoneService`` con los repositorios de la sesión DB."""
    return ZoneService(ZoneRepository(db), AuditRepository(db))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", summary="Listar zonas del usuario")
async def list_zones(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    service: ZoneService = Depends(get_zone_service),
) -> list:
    return await service.list_zones(int(current_user["id"]), skip=skip, limit=limit)


@router.get("/{zone_id}", summary="Detalle de una zona")
async def get_zone(
    zone_id: int,
    current_user: dict = Depends(get_current_user),
    service: ZoneService = Depends(get_zone_service),
) -> dict:
    zone = await service.get_zone(zone_id, int(current_user["id"]))
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zona no encontrada")
    return zone


@router.post("", status_code=status.HTTP_201_CREATED, summary="Crear una zona")
async def create_zone(
    payload: dict,
    current_user: dict = Depends(get_current_user),
    service: ZoneService = Depends(get_zone_service),
) -> dict:
    try:
        return await service.create_zone(int(current_user["id"]), payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.put("/{zone_id}", summary="Actualizar una zona")
async def update_zone(
    zone_id: int,
    payload: dict,
    current_user: dict = Depends(get_current_user),
    service: ZoneService = Depends(get_zone_service),
) -> dict:
    result = await service.update_zone(zone_id, int(current_user["id"]), payload)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zona no encontrada")
    return result


@router.delete("/{zone_id}", summary="Eliminar una zona")
async def delete_zone(
    zone_id: int,
    current_user: dict = Depends(get_current_user),
    service: ZoneService = Depends(get_zone_service),
) -> dict:
    deleted = await service.delete_zone(zone_id, int(current_user["id"]))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zona no encontrada")
    return {"message": "Zona eliminada", "zone_id": zone_id}
