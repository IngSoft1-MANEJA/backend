import pytest
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from app.database import Init_Session, init_db
from app.models.models import Matches, Players, Boards, Tiles, ShapeCards, MovementCards

@pytest.fixture(scope="module")
def db():
    # inicializo la database
    init_db()
    db = Init_Session()
    yield db
    db.close()


def test_create_tables(db: Session):
    # chequeo si se crearon las tablas
    inspector = inspect(db.get_bind())
    tables = inspector.get_table_names()
    assert "players" in tables
    assert "shapeCards" in tables  # Cambiado a minúsculas
    assert "movementCards" in tables  # Cambiado a minúsculas
    assert "matches" in tables
    assert "boards" in tables
    assert "tiles" in tables


def test_relationships(db: Session):
    # creo un match
    match = Matches(match_name="Test Match", started=False,
                    is_public=True, max_players=4, current_player_turn=1)
    db.add(match)
    db.commit()
    db.refresh(match)

    # creo un jugador
    player = Players(player_name="Test Player",
                     is_owner=True, session_token="token123",
                     match_id=match.id, turn_order=1)
    db.add(player)
    db.commit()
    db.refresh(player)

    # creo un tablero
    board = Boards(ban_color="red", match_id=match.id)
    db.add(board)
    db.commit()
    db.refresh(board)

    # creo una ficha
    tile = Tiles(color="red", positionX=0, positionY=0, board_id=board.id)
    db.add(tile)
    db.commit()
    db.refresh(tile)

    # creo una carta de figura y una de movimiento
    shape_card = ShapeCards(shape_type="circle",
                            is_hard=False, is_visible=True, is_blocked=False,
                            player_owner=player.id)
    movement_card = MovementCards(mov_type="up", player_owner=player.id)

    db.add(shape_card)
    db.add(movement_card)
    db.commit()
    db.refresh(shape_card)
    db.refresh(movement_card)

    # Verificar las relaciones
    # match.players es una lista de jugadores
    assert match.players[0].id == player.id
    # player.match es el match al que pertenece el jugador
    assert player.match.id == match.id
    assert match.board.id == board.id  # match.board es el tablero del match
    # board.match es el match al que pertenece el tablero
    assert board.match.id == match.id
    # tile.board es el tablero al que pertenece la ficha
    assert tile.board.id == board.id
    assert board.tiles[0].id == tile.id  # board.tiles es una lista de fichas
    assert shape_card.owner.id == player.id
    assert movement_card.owner.id == player.id
    assert player.shape_cards[0].id == shape_card.id
    assert player.movement_cards[0].id == movement_card.id
