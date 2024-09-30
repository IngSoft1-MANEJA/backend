from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.exceptions import *
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.connection_manager import manager
from app.database import get_db

router = APIRouter(prefix="/matches")

@router.delete("/{match_id}/left/{player_id}")
def leave_player(player_id: int, match_id: int, db: Session = Depends(get_db)):
    try:
        match_service = MatchService(db)
        player_service = PlayerService(db)
        
        player_to_delete = player_service.get_player_by_id(player_id)
        match_to_leave = match_service.get_match_by_id(match_id)
        
        player_match = player_to_delete.match_id
        if player_match != match_id:
            raise HTTPException(status_code=404, detail="Player not in match")
        
        # IN LOBBY
        if match_to_leave.state == "WAITING":
            if player_to_delete.is_owner:
                raise HTTPException(status_code=400, detail="Owner cannot leave match")
        else:
            manager.broadcast_to_game(match_id, {"detail": f"Player {player_id} left the lobby"})
                

        player_service.delete_player(player_id)
        manager.disconnect_player_from_game(match_id, player_id)
        match_service.update_match(match_id, match_to_leave.state, match_to_leave.current_players - 1)
        
        
        if match_to_leave.state == "STARTED":
            manager.broadcast_to_game(match_id, {"detail": f"Player {player_id} left the match"})
            if match_to_leave.current_players == 1:
                manager.broadcast_to_game(match_id, {"detail": "Match finished by abandon, you Win!"})
                match_service.update_match(match_id, "FINISHED", match_to_leave.current_players)
                
        return {"detail": "Player leave successfully"}
    except PlayerNotConnected as e:
        raise HTTPException(status_code=404, detail="Player not connected to match")
    except GameConnectionDoesNotExist as e:
        raise HTTPException(status_code=404, detail="Match not found")
        