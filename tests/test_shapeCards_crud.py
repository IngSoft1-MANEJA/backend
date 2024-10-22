import pytest
from sqlalchemy.orm.exc import NoResultFound

from app.cruds.shape_card import ShapeCardService
from app.cruds.player import PlayerService
from app.models.models import ShapeCards
import app.exceptions as e


def test_get_shape_cards(shape_service: ShapeCardService, db_session):
    shape_cards = shape_service.get_shape_cards()
    assert len(shape_cards) == 0
    try:
        list_shape_cards = [
            {'shape_type': 1, 'hard': False, 'visible': True,
                'blocked': False, 'player_owner': 1},
            {'shape_type': 3, 'hard': True, 'visible': False,
                'blocked': False, 'player_owner': 2}
        ]
        for shape_card in list_shape_cards:
            new_shape_card = ShapeCards(shape_type=shape_card['shape_type'], is_hard=shape_card['hard'],
                                        is_visible=shape_card['visible'], is_blocked=shape_card['blocked'], player_owner=shape_card['player_owner'])
            db_session.add(new_shape_card)
            db_session.commit()
        shape_cards2 = shape_service.get_shape_cards()
        assert len(shape_cards2) == 2
    finally:
        db_session.close()


def test_create_shape_card(shape_service: ShapeCardService, db_session):
    number_shape_cards = db_session.query(ShapeCards).count()
    shape_service.create_shape_card(shape=5,
                                    is_hard=False, is_visible=True,
                                    player_owner=1)
    try:
        new_number_shape_cards = db_session.query(ShapeCards).count()
        assert new_number_shape_cards == number_shape_cards + 1
    finally:
        db_session.close()


def test_create_shape_card_raises_exception(shape_service):
    with pytest.raises(e.ShapeNotValid):
        shape_service.create_shape_card(shape=27,
                                        is_hard=False, is_visible=True,
                                        player_owner=1)


def test_get_shape_card_by_id(shape_service: ShapeCardService):
    shape_card = shape_service.create_shape_card(shape=5,
                                                 is_hard=False, is_visible=True,
                                                 player_owner=1)
    shape_card_id = shape_service.get_shape_card_id(shape_card)
    shape_card2 = shape_service.get_shape_card_by_id(shape_card_id)
    assert shape_card == shape_card2


def test_update_shape_card(shape_service: ShapeCardService):
    shape_card = shape_service.create_shape_card(
        shape=15, is_hard=False, is_visible=True, player_owner=1)
    shape_card_id = shape_service.get_shape_card_id(shape_card)
    shape_service.update_shape_card(shape_card_id, is_visible=False,
                                    is_blocked=True)
    shape_card2 = shape_service.get_shape_card_by_id(shape_card_id)
    assert shape_card2.is_visible == False
    assert shape_card2.is_blocked == True


def test_delete_shape_card(shape_service: ShapeCardService, db_session):
    shape_card = shape_service.create_shape_card(shape=1,
                                                 is_hard=False, is_visible=True,
                                                 player_owner=1)
    number_shape_cards = db_session.query(ShapeCards).count()
    shape_card_id = shape_service.get_shape_card_id(shape_card)
    shape_service.delete_shape_card(shape_card_id)

    new_number_shape_cards = db_session.query(ShapeCards).count()
    assert new_number_shape_cards == number_shape_cards - 1


def test_add_shape_card_to_player(shape_service: ShapeCardService, db_session):
    shape_card = shape_service.create_shape_card(shape=3,
                                                 is_hard=False, is_visible=True,
                                                 player_owner=1)
    shape_card_id = shape_service.get_shape_card_id(shape_card)
    player_service = PlayerService(db_session)
    player = player_service.create_player('Test Player', 1, True, 'token1235')
    player_id = player_service.get_player_id(player)
    shape_service.add_shape_card_to_player(player_id, shape_card_id)
    shape_card2 = shape_service.get_shape_card_by_id(shape_card_id)
    assert shape_card2.player_owner == player_id


def test_get_shape_cards_by_player(shape_service: ShapeCardService, db_session):
    shape_card = shape_service.create_shape_card(shape=3,
                                                 is_hard=False, is_visible=True,
                                                 player_owner=1)
    player_service = PlayerService(db_session)
    player = player_service.create_player('Test Player', 1, True, 'token123')
    player_id = player_service.get_player_id(player)
    shape_card_id = shape_service.get_shape_card_id(shape_card)
    shape_service.add_shape_card_to_player(player_id, shape_card_id)
    shape_cards = shape_service.get_shape_card_by_player(player_id)
    assert len(shape_cards) == 1
    assert shape_cards[0] == shape_card
    assert shape_cards[0].player_owner == player_id
    assert shape_cards[0].id == shape_card_id
    assert shape_cards[0].shape_type == 3
    assert shape_cards[0].is_hard == False
    assert shape_cards[0].is_visible == True
    assert shape_cards[0].is_blocked == False
    assert shape_cards[0].player_owner == player_id


def test_update_shape_card(shape_service: ShapeCardService, db_session):
    shape_card = shape_service.create_shape_card(shape=15, is_hard=True, is_visible= False, player_owner=1)
    shape_card_id = shape_service.get_shape_card_id(shape_card)

    shape_service.update_shape_card(shape_card_id, is_visible= True, is_blocked=False)

    shape_card2 = shape_service.get_shape_card_by_id(shape_card_id)

    assert shape_card2.is_visible == True
    assert shape_card2.is_blocked == False 
    
    shape_service.update_shape_card(shape_card_id, is_visible= True, is_blocked= True)

    shape_card3 = shape_service.get_shape_card_by_id(shape_card_id)

    assert shape_card3.is_visible == True
    assert shape_card3.is_blocked == True 
    

def test_update_shape_card_not_found(shape_service: ShapeCardService):
    shape_card_id = 999  # ID que no existe
    is_visible = True
    is_blocked = False
    
    with pytest.raises(NoResultFound, match=f"ShapeCard with id {shape_card_id} not found, can't update"):
        shape_service.update_shape_card(shape_card_id, is_visible, is_blocked)
      
        
def test_get_visible_cards(shape_service: ShapeCardService, db_session):
    player_id = 1
    
    visible_cards = shape_service.get_visible_cards(player_id, True)
    assert len(visible_cards) == 0
    
    shape_card1 = shape_service.create_shape_card(
        shape=3, is_hard=False, is_visible=True, player_owner=player_id)
    shape_card2 = shape_service.create_shape_card(
        shape=5, is_hard=True, is_visible=True, player_owner=player_id)
    shape_card3 = shape_service.create_shape_card(
        shape=7, is_hard=False, is_visible=False, player_owner=player_id)

    visible_cards = shape_service.get_visible_cards(player_id, True)
    
    assert len(visible_cards) == 2
    assert shape_card1 in visible_cards
    assert shape_card2 in visible_cards
    assert shape_card3 not in visible_cards

    
def test_get_visible_cards_not_found(shape_service: ShapeCardService):
    player_id = 999  # ID que no existe

    # Verificar que la lista de cartas visibles está vacía
    visible_cards = shape_service.get_visible_cards(player_id, True)
    assert len(visible_cards) == 0