from app.models import MovementCards
from app.cruds.movement_card import MovementCardService
import app.exceptions as e
from app.models.enums import Movements
from tests.config import *


def test_create_movement_card_valid(movement_card_service: MovementCardService, db_session):
    currently = db_session.query(MovementCards).count()
    movement_card = movement_card_service.create_movement_card(
        mov_type=Movements.DIAGONAL.value, player_owner=1)
    assert db_session.query(MovementCards).count() == currently + 1
    currently = db_session.query(MovementCards).count()
    movement_card = movement_card_service.create_movement_card(
        mov_type=Movements.L.value)
    assert db_session.query(MovementCards).count() == currently + 1


def test_create_movement_card_invalid_movement(movement_card_service: MovementCardService):
    with pytest.raises(e.MoveNotValid):
        movement_card_service.create_movement_card(mov_type='out')
    with pytest.raises(e.MoveNotValid):
        movement_card_service.create_movement_card(mov_type='aaaa')
    with pytest.raises(e.MoveNotValid):
        movement_card_service.create_movement_card(mov_type='upside')
    with pytest.raises(e.MoveNotValid):
        movement_card_service.create_movement_card(mov_type='downside')


def test_get_all_movement_cards_empty(movement_card_service: MovementCardService, db_session):
    assert db_session.query(MovementCards).count() == 0
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.get_movement_cards()


def test_get_all_movement_cards(movement_card_service: MovementCardService, db_session):
    before = db_session.query(MovementCards).count()
    movement_card1 = movement_card_service.create_movement_card(
        mov_type=Movements.L.value, player_owner=1)
    expected = db_session.query(MovementCards).count()
    assert expected == before + 1
    before = db_session.query(MovementCards).count()
    movement_card2 = movement_card_service.create_movement_card(
        mov_type=Movements.LINE_BETWEEN.value, player_owner=2)
    expected2 = db_session.query(MovementCards).count()
    assert expected2 == before + 1


def test_get_movement_card_by_id_valid(movement_card_service: MovementCardService):
    movement_card1 = movement_card_service.create_movement_card(
        mov_type=Movements.LINE_BETWEEN.value, player_owner=1)
    assert movement_card_service.get_movement_card_by_id(
        movement_card_id=1).mov_type == movement_card1.mov_type
    movement_card2 = movement_card_service.create_movement_card(
        mov_type=Movements.LINE.value, player_owner=2)
    assert movement_card_service.get_movement_card_by_id(
        movement_card_id=2).mov_type == movement_card2.mov_type


def test_get_movement_card_by_id_invalid(movement_card_service: MovementCardService):
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.get_movement_card_by_id(movement_card_id=1)
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.get_movement_card_by_id(movement_card_id=2)


def test_get_movement_card_by_user_valid(movement_card_service: MovementCardService):
    movement_card1 = movement_card_service.create_movement_card(
        mov_type=Movements.LINE_BETWEEN.value, player_owner=1)
    assert movement_card_service.get_movement_card_by_user(
        player_owner=1)[0].mov_type == movement_card1.mov_type
    movement_card2 = movement_card_service.create_movement_card(
        mov_type=Movements.DIAGONAL.value, player_owner=2)
    assert movement_card_service.get_movement_card_by_user(
        player_owner=2)[0].mov_type == movement_card2.mov_type


def test_get_movement_card_by_user_invalid(movement_card_service: MovementCardService):
    with pytest.raises(e.NoMovementCardsFound):
        movement_card_service.get_movement_card_by_user(player_owner=1)


def test_delete_movement_card_from_user_valid(movement_card_service: MovementCardService, db_session):
    movement_card1 = movement_card_service.create_movement_card(
        mov_type=Movements.DIAGONAL.value, player_owner=1)
    movement_card2 = movement_card_service.create_movement_card(
        mov_type=Movements.L.value, player_owner=2)
    assert db_session.query(MovementCards).count() == 2
    movement_card_service.delete_movement_card_from_user(player_owner=1)
    assert db_session.query(MovementCards).count() == 1
    movement_card_service.delete_movement_card_from_user(player_owner=2)
    assert db_session.query(MovementCards).count() == 0


def test_delete_movement_card_from_user_invalid(movement_card_service: MovementCardService, db_session):
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.delete_movement_card_from_user(player_owner=1)
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.delete_movement_card_from_user(player_owner=2)


def test_delete_movement_card_valid(movement_card_service: MovementCardService, db_session):
    movement_card1 = movement_card_service.create_movement_card(
        mov_type=Movements.LINE_BETWEEN.value, player_owner=1)
    movement_card2 = movement_card_service.create_movement_card(
        mov_type=Movements.INVERSE_DIAGONAL.value, player_owner=2)
    assert db_session.query(MovementCards).count() == 2
    movement_card_service.delete_movement_card(
        movement_card_id=movement_card1.id)
    assert db_session.query(MovementCards).count() == 1
    movement_card_service.delete_movement_card(
        movement_card_id=movement_card2.id)
    assert db_session.query(MovementCards).count() == 0


def test_delete_movement_card_invalid(movement_card_service: MovementCardService):
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.delete_movement_card(movement_card_id=1)
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.delete_movement_card(movement_card_id=2)
