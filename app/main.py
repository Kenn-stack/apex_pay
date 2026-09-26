from fastapi import FastAPI
from app.routers.tickets import router as tickets_router

app = FastAPI()
app.include_router(tickets_router)

@app.get("/")
def root():
    return {"message": "API is online"}