from typing import List, Self
import logging
from pydantic import BaseModel, field_validator, model_validator

logger = logging.getLogger(__name__)

INVALID_CHARACTERS = set("!@#$%^&*()+=[]{}|\\;:'\",<>/?`~")


class MatchCreateIn(BaseModel):
    lobby_name: str
    is_public: bool = True
    password: str = ""
    max_players: int
    player_name: str
    token: str


    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        if value.strip() is "":
            return value.strip()
        if any(char in INVALID_CHARACTERS for char in value):
            raise ValueError("Input can't contain special characters")
        if len(value.strip()) < 3 or len(value.strip()) > 50:
            raise ValueError("Input length must be great than 3 and less than 50")
        if not value.replace(" ", "").isalnum():
            raise ValueError("Input must contain alphanumeric words")
        return value.strip()
    

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
    

    @model_validator(mode="after")
    def set_is_public(self) -> Self:
        if self.password.strip() != "":
            self.is_public = False
        return self
    

class MatchOut(BaseModel):
    id: int
    match_name: str
    is_public: bool
    state: str
    max_players: int
    current_players: int

    model_config = {'from_attributes': True}


class MatchCreateOut(MatchOut):
    player_name: str


class PlayerJoinIn(BaseModel):
    player_name: str
    password: str = ""

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
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        if value.strip() is "":
            return value.strip()
        if any(char in INVALID_CHARACTERS for char in value):
            raise ValueError("Input can't contain special characters")
        if len(value.strip()) < 3 or len(value.strip()) > 50:
            raise ValueError("Input length must be great than 3 and less than 50")
        if not value.replace(" ", "").isalnum():
            raise ValueError("Input must contain alphanumeric words")
        return value.strip()



class PlayerJoinOut(BaseModel):
    player_id: int
    players: list[str]


class Tile(BaseModel):
    rowIndex: int
    columnIndex: int


class PartialMove(BaseModel):
    tiles: List[Tile]
    movement_card: int

class UseFigure(BaseModel):
    figure_id: int
    coordinates: list[tuple]