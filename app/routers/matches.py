import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException, Depends, HTTPException
from sqlalchemy.orm import Session

from app.exceptions import *
from app.connection_manager import ConnectionManager
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.schemas import *
from app.database import get_db

router = APIRouter(prefix="/matches")

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


@router.get("/", response_model=list[MatchOut])
def get_matches(db: Session = Depends(get_db)):
    try:
        match_service = MatchService(db)
        matches = match_service.get_all_matches(available=True)
    except:
        raise HTTPException(status_code=404, detail="No matches found")


@router.get("/{match_id}", response_model=MatchOut)
def get_match_by_id(match_id: int, db: Session = Depends(get_db)):
    try:
        match_service = MatchService(db)
        match = match_service.get_match_by_id(match_id)
    except:
        raise HTTPException(status_code=404, detail="Match not found")

@router.post("/")
def create_match(match: MatchCreateIn, db: Session = Depends(get_db)):
    match_service = MatchService(db)
    player_service = PlayerService(db)
    
    match1 = match_service.create_match(match.name, match.max_players, match.is_public)
    new_player = player_service.create_player(match.player_name, match1.id, True , match.token)
    return {"player_id": new_player.id, "match_id": match1.id}

@router.post("/{match_id}/")
def join_player_to_match(match_id: int, playerJoinIn: PlayerJoinIn, db: Session = Depends(get_db)):
    try:
        match_service = MatchService(db)
        match = match_service.get_match_by_id(match_id)

        if match.current_players >= match.max_players:
            raise HTTPException(status_code=404, detail="Match is full")
        
        player_service = PlayerService(db)
        player = player_service.create_player(playerJoinIn.player_name, match_id, False, "123")
        match.current_players = match.current_players + 1
        players = [player.player_name for player in match.players]
        db.commit()

        return {"player_id": player.id, "players": players}
    except:
        raise HTTPException(status_code=404, detail="Match not found")
    

    

    