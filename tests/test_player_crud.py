import pytest
from sqlalchemy.orm import sessionmaker
from app.database import engine, Init_Session, init_db, delete_db
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.models.models import Matches, Players
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
def player_service(session):
    return PlayerService(session)

"""
    Methods for PlayerService to test:
        - get_players
        - create_player
        - get_player_id
        - get_player_by_id
        - update_player
        - delete_player (The client does not want to delete players, but it can be added)
"""

def test_get_players(player_service: PlayerService, session):
    players = player_service.get_players()
    assert len(players) == 0
    try: 
        session2 = Session()
        list_players = [
            {'name': 'Player 1', 'match_to_link': 3,
                'owner': True, 'token': 'token1', 'turn_order': 2},
            {'name': 'Player 2', 'match_to_link': 3,
                'owner': False, 'token': 'token2', 'turn_order': 1}
        ]
        for player in list_players:
            new_player = Players(player_name=player['name'], match_id=player['match_to_link'],
                is_owner=player['owner'], session_token=player['token'], turn_order=player['turn_order'])
            session2.add(new_player)
            session2.commit()
        players2 = player_service.get_players()
        assert len(players2) == 2
    finally:
        session2.close()
        
def test_create_player(player_service: PlayerService, session):
    number_players = session.query(Players).count()
    player_service.create_player('Test Player', 1, True, 'token123')
    try:
        session2 = Session()
        new_number_players = session2.query(Players).count()
    finally:
        session2.close()
    assert new_number_players == number_players + 1

def test_create_player_raises_exception(player_service: PlayerService):
    with pytest.raises(e.PlayerNameInvalid):
        player_service.create_player('M@nuel', 1, True, 'token123')
    
def test_get_player_id(player_service: PlayerService, session):
    player = player_service.create_player('Test-Player-Id', 1, True, 'tokenid1')
    # obtengo el id del player recién creado
    player_id = session.query(Players).filter(Players.player_name == 'Test-Player-Id').first().id
    # obtengo el id del player usando el servicio
    player_id2 = player_service.get_player_id(player)
    # Verifico que el id del player devuelto es el esperado
    assert player_id == player_id2
    
def test_get_player_by_id(player_service: PlayerService, session):
    player = player_service.create_player('Test-Player-GetId', 1, True, 'tokenid1')
    # obtengo el id del player recién creado
    player_id = player_service.get_player_id(player)
    # obtengo el player usando el servicio
    player2 = player_service.get_player_by_id(player_id)
    # Verifico que los valores del diccionario devuelto son los esperados
    assert player == player2

def test_update_player(player_service: PlayerService, session):
    player = player_service.create_player('Test-Player-Update', 1, True, 'tokenid341')
    # obtengo el id del player recién creado
    player_id = player_service.get_player_id(player)
    # actualizo el player
    player_service.update_player_with_match(player_id, 2)
    player_service.update_turn_order(player_id, 4)
    # chequeo que el player se haya actualizado
    player_get = player_service.get_player_by_id(player_id)
    assert player_get.match_id == 2
    assert player_get.turn_order == 4

def test_delete_player(player_service: PlayerService, session):
    match = MatchService(session)
    match.create_match('Test-Match-Delete', 3, True)
    player = player_service.create_player('Test-Player-Delete', 1, True, 'tokenidelete1')
    number_players = session.query(Players).count()
    player_id = player_service.get_player_id(player)
    player_service.delete_player(player_id)
    try:
        session2 = Session()
        new_number_players = session2.query(Players).count()
    finally:
        session2.close()
    assert new_number_players == number_players - 1