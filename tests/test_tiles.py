import pytest
from sqlalchemy.orm import sessionmaker

from app.database import init_db, delete_db, Init_Session, engine
from app.models import Tiles
from app.cruds.tile import TileService
import app.exceptions as e

Session = sessionmaker(bind=engine)

@pytest.fixture
def session():
    # Creo las tablas
    init_db()
    session = Session()
    yield session
    session.close()
    delete_db()
    
@pytest.fixture
def tile_service(session):
    return TileService(session)

def test_create_tile_valid(tile_service : TileService, session):
    currently = session.query(Tiles).count()
    tile = tile_service.create_tile(board_id=1, color="red", position_x=1, position_y=1)
    assert session.query(Tiles).count() == currently + 1

def test_create_tile_invalid_color(tile_service : TileService, session):
    with pytest.raises(e.ColorNotValid):
        tile_service.create_tile(board_id=1, color="black", position_x=1, position_y=1)
        
def test_create_tile_invalid_position(tile_service : TileService, session):
    with pytest.raises(e.TilePositionIsInvalid):
        tile_service.create_tile(board_id=1, color="red", position_x=-1, position_y=1)
    with pytest.raises(e.TilePositionIsInvalid):
        tile_service.create_tile(board_id=1, color="red", position_x=1, position_y=-1)
    with pytest.raises(e.TilePositionIsInvalid):
        tile_service.create_tile(board_id=1, color="red", position_x=3, position_y=6)
    with pytest.raises(e.TilePositionIsInvalid):
        tile_service.create_tile(board_id=1, color="red", position_x=6, position_y=3)

def test_get_all_tiles_empty(tile_service : TileService, session):
    assert session.query(Tiles).count() == 0
    with pytest.raises(e.NoTilesFound):
        tile_service.get_all_tiles()

def test_get_all_tiles(tile_service : TileService, session):
    before = session.query(Tiles).count() 
    tile1 = tile_service.create_tile(board_id=1, color="red", position_x=1, position_y=1)
    expected = session.query(Tiles).count()
    assert expected == before + 1
    before = session.query(Tiles).count() 
    tile2 = tile_service.create_tile(board_id=2, color="green", position_x=2, position_y=2)
    expected2 = session.query(Tiles).count()
    assert expected2 == before + 1
    
def test_get_tile_by_id_valid(tile_service : TileService, session):
    tile1 = tile_service.create_tile(board_id=1, color="red", position_x=1, position_y=1)
    assert tile_service.get_tile_by_id(tile_id=1).color == tile1.color
    assert tile_service.get_tile_by_id(tile_id=1).position_x == tile1.position_x
    assert tile_service.get_tile_by_id(tile_id=1).position_y == tile1.position_y
    tile2 = tile_service.create_tile(board_id=2, color="green", position_x=2, position_y=2)
    assert tile_service.get_tile_by_id(tile_id=2).color == tile2.color
    assert tile_service.get_tile_by_id(tile_id=2).position_x == tile2.position_x
    assert tile_service.get_tile_by_id(tile_id=2).position_y == tile2.position_y
    assert tile_service.get_tile_by_id(tile_id=1).color == tile1.color
    assert tile_service.get_tile_by_id(tile_id=1).position_x == tile1.position_x
    assert tile_service.get_tile_by_id(tile_id=1).position_y == tile1.position_y
    
def test_get_tile_by_id_invalid(tile_service : TileService, session):
    with pytest.raises(e.TileNotFound):
        tile_service.get_tile_by_id(tile_id=1)

def test_update_tile_position_valid(tile_service, session):
    tile = tile_service.create_tile(board_id=1, color="red", position_x=1, position_y=1)
    assert session.query(Tiles).filter(Tiles.id == tile.id).one().position_x == 1
    assert session.query(Tiles).filter(Tiles.id == tile.id).one().position_y == 1
    tile_service.update_tile_position(tile_id=tile.id, position_x=2, position_y=2)
    updated_tile = session.query(Tiles).filter(Tiles.id == tile.id).one()
    assert updated_tile.position_x == 2
    assert updated_tile.position_y == 2
    
def test_update_tile_position_invalid(tile_service : TileService, session):
    tile = tile_service.create_tile(board_id=1, color="red", position_x=1, position_y=1)
    with pytest.raises(e.TilePositionIsInvalid):
        tile_service.update_tile_position(tile_id=tile.id, position_x=-1, position_y=1)
    with pytest.raises(e.TilePositionIsInvalid):
        tile_service.update_tile_position(tile_id=tile.id, position_x=1, position_y=-1)
    with pytest.raises(e.TilePositionIsInvalid):
        tile_service.update_tile_position(tile_id=tile.id, position_x=3, position_y=6)
    with pytest.raises(e.TilePositionIsInvalid):
        tile_service.update_tile_position(tile_id=tile.id, position_x=6, position_y=3)
        
def test_delete_tile (tile_service : TileService, session):
    tile = tile_service.create_tile(board_id=1, color="red", position_x=1, position_y=1)
    before = session.query(Tiles).count()
    tile_service.delete_tile(tile_id=1)
    expected = session.query(Tiles).count()
    assert expected == before - 1
    with pytest.raises(e.TileNotFound):
        tile_service.get_tile_by_id(tile_id=1)