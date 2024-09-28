import pytest
from sqlalchemy.orm import sessionmaker
from app.database import engine, Init_Session, init_db, delete_db
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.models.models import Matches, Players

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
def match_service(session):
    return MatchService(session)

@pytest.fixture
def player_service(session):
    return PlayerService(session)

#================================================= MATCH SERVICE TESTS =================================================
def test_get_matches(match_service: MatchService):
    matches = match_service.get_all_matches()
    assert len(matches) == 0

def test_create_match(match_service: MatchService, session):
    number_matches = session.query(Matches).count()
    match_service.create_match('Test Match', 4, public=True)
    try:
        session2 = Session()
        new_number_matches = session2.query(Matches).count()
    finally:
        session2.close()
    assert new_number_matches == number_matches + 1

#================================================ PLAYER SERVICE TESTS ================================================
def test_get_players(player_service: PlayerService, session):
    players = player_service.get_players()
    assert len(players) == 0
        
def test_create_player(player_service: PlayerService, session):
    number_players = session.query(Players).count()
    player_service.create_player('Test Player', 1, True, 'token123')
    try:
        session2 = Session()
        new_number_players = session2.query(Players).count()
    finally:
        session2.close()
    assert new_number_players == number_players + 1