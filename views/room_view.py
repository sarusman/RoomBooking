"""Vue JSON : champs publics des réponses, sérialisés par FastAPI."""

from pydantic import BaseModel, ConfigDict


class RoomView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    capacity: int
    floor: int
    equipment: list[str]
    available: bool
