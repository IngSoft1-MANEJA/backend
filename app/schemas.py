from pydantic import BaseModel
from app.models.models import Matches, Players, Boards, Tiles, ShapeCards, MovementCards

class MatchIn(BaseModel):
    match_name: str
    state: str
    is_public: bool
    max_players: int    