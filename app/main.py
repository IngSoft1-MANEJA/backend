from fastapi import FastAPI, WebSocket
from app.routers import matches, players
from fastapi.middleware.cors import CORSMiddleware
from tests.populate_test_db import load_data_for_test

from app.database import init_db

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

load_data_for_test()

@app.get("/")
def hello_world():
    return {"Hello": "World"}