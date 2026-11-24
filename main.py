"""Room Service : première étape du projet RoomBooking."""

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="RoomBooking — Room Service", version="1.0.0")


class RoomData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1)
    capacity: int = Field(gt=0)
    floor: int
    equipment: list[str] = Field(default_factory=list)
    available: bool = True


class Room(RoomData):
    id: int


# Stockage en mémoire : les modifications disparaissent au redémarrage.
rooms = {
    1: Room(id=1, name="A101", capacity=30, floor=1,
            equipment=["Vidéoprojecteur", "Wi-Fi"]),
    2: Room(id=2, name="B205", capacity=15, floor=2,
            equipment=["Tableau blanc", "Wi-Fi"]),
    3: Room(id=3, name="C302", capacity=40, floor=3,
            equipment=["Ordinateurs", "Vidéoprojecteur"], available=False),
}
next_id = 4


def find_room(room_id: int) -> Room:
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Salle introuvable")
    return rooms[room_id]


@app.get("/", include_in_schema=False)
async def index():
    return RedirectResponse("/docs")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/rooms", response_model=list[Room])
async def list_rooms(
    min_capacity: int = Query(default=1, ge=1),
    available: bool | None = None,
):
    return [
        room for room in rooms.values()
        if room.capacity >= min_capacity
        and (available is None or room.available == available)
    ]


@app.get("/rooms/{room_id}", response_model=Room)
async def get_room(room_id: int):
    return find_room(room_id)


@app.post("/rooms", response_model=Room, status_code=201)
async def create_room(data: RoomData):
    global next_id
    room = Room(id=next_id, **data.model_dump())
    rooms[room.id] = room
    next_id += 1
    return room


@app.put("/rooms/{room_id}", response_model=Room)
async def update_room(room_id: int, data: RoomData):
    find_room(room_id)
    rooms[room_id] = Room(id=room_id, **data.model_dump())
    return rooms[room_id]


@app.delete("/rooms/{room_id}", status_code=204)
async def delete_room(room_id: int):
    find_room(room_id)
    del rooms[room_id]
    return Response(status_code=204)
