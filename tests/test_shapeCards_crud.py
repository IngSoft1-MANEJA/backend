import pytest
from sqlalchemy.orm import sessionmaker
from app.database import engine, Init_Session, init_db, delete_db
from app.cruds.shape_card import ShapeCardService
from app.cruds.player import PlayerService
from app.models.models import ShapeCards
import app.exceptions as e

# Configuración de la sesión
Session = sessionmaker(bind=engine)

@pytest.fixture
def session():
    # Creo las tablas
    init_db()
    session = Session()
    yield session
    session.close()

@pytest.fixture
def shape_service(session):
    return ShapeCardService(session)

"""
    Methods for ShapeCardService to test:
        - get_shape_cards
        - create_shape_card
        - get_shape_card_id
        - get_shape_card_by_id
        - update_shape_card
        - delete_shape_card
        - get_shape_cards_by_player
"""

def test_get_shape_cards(shape_service: ShapeCardService):
    shape_cards = shape_service.get_shape_cards()
    assert len(shape_cards) == 0
    try:
        session2 = Session()
        list_shape_cards = [
            {'shape_type': 'circle', 'hard': False, 'visible': True, 'blocked': False, 'player_owner': 1},
            {'shape_type': 'square', 'hard': True, 'visible': False, 'blocked': False, 'player_owner': 2}
        ]
        for shape_card in list_shape_cards:
            new_shape_card = ShapeCards(shape_type=shape_card['shape_type'], is_hard=shape_card['hard'],
                is_visible=shape_card['visible'], is_blocked=shape_card['blocked'], player_owner=shape_card['player_owner'])
            session2.add(new_shape_card)
            session2.commit()
        shape_cards2 = shape_service.get_shape_cards()
        assert len(shape_cards2) == 2
    finally:
        session2.close()
        
def test_create_shape_card(shape_service: ShapeCardService, session):
    number_shape_cards = session.query(ShapeCards).count()
    shape_service.create_shape_card(shape='circle', 
                                    is_hard=False, is_visible=True, 
                                    player_owner=1)
    try:
        session2 = Session()
        new_number_shape_cards = session2.query(ShapeCards).count()
        assert new_number_shape_cards == number_shape_cards + 1
    finally:
        session2.close()

def test_create_shape_card_raises_exception(shape_service: ShapeCardService, session):
    with pytest.raises(e.ShapeNotValid):
        shape_service.create_shape_card(shape='octagono', 
                                        is_hard=False, is_visible=True, 
                                        player_owner=1)

def test_get_shape_card_by_id(shape_service: ShapeCardService, session):
    shape_card = shape_service.create_shape_card(shape='circle', 
                                    is_hard=False, is_visible=True, 
                                    player_owner=1)
    shape_card_id = shape_service.get_shape_card_id(shape_card)
    shape_card2 = shape_service.get_shape_card_by_id(shape_card_id)
    assert shape_card == shape_card2
    
def test_update_shape_card(shape_service: ShapeCardService, session):
    shape_card = shape_service.create_shape_card(shape='circle', 
                                    is_hard=False, is_visible=True, 
                                    player_owner=1)
    shape_card_id = shape_service.get_shape_card_id(shape_card)
    shape_service.update_shape_card(shape_card_id, is_visible=False, 
                                    is_blocked=True)
    shape_card2 = shape_service.get_shape_card_by_id(shape_card_id)
    assert shape_card2.is_visible == False
    assert shape_card2.is_blocked == True

def test_delete_shape_card(shape_service: ShapeCardService, session):
    shape_card = shape_service.create_shape_card(shape='circle', 
                                    is_hard=False, is_visible=True, 
                                    player_owner=1)
    number_shape_cards = session.query(ShapeCards).count()
    shape_card_id = shape_service.get_shape_card_id(shape_card)
    shape_service.delete_shape_card(shape_card_id)
    try:
        session2 = Session()
        new_number_shape_cards = session2.query(ShapeCards).count()
        assert new_number_shape_cards == number_shape_cards - 1
    finally:
        session2.close()

def test_add_shape_card_to_player(shape_service: ShapeCardService, session):
    shape_card = shape_service.create_shape_card(shape='circle', 
                                    is_hard=False, is_visible=True, 
                                    player_owner=1)
    shape_card_id = shape_service.get_shape_card_id(shape_card)
    player_service = PlayerService(session)
    player = player_service.create_player('Test Player', 1, True, 'token1235')
    player_id = player_service.get_player_id(player)
    shape_service.add_shape_card_to_player(player_id, shape_card_id)
    shape_card2 = shape_service.get_shape_card_by_id(shape_card_id)
    assert shape_card2.player_owner == player_id
    
def test_get_shape_cards_by_player(shape_service: ShapeCardService, session):
    shape_card = shape_service.create_shape_card(shape='circle', 
                                    is_hard=False, is_visible=True, 
                                    player_owner=1)
    player_service = PlayerService(session)
    player = player_service.create_player('Test Player', 1, True, 'token123')
    player_id = player_service.get_player_id(player)
    shape_card_id = shape_service.get_shape_card_id(shape_card)
    shape_service.add_shape_card_to_player(player_id, shape_card_id)
    shape_cards = shape_service.get_shape_card_by_player(player_id)
    assert len(shape_cards) == 1
    assert shape_cards[0] == shape_card
    assert shape_cards[0].player_owner == player_id
    assert shape_cards[0].id == shape_card_id
    assert shape_cards[0].shape_type == 'circle'
    assert shape_cards[0].is_hard == False
    assert shape_cards[0].is_visible == True
    assert shape_cards[0].is_blocked == False
    assert shape_cards[0].player_owner == player_id