import pytest
from app.utils.utils import validate_color, validate_turn
from app.exceptions import ColorNotValid, TurnsAreEqual
from app.models.enums import Colors

def test_validate_color_valid():
    # Prueba con un color válido
    try:
        validate_color("red")
    except ColorNotValid:
        pytest.fail("validate_color raised ColorNotValid unexpectedly!")

def test_validate_color_invalid():
    # Prueba con un color inválido
    with pytest.raises(ColorNotValid):
        validate_color("black")
        
def test_validate_turn_equal():
    # Prueba cuando current_player y next_player_turn son iguales
    current_player = 1
    next_player_turn = 1
    board_id = 1
    with pytest.raises(TurnsAreEqual):
        validate_turn(current_player, next_player_turn, board_id)

def test_validate_turn_different():
    # Prueba cuando current_player y next_player_turn son diferentes
    current_player = 1
    next_player_turn = 2
    board_id = 1
    try:
        validate_turn(current_player, next_player_turn, board_id)
    except TurnsAreEqual:
        pytest.fail("validate_turn raised TurnsAreEqual unexpectedly!")

def test_validate_turn_edge_case_zero():
    # Prueba con el caso límite cuando current_player y next_player_turn son cero
    current_player = 0
    next_player_turn = 0
    board_id = 1
    with pytest.raises(TurnsAreEqual):
        validate_turn(current_player, next_player_turn, board_id)

def test_validate_turn_edge_case_negative():
    # Prueba con el caso límite cuando current_player y next_player_turn son negativos
    current_player = -1
    next_player_turn = -1
    board_id = 1
    with pytest.raises(TurnsAreEqual):
        validate_turn(current_player, next_player_turn, board_id)
