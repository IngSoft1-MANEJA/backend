from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app.exceptions import *
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.connection_manager import manager
from app.database import get_db
from app.models.models import Players
from app.models.enums import ReasonWinning

router = APIRouter(prefix="/matches")

async def playerWinner(match_id:int, reason: ReasonWinning, db):
    match_service = MatchService(db)
    player_service = PlayerService(db) 
    
    players = player_service.get_players_by_match(match_id)[0]
    player_id = players.id
    player_service.delete_player(player_id)
    match_service.update_match(match_id, "FINISHED", 0)

    msg = {"key": "WINNER", "payload":{"player_id": player_id, "Reason": reason}}
    await manager.broadcast_to_game(match_id, msg)

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
        except Exception as e:
            raise HTTPException(status_code=404, detail="Player not connected to match")
        
        match_service.update_match(match_id, match_to_leave.state, match_to_leave.current_players - 1)
        
        if (match_to_leave.current_players) == 1:
            await playerWinner(match_id, ReasonWinning.FORFEIT, db)
        
        msg = {"key": "PLAYER_LEFT", "payload":{"name": player_name}}

        await manager.broadcast_to_game(match_id, msg)
        return {"player_id": player_id, "players": player_name}

    except PlayerNotConnected as e:
        raise HTTPException(status_code=404, detail="Player not connected to match")
    except GameConnectionDoesNotExist as e:
        raise HTTPException(status_code=404, detail="Match not found")
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Match not found")