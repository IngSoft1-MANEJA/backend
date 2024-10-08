import re
import app.exceptions as e
from app.models.enums import Movements, Colors, Shapes
# Definir caracteres inválidos para nombres de partidas
INVALID_CHARACTERS = set("!@#$%^&*()+=[]{}|\\;:'\",<>/?`~")

# Definir rango válido para el número máximo de jugadores
MIN_PLAYERS = 2
MAX_PLAYERS = 4

# Defino tamaño máximo del tablero
BOARD_SIZE_X = 6
BOARD_SIZE_Y = 6

# Definir colores válidos para el ban
VALID_COLORS = Colors._value2member_map_.keys()
VALID_SHAPES = Shapes._value2member_map_.keys()
VALID_MOVEMENTS = Movements._value2member_map_.keys()

def validate_match_name(name: str):
    if any(char in INVALID_CHARACTERS for char in name):
        raise e.MatchNameInvalid(name)
    if len(name) < 3 or len(name) > 50:
        raise e.MatchNameInvalid(name)

def validate_max_players(max_players: int):
    if not (MIN_PLAYERS <= max_players <= MAX_PLAYERS):
        raise e.MatchMaxPlayersInvalid(max_players)

def validate_player_name(name: str):
    if any(char in INVALID_CHARACTERS for char in name):
        raise e.PlayerNameInvalid(name)
    if len(name) < 3 or len(name) > 50:
        raise e.PlayerNameInvalid(name)

def validate_color(color: str):
    if color not in VALID_COLORS:
        raise e.ColorNotValid(color)

def validate_position(x: int, y: int):
    if x < 0 or x >= BOARD_SIZE_X or y < 0 or y >= BOARD_SIZE_Y:
        raise e.TilePositionIsInvalid(x, y)

def validate_shape(shape: str):
    if shape not in VALID_SHAPES:
        raise e.ShapeNotValid(shape)

def validate_movement(movement: str):
    if movement not in VALID_MOVEMENTS:
        raise e.MoveNotValid(movement)
    
def validate_add_shape_card_to_hand(player_id: int, count_cards: int):
    if count_cards > 3:
        raise e.HandIsFull(player_id)

def validate_turn(current_player: int, next_player_turn: int, board_id: int):
    if current_player == next_player_turn:
        raise e.TurnsAreEqual(board_id)

def validate_board(board_id: int):
    if not board_id:
        raise e.BoardNotFound(board_id)