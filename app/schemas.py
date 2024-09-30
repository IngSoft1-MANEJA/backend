from pydantic import BaseModel
from app.models.models import Matches, Players, Boards, Tiles, ShapeCards, MovementCards 
    
class MatchCreateIn(BaseModel):
    name: str
    is_public: bool
    max_players: int
    player_name: str
    token: str

class MatchOut(BaseModel):
    id: int
    match_name: str
    is_public: bool
    state: str
    max_players: int
    current_players: int
    
    class Config:
        orm_mode = True

class MatchCreateOut(MatchOut):
    player_name: str
    
    class Config:
        orm_mode = True

class PlayerJoinIn(BaseModel):
    player_name: str

class PlayerJoinOut(BaseModel):
    player_id: int