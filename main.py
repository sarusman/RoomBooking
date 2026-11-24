"""Point d'entrée du Room Service : assemblage de l'application MVC."""

from fastapi import FastAPI

from controllers.room_controller import router

app = FastAPI(title="RoomBooking — Room Service", version="1.0.0")
app.include_router(router)
