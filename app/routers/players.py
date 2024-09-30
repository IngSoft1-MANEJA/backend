from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.exceptions import *
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.connection_manager import ConnectionManager
from app.schemas import MatchCreateIn, MatchOut
from app.database import get_db
from app.models.models import Players

router = APIRouter(prefix="/matches")

manager = ConnectionManager()

@router.delete("/{match_id}/left/{player_id}")
def leave_player(player_id: int, match_id: int, db: Session = Depends(get_db)):
    PlayerService(db).delete_player(player_id)
    return {"detail": "Player deleted successfully"}