import re
import app.exceptions as e

# Definir caracteres inválidos para nombres de partidas
INVALID_CHARACTERS = set("!@#$%^&*()+=[]{}|\\;:'\",<>/?`~")

# Definir rango válido para el número máximo de jugadores
MIN_PLAYERS = 2
MAX_PLAYERS = 10

# Defino tamaño máximo del tablero
BOARD_SIZE_X = 6
BOARD_SIZE_Y = 6

# Definir colores válidos para el ban
VALID_COLORS = {"red", "blue", "green", "yellow"}

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
    