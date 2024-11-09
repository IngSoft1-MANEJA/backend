import os

from fastapi import FastAPI, WebSocket
from app.routers import matches, players
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db

os.environ["TURN_TIMER"] = "120"

init_db()

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matches.router)
app.include_router(players.router)


@app.get("/")
def hello_world():
    return {"Hello": "World"}
