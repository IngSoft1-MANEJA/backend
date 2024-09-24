from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException

from exceptions import *
from connection_manager import ConnectionManager

router = APIRouter(prefix="/matches/")

manager = ConnectionManager()

@router.websocket("/{game_id}/ws/{player_id}")
async def create_websocket_connection(game_id: int, player_id: int, websocket: WebSocket):
    await websocket.accept()

    try:
        try:
            manager.connect_player_to_game(game_id, player_id, websocket)
            await manager.keep_alive(websocket)
        except GameConnectionDoesNotExist:
            await websocket.send_json(
                {"Error": f"Conexión a la partida {game_id} no existe"}
            )
            await websocket.close()
        except PlayerAlreadyConnected:
            await websocket.send_json(
                {
                    "Error": f"Jugador {player_id} ya tiene una conexión activa a la partida {game_id}"
                }
            )
            await websocket.close()
            raise WebSocketDisconnect

    except WebSocketDisconnect:
        manager.disconnect_player_from_game(game_id, player_id)