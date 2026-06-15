from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditAction
from app.repositories import AuditRepository, ZoneRepository

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("/", summary="Listar zonas del usuario")
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
            "soil_type": z.soil_type,
            "humidity": float(z.humidity) if z.humidity is not None else None,
            "temperature": float(z.temperature) if z.temperature is not None else None,
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
        "soil_type": zone.soil_type,
        "humidity": float(zone.humidity) if zone.humidity is not None else None,
        "temperature": float(zone.temperature) if zone.temperature is not None else None,
        "water_quality": zone.water_quality,
        "latitude": float(zone.latitude) if zone.latitude is not None else None,
        "longitude": float(zone.longitude) if zone.longitude is not None else None,
        "created_at": zone.created_at.isoformat(),
        "updated_at": zone.updated_at.isoformat(),
    }


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Crear una zona")
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

    zone = await zones.create_zone(int(current_user["id"]), payload)

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

    updated = await zones.update_zone(zone, payload)

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
