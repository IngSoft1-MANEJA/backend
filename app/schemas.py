import logging
from typing import List
from pydantic import BaseModel, Field, field_validator, StrictBool

INVALID_CHARACTERS = set("!@#$%^&*()+=[]{}|\\;:'\",<>/?`~")

logger = logging.getLogger(__name__)

class MatchCreateIn(BaseModel):
    lobby_name: str
    is_public: bool
    max_players: int
    player_name: str
    token: str

    @field_validator("lobby_name", "player_name")
    @classmethod
    def validate_lobby_name_and_player_name(cls, value: str):
        if any(char in INVALID_CHARACTERS for char in value):
            raise ValueError("Input can't contain special characters")
        if len(value.strip()) < 3 or len(value.strip()) > 50:
            raise ValueError("Input length must be great than 3 and less than 50")
        if not value.replace(" ", "").isalnum():
            raise ValueError("Input must contain alphanumeric words")
        return value.strip()
    
    @field_validator("max_players")
    @classmethod
    def validate_max_players(cls, value: str):
        if not (2 <= value <= 4):
            raise ValueError("Input must be a number between 2 and 4")
        return value
    

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

    @field_validator("player_name")
    @classmethod
    def validate_player_name(cls, value: str):
        if any(char in INVALID_CHARACTERS for char in value):
            raise ValueError("Input can't contain special characters")
        if len(value.strip()) < 3 or len(value.strip()) > 50:
            raise ValueError("Input length must be great than 3 and less than 50")
        if not value.replace(" ", "").isalnum():
            raise ValueError("Input must contain alphanumeric words")
        return value.strip()


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