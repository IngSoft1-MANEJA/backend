import pytest
from sqlalchemy.orm import sessionmaker

from app.database import engine, Init_Session, init_db, delete_db
from app.models import MovementCards
from app.cruds.movement_card import MovementCardService
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
def movement_card_service(session):
    return MovementCardService(session)

def test_create_movement_card_valid(movement_card_service : MovementCardService, session):
    currently = session.query(MovementCards).count()
    movement_card = movement_card_service.create_movement_card(mov_type='up', player_owner=1)
    assert session.query(MovementCards).count() == currently + 1
    currently = session.query(MovementCards).count()
    movement_card = movement_card_service.create_movement_card(mov_type='up')
    assert session.query(MovementCards).count() == currently + 1

def test_create_movement_card_invalid_movement(movement_card_service : MovementCardService, session):
    with pytest.raises(e.MoveNotValid):
        movement_card_service.create_movement_card(mov_type='out')
    with pytest.raises(e.MoveNotValid):
        movement_card_service.create_movement_card(mov_type='aaaa')
    with pytest.raises(e.MoveNotValid):
        movement_card_service.create_movement_card(mov_type='upside')
    with pytest.raises(e.MoveNotValid):
        movement_card_service.create_movement_card(mov_type='downside')
        
def test_get_all_movement_cards_empty(movement_card_service : MovementCardService, session):
    assert session.query(MovementCards).count() == 0
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.get_movement_cards()

def test_get_all_movement_cards(movement_card_service : MovementCardService, session):
    before = session.query(MovementCards).count() 
    movement_card1 = movement_card_service.create_movement_card(mov_type='up', player_owner=1)
    expected = session.query(MovementCards).count()
    assert expected == before + 1
    before = session.query(MovementCards).count() 
    movement_card2 = movement_card_service.create_movement_card(mov_type='left', player_owner=2)
    expected2 = session.query(MovementCards).count()
    assert expected2 == before + 1
    
def test_get_movement_card_by_id_valid(movement_card_service : MovementCardService, session):
    movement_card1 = movement_card_service.create_movement_card(mov_type='up', player_owner=1)
    assert movement_card_service.get_movement_card_by_id(movement_card_id=1).mov_type == movement_card1.mov_type
    movement_card2 = movement_card_service.create_movement_card(mov_type='left', player_owner=2)
    assert movement_card_service.get_movement_card_by_id(movement_card_id=2).mov_type == movement_card2.mov_type
    
def test_get_movement_card_by_id_invalid(movement_card_service : MovementCardService, session):
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.get_movement_card_by_id(movement_card_id=1)
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.get_movement_card_by_id(movement_card_id=2)
        
def test_get_movement_card_by_user_valid(movement_card_service : MovementCardService, session):
    movement_card1 = movement_card_service.create_movement_card(mov_type='up', player_owner=1)
    assert movement_card_service.get_movement_card_by_user(player_owner=1)[0].mov_type == movement_card1.mov_type
    movement_card2 = movement_card_service.create_movement_card(mov_type='left', player_owner=2)
    assert movement_card_service.get_movement_card_by_user(player_owner=2)[0].mov_type == movement_card2.mov_type
    
def test_get_movement_card_by_user_invalid(movement_card_service : MovementCardService, session):
    with pytest.raises(e.NoMovementCardsFound):
        movement_card_service.get_movement_card_by_user(player_owner=1)

def test_delete_movement_card_from_user_valid(movement_card_service : MovementCardService, session):
    movement_card1 = movement_card_service.create_movement_card(mov_type='up', player_owner=1)
    movement_card2 = movement_card_service.create_movement_card(mov_type='left', player_owner=2)
    assert session.query(MovementCards).count() == 2
    movement_card_service.delete_movement_card_from_user(player_owner=1)
    assert session.query(MovementCards).count() == 1
    movement_card_service.delete_movement_card_from_user(player_owner=2)
    assert session.query(MovementCards).count() == 0
    
def test_delete_movement_card_from_user_invalid(movement_card_service : MovementCardService, session):
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.delete_movement_card_from_user(player_owner=1)
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.delete_movement_card_from_user(player_owner=2)

def test_delete_movement_card_valid(movement_card_service, session):
    movement_card1 = movement_card_service.create_movement_card(mov_type='up', player_owner=1)
    movement_card2 = movement_card_service.create_movement_card(mov_type='left', player_owner=2)
    assert session.query(MovementCards).count() == 2
    movement_card_service.delete_movement_card(movement_card_id=movement_card1.id)
    assert session.query(MovementCards).count() == 1
    movement_card_service.delete_movement_card(movement_card_id=movement_card2.id)
    assert session.query(MovementCards).count() == 0
    
def test_delete_movement_card_invalid(movement_card_service, session):
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.delete_movement_card(movement_card_id=1)
    with pytest.raises(e.MovementCardNotFound):
        movement_card_service.delete_movement_card(movement_card_id=2)
