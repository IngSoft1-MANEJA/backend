import pytest
from sqlalchemy.orm import sessionmaker

from app.database import engine, Init_Session, init_db, delete_db
from app.models.models import Boards
from app.cruds.board import BoardService
import app.exceptions as e

Session = sessionmaker(bind=engine)

@pytest.fixture
def session():
    # Creo las tablas
    init_db()
    session = Session()
    yield session
    session.close()
    delete_db

@pytest.fixture
def board_service(session):
    return BoardService(session)

def test_get_all_boards(board_service : BoardService, session):
    assert session.query(Boards).count() == 0
    board1 = board_service.create_board(match_id = 1, ban_color = "green")
    session.add(board1)
    expected = session.query(Boards).count()
    assert expected == 1
    board2 = board_service.create_board(match_id = 2, ban_color = "red")
    session.add(board2)
    expected2 = session.query(Boards).count()
    assert expected2 == 2
    
def test_create_board(board_service : BoardService, session):
    currently = session.query(Boards).count() 
    board = board_service.create_board(match_id = 1)
    assert session.query(Boards).count() == currently + 1
    
def test_get_board_by_id(board_service : BoardService, session):
    board1 = board_service.create_board(match_id = 1, ban_color = "green")
    session.add(board1)
    assert board_service.get_board_by_id(board_id = 1).ban_color == board1.ban_color
    board2 = board_service.create_board(match_id = 2, ban_color = "red")
    session.add(board2)
    assert board_service.get_board_by_id(board_id = 2).ban_color == board2.ban_color
    assert board_service.get_board_by_id(board_id = 1).ban_color == board1.ban_color

def test_update_ban_color_valid(board_service, session):
    # Crear un tablero
    board = board_service.create_board(match_id = 1, ban_color = "red")
    assert session.query(Boards).filter(Boards.id == board.id).one().ban_color == "red"
    # Actualizar el color del ban con un color válido
    board_service.update_ban_color(board_id=board.id, ban_color="green")
    
    # Verificar que el color del ban se haya actualizado correctamente
    updated_board = session.query(Boards).filter(Boards.id == board.id).one()
    assert updated_board.ban_color == "green"

def test_update_ban_color_invalid(board_service, session):
    # Crear un tablero
    board = board_service.create_board(match_id = 1, ban_color = "red")
    # Intentar actualizar el color del ban con un color inválido
    with pytest.raises(e.ColorNotValid):
        board_service.update_ban_color(board_id=board.id, ban_color="black")

def test_update_ban_color_nonexistent_board(board_service, session):
    # Intentar actualizar el color del ban de un tablero que no existe
    with pytest.raises(Exception):  # Puedes especificar una excepción más específica si es necesario
        board_service.update_ban_color(board_id=999, ban_color="green") 
        
def test_update_turn_valid(board_service, session):
    # Crear un tablero
    board = board_service.create_board(match_id = 1, current_player = 1, next_player_turn = 2)
    # Actualizar el turno del tablero
    board_service.update_turn(board_id=board.id, current_player= 2, next_player_turn= 3)
    # Verificar que el turno se haya actualizado correctamente
    updated_board = session.query(Boards).filter(Boards.id == board.id).one()
    assert updated_board.current_player == 2

def test_update_turn_nonexistent_board(board_service):
    # Intentar actualizar el turno de un tablero que no existe
    with pytest.raises(Exception):  # Puedes especificar una excepción más específica si es necesario
        board_service.update_turn(board_id=999, current_player= 2, next_player_turn= 3)