from fastapi import FastAPI, WebSocket
from app.routers import matches
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/")
def hello_world():
    return {"Hello": "World"}