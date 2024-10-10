import pytest

from app.models.models import Boards
from app.cruds.board import BoardService
import app.exceptions as e
from tests.config import *

def test_get_all_boards(board_service: BoardService, db_session):
    assert db_session.query(Boards).count() == 0
    board1 = board_service.create_board(match_id=1, ban_color="green")
    db_session.add(board1)
    expected = db_session.query(Boards).count()
    assert expected == 1
    board2 = board_service.create_board(match_id=2, ban_color="red")
    db_session.add(board2)
    expected2 = db_session.query(Boards).count()
    assert expected2 == 2


def test_create_board(board_service: BoardService, db_session):
    currently = db_session.query(Boards).count()
    board = board_service.create_board(match_id=1)
    assert db_session.query(Boards).count() == currently + 1


def test_get_board_by_id(board_service: BoardService, db_session):
    board1 = board_service.create_board(match_id=1, ban_color="green")
    db_session.add(board1)
    assert board_service.get_board_by_id(
        board_id=1).ban_color == board1.ban_color
    board2 = board_service.create_board(match_id=2, ban_color="red")
    db_session.add(board2)
    assert board_service.get_board_by_id(
        board_id=2).ban_color == board2.ban_color
    assert board_service.get_board_by_id(
        board_id=1).ban_color == board1.ban_color


def test_update_ban_color_valid(board_service, db_session):
    # Crear un tablero
    board = board_service.create_board(match_id=1, ban_color="red")
    assert db_session.query(Boards).filter(
        Boards.id == board.id).one().ban_color == "red"
    # Actualizar el color del ban con un color válido
    board_service.update_ban_color(board_id=board.id, ban_color="green")

    # Verificar que el color del ban se haya actualizado correctamente
    updated_board = db_session.query(Boards).filter(Boards.id == board.id).one()
    assert updated_board.ban_color == "green"


def test_update_ban_color_invalid(board_service, db_session):
    # Crear un tablero
    board = board_service.create_board(match_id=1, ban_color="red")
    # Intentar actualizar el color del ban con un color inválido
    with pytest.raises(e.ColorNotValid):
        board_service.update_ban_color(board_id=board.id, ban_color="black")


def test_update_ban_color_nonexistent_board(board_service, db_session):
    # Intentar actualizar el color del ban de un tablero que no existe
    with pytest.raises(Exception):  # Puedes especificar una excepción más específica si es necesario
        board_service.update_ban_color(board_id=999, ban_color="green") 
        
def test_update_turn_nonexistent_board(board_service):
    # Intentar actualizar el turno de un tablero que no existe
    # Puedes especificar una excepción más específica si es necesario
    with pytest.raises(Exception):
        board_service.update_turn(
            board_id=999, current_player=2, next_player_turn=3)
