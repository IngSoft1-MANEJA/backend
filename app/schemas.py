from typing import List
from pydantic import BaseModel
from app.utils.board_shapes_algorithm import Figure

class MatchCreateIn(BaseModel):
    lobby_name: str
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


class MatchCreateOut(MatchOut):
    player_name: str


class PlayerJoinIn(BaseModel):
    player_name: str


class PlayerJoinOut(BaseModel):
    player_id: int


class Tile(BaseModel):
    rowIndex: int
    columnIndex: int


class PartialMove(BaseModel):
    tiles: List[Tile]
    movement_card: int

class UseFigure(BaseModel):
    figure_id: int
    coordinates: list[tuple]