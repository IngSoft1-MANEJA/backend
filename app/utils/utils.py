import app.exceptions as e
from app.models.enums import *
from app.schemas import Tile
from app.utils.board_shapes_algorithm import Coordinate, Figure, rotate_90_degrees, rotate_180_degrees, rotate_270_degrees

INVALID_CHARACTERS = set("!@#$%^&*()+=[]{}|\\;:'\",<>/?`~")

# Definir rango válido para el número máximo de jugadores
MIN_PLAYERS = 2
MAX_PLAYERS = 4

# Defino tamaño máximo del tablero
BOARD_SIZE_X = 6
BOARD_SIZE_Y = 6
BOARD_SIZE = (BOARD_SIZE_X, BOARD_SIZE_Y)
MAX_SHAPE_CARDS = 50

# Definir colores válidos para el ban
VALID_COLORS = [color.value for color in Colors]
VALID_SHAPES = [shape.value for shape in HardShapes] + [shape.value for shape in EasyShapes]
VALID_MOVEMENTS = [mov.value for mov in Movements]

FIGURE_COORDINATES = {
    "T_90": Figure((Coordinate(3, 0), Coordinate(4, 0), Coordinate(4, 1), Coordinate(4, 2), Coordinate(5, 0))),
    "INVERSE_SNAKE": Figure((Coordinate(4, 0), Coordinate(4, 1), Coordinate(5, 1), Coordinate(5, 2), Coordinate(5, 3))),
    "SNAKE": Figure((Coordinate(4, 2), Coordinate(4, 3), Coordinate(5, 0), Coordinate(5, 1), Coordinate(5, 2))),
    "STAIRS": Figure((Coordinate(3, 0), Coordinate(4, 0), Coordinate(4, 1), Coordinate(5, 1), Coordinate(5, 2))),
    "LINE": Figure((Coordinate(5, 0), Coordinate(5, 1), Coordinate(5, 2), Coordinate(5, 3), Coordinate(5, 4))),
    "L": Figure((Coordinate(3, 0), Coordinate(4, 0), Coordinate(5, 0), Coordinate(5, 1), Coordinate(5, 2))),
    "INVERSE_L_90": Figure((Coordinate(4, 0), Coordinate(4, 1), Coordinate(4, 2), Coordinate(4, 3), Coordinate(5, 3))),
    "L_90": Figure((Coordinate(5, 0), Coordinate(5, 1), Coordinate(5, 2), Coordinate(5, 3), Coordinate(4, 3))),
    "TOILET": Figure((Coordinate(3, 2), Coordinate(4, 0), Coordinate(4, 1), Coordinate(4, 2), Coordinate(5, 1))),
    "Z_90": Figure((Coordinate(3, 2), Coordinate(4, 0), Coordinate(4, 1), Coordinate(4, 2), Coordinate(5, 0))),
    "INVERSE_TOILET": Figure((Coordinate(3, 0), Coordinate(4, 0), Coordinate(4, 1), Coordinate(4, 2), Coordinate(5, 1))),
    "S_90": Figure((Coordinate(3, 0), Coordinate(4, 0), Coordinate(4, 1), Coordinate(4, 2), Coordinate(5, 2))),
    "BATON": Figure((Coordinate(4, 0), Coordinate(4, 1), Coordinate(4, 2), Coordinate(4, 3), Coordinate(5, 2))),
    "INVERSE_BATON": Figure((Coordinate(4, 2), Coordinate(5, 0), Coordinate(5, 1), Coordinate(5, 2), Coordinate(5, 3))),
    "TURTLE": Figure((Coordinate(4, 1), Coordinate(4, 2), Coordinate(5, 0), Coordinate(5, 1), Coordinate(5, 2))),
    "U": Figure((Coordinate(4, 0), Coordinate(4, 2), Coordinate(5, 0), Coordinate(5, 1), Coordinate(5, 2))),
    "PLUS": Figure((Coordinate(3, 1), Coordinate(4, 0), Coordinate(4, 1), Coordinate(4, 2), Coordinate(5, 1))),
    "DOG": Figure((Coordinate(4, 0), Coordinate(4, 1), Coordinate(4, 2), Coordinate(5, 1), Coordinate(5, 2))),
    "MINI_SNAKE": Figure((Coordinate(4, 1), Coordinate(4, 2), Coordinate(5, 1), Coordinate(5, 0))),
    "SQUARE": Figure((Coordinate(4, 0), Coordinate(4, 1), Coordinate(5, 0), Coordinate(5, 1))),
    "INVERSE_MINI_SNAKE": Figure((Coordinate(4, 0), Coordinate(4, 1), Coordinate(5, 1), Coordinate(5, 2))),
    "TRIANGLE": Figure((Coordinate(4, 1), Coordinate(5, 0), Coordinate(5, 1), Coordinate(5, 2))),
    "INVERSE_MINI_L": Figure((Coordinate(4, 0), Coordinate(4, 1), Coordinate(4, 2), Coordinate(5, 2))),
    "MINI_LINE": Figure((Coordinate(5, 0), Coordinate(5, 1), Coordinate(5, 2), Coordinate(5, 3))),
    "MINI_L_90": Figure((Coordinate(4, 2), Coordinate(5, 0), Coordinate(5, 1), Coordinate(5, 2))),
}

ALL_FIGURES = [figure for figure in FIGURE_COORDINATES.values()] + [rotate_90_degrees(figure, (6,6)) for figure in FIGURE_COORDINATES.values()] + [rotate_180_degrees(figure, (6,6)) for figure in FIGURE_COORDINATES.values()] + [rotate_270_degrees(figure, (6,6)) for figure in FIGURE_COORDINATES.values()]

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
        raise e.ShapeCardHandIsFull(player_id)


def validate_turn(current_player: int, next_player_turn: int, board_id: int):
    if current_player == next_player_turn:
        raise e.TurnsAreEqual(board_id)


def validate_board(board_id: int):
    if not board_id:
        raise e.BoardNotFound(board_id)
    
    
def validate_diagonal(tile1: Tile , tile2: Tile):
    if abs(tile1.rowIndex - tile2.rowIndex) == 2 and abs(tile1.columnIndex - tile2.columnIndex) == 2:
        return True
    return False
    
    
def validate_line_between(tile1: Tile, tile2: Tile):
    if tile1.rowIndex == tile2.rowIndex and abs(tile1.columnIndex - tile2.columnIndex) == 2:
        return True
    
    if tile1.columnIndex == tile2.columnIndex and abs(tile1.rowIndex - tile2.rowIndex) == 2:
        return True
    
    return False
    
    
def validate_line(tile1: Tile, tile2: Tile):
    if tile1.rowIndex == tile2.rowIndex and abs(tile1.columnIndex - tile2.columnIndex) == 1:
        return True
    
    if tile1.columnIndex == tile2.columnIndex and abs(tile1.rowIndex - tile2.rowIndex) == 1:
        return True
    
    return False
    
    
def validate_inverse_diagonal(tile1: Tile, tile2: Tile):
    if abs(tile1.rowIndex - tile2.rowIndex) == 1 and abs(tile1.columnIndex - tile2.columnIndex) == 1:
        return True
    
    return False


def validate_inverse_l(tile1: Tile, tile2: Tile):
    if tile1.rowIndex == tile2.rowIndex + 2 and tile1.columnIndex == tile2.columnIndex - 1:
        return True
    
    if tile1.rowIndex == tile2.rowIndex - 1 and tile1.columnIndex == tile2.columnIndex - 2:
        return True
    
    if tile1.rowIndex == tile2.rowIndex - 2 and tile1.columnIndex == tile2.columnIndex + 1:
        return True 
    
    if tile1.rowIndex == tile2.rowIndex + 1 and tile1.columnIndex == tile2.columnIndex + 2:
        return True
    
    return False
   
   
def validate_l(tile1: Tile, tile2: Tile):
    if tile1.rowIndex == tile2.rowIndex + 2 and tile1.columnIndex == tile2.columnIndex + 1:
        return True
    
    if tile1.rowIndex == tile2.rowIndex + 1 and tile1.columnIndex == tile2.columnIndex - 2:
        return True
    
    if tile1.rowIndex == tile2.rowIndex - 2 and tile1.columnIndex == tile2.columnIndex - 1:
        return True 
    
    if tile1.rowIndex == tile2.rowIndex - 1 and tile1.columnIndex == tile2.columnIndex + 2:
        return True
    
    return False

def validate_line_border(tile1: Tile, tile2: Tile):
    if tile1.rowIndex == tile2.rowIndex and (tile1.columnIndex == 0 or tile1.columnIndex == 5 or tile2.columnIndex == 0 or tile2.columnIndex == 5):
        return True
    
    if tile1.columnIndex == tile2.columnIndex and (tile1.rowIndex == 0 or tile1.rowIndex == 5 or tile2.rowIndex == 0 or tile2.rowIndex == 5):
        return True
    
    return False