from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from sqlalchemy import select

from app.exceptions import *
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.connection_manager import manager
from app.database import get_db
from app.models.models import Players, Matches
from app.models.enums import ReasonWinning

router = APIRouter(prefix="/matches")

async def playerWinner(match_id: int, reason: ReasonWinning, db: Session):
    match_service = MatchService(db)
    player_service = PlayerService(db) 
    
    players = player_service.get_players_by_match(match_id)[0]
    player_id = players.id
    player_service.delete_player(player_id)
    match_service.update_match(match_id, "FINISHED", 0)
    reason_winning = reason.value
    
    msg = {"key": "WINNER", "payload": {"player_id": player_id, "Reason": reason_winning}}
    
    try:
        await manager.broadcast_to_game(match_id, msg)
    except RuntimeError as e:
        # Manejar el caso en que el WebSocket ya esté cerrado
        print(f"Error al enviar mensaje: {e}")

@router.delete("/{match_id}/left/{player_id}")
async def leave_player(player_id: int, match_id: int, db: Session = Depends(get_db)):
    try:
        match_service = MatchService(db)
        player_service = PlayerService(db)

        player_to_delete = player_service.get_player_by_id(player_id)
        match_to_leave = match_service.get_match_by_id(match_id)

        player_name = player_to_delete.player_name
        player_match = player_to_delete.match_id

        if player_match != match_id:
            raise HTTPException(status_code=404, detail="Player not in match")

        # IN LOBBY
        if match_to_leave.state == "WAITING":
            if player_to_delete.is_owner:
                raise HTTPException(status_code=400, detail="Owner cannot leave match")
                
        match_to_leave = match_service.get_match_by_id(match_id)
        player_service.delete_player(player_id)

        try:
            manager.disconnect_player_from_game(match_id, player_id)
        except PlayerNotConnected:
            # El jugador ya ha sido desconectado, no hacer nada
            pass
        
        match_service.update_match(match_id, match_to_leave.state, match_to_leave.current_players - 1)
        
        msg = {"key": "PLAYER_LEFT", "payload": {"name": player_name}}

        try:
            await manager.broadcast_to_game(match_id, msg)
        except RuntimeError as e:
            # Manejar el caso en que el WebSocket ya esté cerrado
            print(f"Error al enviar mensaje: {e}")

        if (match_to_leave.current_players) == 1 and match_to_leave.state == "STARTED":
            await playerWinner(match_id, ReasonWinning.FORFEIT, db)
        
        return {"player_id": player_id, "players": player_name}

    except PlayerNotConnected as e:
        raise HTTPException(
            status_code=404, detail="Player not connected to match")
    except GameConnectionDoesNotExist as e:
        raise HTTPException(status_code=404, detail="Match not found")
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Match not found")
    

@router.patch("/{match_id}/end-turn/{player_id}", status_code=200)
async def end_turn(match_id: int, player_id: int, db: Session = Depends(get_db)):
    match_service = MatchService(db)
    player_service = PlayerService(db)

    match = match_service.get_match_by_id(match_id= match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    
    player = player_service.get_player_by_id(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if player.turn_order != match.current_player_turn:
        raise HTTPException(status_code=403, detail=f"It's not player {player.player_name}'s turn")
    
    print("antes",match.current_player_turn)
    print("current player", match.current_player_turn)
    
    if match.current_player_turn == match.current_players:
        print("entro aca")
        match_service.update_turn(match_id, turn=1)
    else :
        print("no se xq estoy aca")
        match_service.update_turn(match_id, match.current_player_turn + 1) 

    print("dsps",match.current_player_turn)
    
    next_player = player_service.get_player_by_turn(turn_order= match.current_player_turn, match_id= match_id)

    msg = {
        "key": "END_PLAYER_TURN", 
        "payload": {
            "current_player_name": player.player_name,
            "next_player_name": next_player.player_name,
            "next_player_turn": next_player.turn_order
        }
    }
    await manager.broadcast_to_game(match_id, msg)
    
