from fastapi import FastAPI

from app.config import (
    settings,  # Loads & validates environment settings from app/config.py
)
from app.routers.tickets import router as ticket_router

app = FastAPI(title="Apex Pay API")

# Register the router with your app
app.include_router(ticket_router)