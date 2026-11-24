"""Routes HTTP : réception des demandes, appel du modèle et choix de la vue."""

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import RedirectResponse

from models import room as room_model
from models.room import RoomData
from views.room_view import RoomView

router = APIRouter()


@router.get("/", include_in_schema=False)
async def index():
    return RedirectResponse("/docs")


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/rooms", response_model=list[RoomView])
async def list_rooms(
    min_capacity: int = Query(default=1, ge=1),
    available: bool | None = None,
):
    return room_model.list_rooms(min_capacity, available)


@router.get("/rooms/{room_id}", response_model=RoomView)
async def get_room(room_id: int):
    try:
        return room_model.get_room(room_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Salle introuvable") from None


@router.post("/rooms", response_model=RoomView, status_code=201)
async def create_room(data: RoomData):
    return room_model.create_room(data)


@router.put("/rooms/{room_id}", response_model=RoomView)
async def update_room(room_id: int, data: RoomData):
    try:
        return room_model.update_room(room_id, data)
    except KeyError:
        raise HTTPException(status_code=404, detail="Salle introuvable") from None


@router.delete("/rooms/{room_id}", status_code=204)
async def delete_room(room_id: int):
    try:
        room_model.delete_room(room_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Salle introuvable") from None
    return Response(status_code=204)
