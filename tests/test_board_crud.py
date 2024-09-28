import pytest
from sqlalchemy.orm import sessionmaker
from app.database import engine, Init_Session, init_db, delete_db
from app.cruds.tile import TileService
from app.cruds.board import BoardService
from app.models.models import Tiles, Boards
import app.exceptions as e

# Configuración de la sesión
Session = sessionmaker(bind=engine)

@pytest.fixture
def session():
    # Creo las tablas
    # init_db()
    session = Session()
    yield session
    session.close()
    delete_db
    
@pytest.fixture
def board_service(session):
    return BoardService(session)
    
@pytest.fixture
def tile_service(session):
    return TileService(session)

def test_create_board(board_service: BoardService):
    boards = board_service.get_all_boards()
    assert len(boards) == 0 # Check if the list of boards is empty
    try:
        session2 = Session()
        list_boards = [
            {'match_id': 1, 'current_player_turn': 1, 'next_player_turn': 2},
            {'match_id': 2, 'current_player_turn': 2, 'next_player_turn': 3},
            {'match_id': 3, 'current_player_turn': 3, 'next_player_turn': 4}
        ]
        for board in list_boards:
            new_board = Boards(match_id=board['match_id'], 
                               current_player_turn=board['current_player_turn'],
                               next_player_turn=board['next_player_turn']) 
            session2.add(new_board)
            session2.commit()
        boards2 = board_service.get_all_boards()
        assert len(boards2) == 3 # Check if the list of boards is 3 next to adding 3 boards
    except Exception as e:
        raise e




""" def test_get_tiles(tile_service: TileService):
    tiles = tile_service.get_all_tiles()
    assert len(tiles) == 0 # Check if the list of tiles is empty
    try:
        session2 = Session()
        list_tiles = [
            {'board_id': 1, 'color': 'red', 'position_x': 1, 'position_y': 1},
            {'board_id': 1, 'color': 'blue', 'position_x': 2, 'position_y': 2},
            {'board_id': 1, 'color': 'green', 'position_x': 3, 'position_y': 3}
        ]
        for tile in list_tiles:
            new_tile = Tiles(board_id=tile['board_id'], color=tile['color'], 
                    positionX=tile['position_x'], positionY=tile['position_y'])
            session2.add(new_tile)
            session2.commit()
        tiles2 = tile_service.get_all_tiles()
        assert len(tiles2) == 3 # Check if the list of tiles is 3 next to adding 3 tiles
    except Exception as e:
        raise e """