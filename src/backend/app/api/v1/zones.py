from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user

router = APIRouter(prefix="/zones", tags=["zones"])

ZONES: list[dict[str, object]] = []


@router.get("/", summary="Listar zonas del usuario")
async def list_zones(current_user: dict[str, object] = Depends(get_current_user)) -> list[dict[str, object]]:
    return [zone for zone in ZONES if zone["user_id"] == current_user["id"]]


@router.post("/", summary="Crear una zona")
async def create_zone(payload: dict[str, object], current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
    zone = {"id": f"zone-{len(ZONES) + 1}", "user_id": current_user["id"], **payload}
    ZONES.append(zone)
    return zone


@router.put("/{zone_id}", summary="Actualizar una zona")
async def update_zone(zone_id: str, payload: dict[str, object], current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
    for zone in ZONES:
        if zone["id"] == zone_id and zone["user_id"] == current_user["id"]:
            zone.update(payload)
            return zone
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zona no encontrada")


@router.delete("/{zone_id}", summary="Eliminar una zona")
async def delete_zone(zone_id: str, current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
    for index, zone in enumerate(ZONES):
        if zone["id"] == zone_id and zone["user_id"] == current_user["id"]:
            removed = ZONES.pop(index)
            return {"message": "Zona eliminada", "zone": removed}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zona no encontrada")
