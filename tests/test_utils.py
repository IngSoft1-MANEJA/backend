import pytest
from app.utils.utils import *
from app.exceptions import ColorNotValid, TurnsAreEqual

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


def test_validate_figures():
    # El primero es row, el segundo es column
    assert validate_diagonal(Tile(rowIndex=0, columnIndex=0), Tile(rowIndex=2, columnIndex=2))
    assert validate_diagonal(Tile(rowIndex=2, columnIndex=2), Tile(rowIndex=0, columnIndex=0))
    assert validate_diagonal(Tile(rowIndex=5, columnIndex=5), Tile(rowIndex=3, columnIndex=3))
    assert validate_diagonal(Tile(rowIndex=3, columnIndex=3), Tile(rowIndex=5, columnIndex=5))
    assert validate_diagonal(Tile(rowIndex=3, columnIndex=5), Tile(rowIndex=5, columnIndex=3))
    assert validate_diagonal(Tile(rowIndex=4, columnIndex=2), Tile(rowIndex=2, columnIndex=4))
    assert validate_diagonal(Tile(rowIndex=2, columnIndex=4), Tile(rowIndex=4, columnIndex=2))
    assert validate_diagonal(Tile(rowIndex=4, columnIndex=2), Tile(rowIndex=2, columnIndex=0))
    assert validate_diagonal(Tile(rowIndex=2, columnIndex=0), Tile(rowIndex=4, columnIndex=2))
    
    assert not validate_diagonal(Tile(rowIndex=0, columnIndex=0), Tile(rowIndex=2, columnIndex=3))
    assert not validate_diagonal(Tile(rowIndex=0, columnIndex=0), Tile(rowIndex=0, columnIndex=3))
    assert not validate_diagonal(Tile(rowIndex=3, columnIndex=4), Tile(rowIndex=5, columnIndex=3))
    assert not validate_diagonal(Tile(rowIndex=0, columnIndex=0), Tile(rowIndex=3, columnIndex=3))
    assert not validate_diagonal(Tile(rowIndex=0, columnIndex=0), Tile(rowIndex=1, columnIndex=1))
    assert not validate_diagonal(Tile(rowIndex=3, columnIndex=3), Tile(rowIndex=2, columnIndex=2))
    
    assert validate_line_between(Tile(rowIndex=2, columnIndex=4), Tile(rowIndex=4, columnIndex=4))
    assert validate_line_between(Tile(rowIndex=2, columnIndex=4), Tile(rowIndex=2, columnIndex=2))
    assert validate_line_between(Tile(rowIndex=2, columnIndex=4), Tile(rowIndex=0, columnIndex=4))
    assert validate_line_between(Tile(rowIndex=2, columnIndex=3), Tile(rowIndex=2, columnIndex=5))
    assert validate_line_between(Tile(rowIndex=4, columnIndex=4), Tile(rowIndex=2, columnIndex=4))
    assert validate_line_between(Tile(rowIndex=2, columnIndex=2), Tile(rowIndex=2, columnIndex=4))
    assert validate_line_between(Tile(rowIndex=0, columnIndex=4), Tile(rowIndex=2, columnIndex=4))
    assert validate_line_between(Tile(rowIndex=3, columnIndex=5), Tile(rowIndex=3, columnIndex=3))
    
    assert not validate_line_between(Tile(rowIndex=2, columnIndex=4), Tile(rowIndex=4, columnIndex=3))
    assert not validate_line_between(Tile(rowIndex=5, columnIndex=5), Tile(rowIndex=4, columnIndex=4))
    assert not validate_line_between(Tile(rowIndex=3, columnIndex=3), Tile(rowIndex=3, columnIndex=0))
    assert not validate_line_between(Tile(rowIndex=2, columnIndex=4), Tile(rowIndex=4, columnIndex=2))
    assert not validate_line_between(Tile(rowIndex=2, columnIndex=2), Tile(rowIndex=2, columnIndex=5))
    
    assert validate_line(Tile(rowIndex=0, columnIndex=0), Tile(rowIndex=0, columnIndex=1))
    assert validate_line(Tile(rowIndex=0, columnIndex=1), Tile(rowIndex=0, columnIndex=0))
    assert validate_line(Tile(rowIndex=1, columnIndex=1), Tile(rowIndex=1, columnIndex=2))
    assert validate_line(Tile(rowIndex=1, columnIndex=2), Tile(rowIndex=1, columnIndex=1))
    assert validate_line(Tile(rowIndex=2, columnIndex=2), Tile(rowIndex=3, columnIndex=2))
    assert validate_line(Tile(rowIndex=3, columnIndex=2), Tile(rowIndex=2, columnIndex=2))
    assert validate_line(Tile(rowIndex=3, columnIndex=3), Tile(rowIndex=2, columnIndex=3))
    assert validate_line(Tile(rowIndex=2, columnIndex=3), Tile(rowIndex=3, columnIndex=3))
    
    assert not validate_line(Tile(rowIndex=0, columnIndex=0), Tile(rowIndex=1, columnIndex=1))
    assert not validate_line(Tile(rowIndex=1, columnIndex=1), Tile(rowIndex=2, columnIndex=3))
    assert not validate_line(Tile(rowIndex=2, columnIndex=2), Tile(rowIndex=4, columnIndex=2))
    assert not validate_line(Tile(rowIndex=3, columnIndex=3), Tile(rowIndex=3, columnIndex=5))

    assert validate_inverse_diagonal(Tile(rowIndex=0, columnIndex=0), Tile(rowIndex=1, columnIndex=1))
    assert validate_inverse_diagonal(Tile(rowIndex=2, columnIndex=1), Tile(rowIndex=3, columnIndex=2))
    assert validate_inverse_diagonal(Tile(rowIndex=1, columnIndex=2), Tile(rowIndex=2, columnIndex=3))
    assert validate_inverse_diagonal(Tile(rowIndex=3, columnIndex=3), Tile(rowIndex=2, columnIndex=2))
    assert validate_inverse_diagonal(Tile(rowIndex=1, columnIndex=1), Tile(rowIndex=0, columnIndex=0))
    assert validate_inverse_diagonal(Tile(rowIndex=3, columnIndex=2), Tile(rowIndex=2, columnIndex=1))
    assert validate_inverse_diagonal(Tile(rowIndex=2, columnIndex=3), Tile(rowIndex=1, columnIndex=2))
    assert validate_inverse_diagonal(Tile(rowIndex=4, columnIndex=4), Tile(rowIndex=3, columnIndex=3))
 
    assert validate_l(Tile(rowIndex= 2, columnIndex= 2), Tile(rowIndex= 4, columnIndex= 3))
    assert validate_l(Tile(rowIndex= 2, columnIndex= 2), Tile(rowIndex= 3, columnIndex= 0))
    assert validate_l(Tile(rowIndex= 2, columnIndex= 2), Tile(rowIndex= 0, columnIndex= 1))
    assert validate_l(Tile(rowIndex= 2, columnIndex= 2), Tile(rowIndex= 1, columnIndex= 4))
    assert validate_l(Tile(rowIndex= 4, columnIndex= 3), Tile(rowIndex= 2, columnIndex= 2))
    assert validate_l(Tile(rowIndex= 3, columnIndex= 0), Tile(rowIndex= 2, columnIndex= 2))
    assert validate_l(Tile(rowIndex= 0, columnIndex= 1), Tile(rowIndex= 2, columnIndex= 2))
    assert validate_l(Tile(rowIndex= 1, columnIndex= 4), Tile(rowIndex= 2, columnIndex= 2))
    
    assert validate_inverse_l(Tile(rowIndex= 2, columnIndex= 2), Tile(rowIndex= 4, columnIndex= 1))
    assert validate_inverse_l(Tile(rowIndex= 2, columnIndex= 2), Tile(rowIndex= 1, columnIndex= 0))
    assert validate_inverse_l(Tile(rowIndex= 2, columnIndex= 2), Tile(rowIndex= 0, columnIndex= 3))
    assert validate_inverse_l(Tile(rowIndex= 2, columnIndex= 2), Tile(rowIndex= 3, columnIndex= 4))
    assert validate_inverse_l(Tile(rowIndex= 4, columnIndex= 1), Tile(rowIndex= 2, columnIndex= 2))
    assert validate_inverse_l(Tile(rowIndex= 1, columnIndex= 0), Tile(rowIndex= 2, columnIndex= 2))
    assert validate_inverse_l(Tile(rowIndex= 0, columnIndex= 3), Tile(rowIndex= 2, columnIndex= 2))
    assert validate_inverse_l(Tile(rowIndex= 3, columnIndex= 4), Tile(rowIndex= 2, columnIndex= 2))
    
    assert validate_line_border(Tile(rowIndex=0, columnIndex=0), Tile(rowIndex=0, columnIndex=5))
    assert validate_line_border(Tile(rowIndex=0, columnIndex=5), Tile(rowIndex=0, columnIndex=0))
    assert validate_line_border(Tile(rowIndex=5, columnIndex=0), Tile(rowIndex=5, columnIndex=4))
    assert validate_line_border(Tile(rowIndex=5, columnIndex=4), Tile(rowIndex=5, columnIndex=0))
    assert validate_line_border(Tile(rowIndex=2, columnIndex=0), Tile(rowIndex=5, columnIndex=0))
    assert validate_line_border(Tile(rowIndex=5, columnIndex=0), Tile(rowIndex=2, columnIndex=0))
    assert validate_line_border(Tile(rowIndex=3, columnIndex=5), Tile(rowIndex=0, columnIndex=5))
    assert validate_line_border(Tile(rowIndex=0, columnIndex=5), Tile(rowIndex=3, columnIndex=5))
