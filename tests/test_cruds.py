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
    delete_db
    
@pytest.fixture
def match_service(session):
    return MatchService(session)

@pytest.fixture
def player_service(session):
    return PlayerService(session)

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
                    is_public=match['public'], started=False, amount_players=0)
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
    print(match2['id'])
    assert match2['id'] == match_id
    assert match2['match_name'] == match.match_name
    assert match2['started'] == match.started
    assert match2['is_public'] == match.is_public
    assert match2['max_players'] == match.max_players
    assert match2['amount_players'] == match.amount_players
    
def test_update_match(match_service: MatchService, session):
    match = match_service.create_match('Test-Match-Update', 4, public=True)
    # Obtener el ID del match recién creado
    match_id = match_service.get_match_id(match)
    # Actualizar el match
    match_service.update_match(match_id, is_started= False, new_amount_players= 2)
    # chequeo que el match se haya actualizado
    match_info = match_service.get_match_by_id(match_id)
    assert match_info['amount_players'] == 2
    assert match_info['started'] == False
    
#================================================ PLAYER SERVICE TESTS ================================================
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
    assert player2['id'] == player_id
    assert player2['player_name'] == player.player_name
    assert player2['is_owner'] == player.is_owner
    assert player2['session_token'] == player.session_token
    assert player2['turn_order'] == player.turn_order

def test_update_player(player_service: PlayerService, session):
    player = player_service.create_player('Test-Player-Update', 1, True, 'tokenid341')
    # obtengo el id del player recién creado
    player_id = player_service.get_player_id(player)
    # actualizo el player
    player_service.update_player_with_match(player_id, 2)
    player_service.update_turn_order(player_id, 4)
    # chequeo que el player se haya actualizado
    player_get = player_service.get_player_by_id(player_id)
    assert player_get['match_id'] == 2
    assert player_get['turn_order'] == 4

def test_delete_player(player_service: PlayerService, session):
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
    
# ================================================= TILE SERVICE TESTS =================================================
