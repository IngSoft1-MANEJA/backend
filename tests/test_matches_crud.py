import pytest
from sqlalchemy.orm import sessionmaker
from app.database import engine, Init_Session, init_db, delete_db
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.models.models import Matches, Players
import app.exceptions as e
from app.models.enums import MatchState

# Configuración de la sesión
Session = sessionmaker(bind=engine)

@pytest.fixture
def session():
    # Creo las 
    init_db()
    session = Session()
    yield session
    session.close()
    
@pytest.fixture
def match_service(session):
    return MatchService(session)

#================================================= MATCH SERVICE TESTS =================================================
"""
    Methods for MatchService to test:
        - get_all_matches
        - create_match
        - get_match_id
        - get_match_by_id
        - update_match
        - delete_match (The client does not want to delete matches, but it can be added)
        
"""
def test_get_matches(match_service: MatchService):
    matches = match_service.get_all_matches()
    assert len(matches) == 0 # Check if the list of matches is empty
    try:
        session2 = Session()
        list_matches = [
            {'name': 'Match 1', 'max_players': 4, 'public': True},
            {'name': 'Match 2', 'max_players': 4, 'public': False},
            {'name': 'Match 3', 'max_players': 4, 'public': True}
        ]
        for match in list_matches:
            new_match = Matches(match_name=match['name'], max_players=match['max_players'], 
                    is_public=match['public'], state=MatchState.WAITING.value, current_players=0)
            session2.add(new_match)
            session2.commit()
        matches2 = match_service.get_all_matches()
        assert len(matches2) == 3 # Check if the list of matches is 3 next to adding 3 matches
    finally:
        session2.close()

def test_delete_match(match_service: MatchService, session):
    match = match_service.create_match('Test Match', 4, public=True)
    number_matches = session.query(Matches).count()
    match_id = match_service.get_match_id(match)
    match_service.delete_match(match_id)
    try:
        session2 = Session()
        new_number_matches = session2.query(Matches).count()
    finally:
        session2.close()
    assert new_number_matches == number_matches - 1

def test_create_match(match_service: MatchService, session):
    number_matches = session.query(Matches).count()
    match_service.create_match('Test Match', 4, public=True)
    try:
        session2 = Session()
        new_number_matches = session2.query(Matches).count()
    finally:
        session2.close()
    assert new_number_matches == number_matches + 1
    
def test_get_match_id(match_service: MatchService, session):
    match = match_service.create_match('Test-Match-Id', 4, public=True)
    # Obtener el ID del match recién creado
    match_id = session.query(Matches).filter(Matches.match_name == 'Test-Match-Id').first().id
    # Obtener el ID del match usando el servicio
    match_id2 = match_service.get_match_id(match)
    # Verificar que el ID del match devuelto es el esperado
    assert match_id == match_id2

def test_get_match_by_id(match_service: MatchService, session):
    match = match_service.create_match('Test-Match-Id', 4, public=True)
    # Obtener el ID del match recién creado
    match_id = match_service.get_match_id(match)
    # Obtener el match usando el servicio
    match2 = match_service.get_match_by_id(match_id)
    # Verificar que los valores del diccionario devuelto son los esperados
    assert match == match2
    
def test_update_match(match_service: MatchService, session):
    match = match_service.create_match('Test-Match-Update', 4, public=True)
    # Obtener el ID del match recién creado
    match_id = match_service.get_match_id(match)
    # Actualizar el match
    match_service.update_match(match_id, new_state= MatchState.WAITING.value, new_amount_players= 2)
    # chequeo que el match se haya actualizado
    match_info = match_service.get_match_by_id(match_id)
    assert match_info.current_players == 2
    assert match_info.state == MatchState.WAITING.value
