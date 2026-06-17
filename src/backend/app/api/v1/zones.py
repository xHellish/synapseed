from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.repositories import AuditRepository, ZoneRepository
from app.services.zone_service import (
    ZoneConflictError,
    ZoneNotFoundError,
    ZoneService,
    ZoneValidationError,
)

router = APIRouter(prefix="/zones", tags=["zones"])


def get_zone_service(db: AsyncSession = Depends(get_db)) -> ZoneService:
    return ZoneService(ZoneRepository(db), AuditRepository(db))


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
    try:
        return await service.get_zone(zone_id, int(current_user["id"]))
    except ZoneNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zona no encontrada",
        ) from exc


@router.post("", status_code=status.HTTP_201_CREATED, summary="Crear una zona")
async def create_zone(
    payload: dict,
    current_user: dict = Depends(get_current_user),
    service: ZoneService = Depends(get_zone_service),
) -> dict:
    try:
        return await service.create_zone(int(current_user["id"]), payload)
    except ZoneValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ZoneConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.put("/{zone_id}", summary="Actualizar una zona")
async def update_zone(
    zone_id: int,
    payload: dict,
    current_user: dict = Depends(get_current_user),
    service: ZoneService = Depends(get_zone_service),
) -> dict:
    try:
        return await service.update_zone(zone_id, int(current_user["id"]), payload)
    except ZoneNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zona no encontrada",
        ) from exc


@router.delete("/{zone_id}", summary="Eliminar una zona")
async def delete_zone(
    zone_id: int,
    current_user: dict = Depends(get_current_user),
    service: ZoneService = Depends(get_zone_service),
) -> dict:
    try:
        return await service.delete_zone(zone_id, int(current_user["id"]))
    except ZoneNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zona no encontrada",
        ) from exc

