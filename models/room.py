"""Données des salles et opérations sur le stockage en mémoire."""

from pydantic import BaseModel, ConfigDict, Field


class RoomData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1)
    capacity: int = Field(gt=0)
    floor: int
    equipment: list[str] = Field(default_factory=list)
    available: bool = True


class Room(RoomData):
    id: int


# Les modifications disparaissent au redémarrage du processus.
rooms = {
    1: Room(id=1, name="A101", capacity=30, floor=1,
            equipment=["Vidéoprojecteur", "Wi-Fi"]),
    2: Room(id=2, name="B205", capacity=15, floor=2,
            equipment=["Tableau blanc", "Wi-Fi"]),
    3: Room(id=3, name="C302", capacity=40, floor=3,
            equipment=["Ordinateurs", "Vidéoprojecteur"], available=False),
}
next_id = 4


def list_rooms(min_capacity: int = 1, available: bool | None = None) -> list[Room]:
    return [
        room for room in rooms.values()
        if room.capacity >= min_capacity
        and (available is None or room.available == available)
    ]


def get_room(room_id: int) -> Room:
    return rooms[room_id]


def create_room(data: RoomData) -> Room:
    global next_id
    room = Room(id=next_id, **data.model_dump())
    rooms[room.id] = room
    next_id += 1
    return room


def update_room(room_id: int, data: RoomData) -> Room:
    get_room(room_id)
    rooms[room_id] = Room(id=room_id, **data.model_dump())
    return rooms[room_id]


def delete_room(room_id: int) -> None:
    del rooms[room_id]
