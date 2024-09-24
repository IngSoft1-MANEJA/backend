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

@app.websocket("/ws/")
async def create_websocket_connection(websocket: WebSocket):
    await websocket.accept()

    await websocket.send_json({"msg": "Hello WebSocket"})
    
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(
            f"Session cookie or query token value is"
        )