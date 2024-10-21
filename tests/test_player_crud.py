import pytest
from sqlalchemy.orm.exc import NoResultFound

from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.models.models import Players, Matches
import app.exceptions as e


def test_get_players(player_service: PlayerService, db_session):
    players = player_service.get_players()
    assert len(players) == 0
    list_players = [
        {'name': 'Player 1', 'match_to_link': 3, 'owner': True, 'token': 'token1', 'turn_order': 2},
        {'name': 'Player 2', 'match_to_link': 3, 'owner': False, 'token': 'token2', 'turn_order': 1}
    ]
    for player in list_players:
        new_player = Players(player_name=player['name'], match_id=player['match_to_link'],
                             is_owner=player['owner'], session_token=player['token'], turn_order=player['turn_order'])
        db_session.add(new_player)
        db_session.commit()
    players2 = player_service.get_players()
    assert len(players2) == 2


def test_create_player(player_service: PlayerService, db_session):
    number_players = db_session.query(Players).count()
    player_service.create_player('Test Player', 1, True, 'token123')
    new_number_players = db_session.query(Players).count()
    assert new_number_players == number_players + 1


def test_create_player_raises_exception(player_service: PlayerService):
    with pytest.raises(e.PlayerNameInvalid):
        player_service.create_player('M@nuel', 1, True, 'token123')


def test_get_player_id(player_service: PlayerService, db_session):
    player = player_service.create_player(
        'Test-Player-Id', 1, True, 'tokenid1')
    # obtengo el id del player recién creado
    player_id = db_session.query(Players).filter(
        Players.player_name == 'Test-Player-Id').first().id
    # obtengo el id del player usando el servicio
    player_id2 = player_service.get_player_id(player)
    # Verifico que el id del player devuelto es el esperado
    assert player_id == player_id2


def test_get_player_by_id(player_service: PlayerService):
    player = player_service.create_player(
        'Test-Player-GetId', 1, True, 'tokenid1')
    # obtengo el id del player recién creado
    player_id = player_service.get_player_id(player)
    # obtengo el player usando el servicio
    player2 = player_service.get_player_by_id(player_id)
    # Verifico que los valores del diccionario devuelto son los esperados
    assert player == player2


def test_update_player(player_service: PlayerService):
    player = player_service.create_player(
        'Test-Player-Update', 1, True, 'tokenid341')
    # obtengo el id del player recién creado
    player_id = player_service.get_player_id(player)
    # actualizo el player
    player_service.update_player_with_match(player_id, 2)
    player_service.update_turn_order(player_id, 4)
    # chequeo que el player se haya actualizado
    player_get = player_service.get_player_by_id(player_id)
    assert player_get.match_id == 2
    assert player_get.turn_order == 4


def test_delete_player(player_service: PlayerService, db_session):
    match = MatchService(db_session)
    match.create_match('Test-Match-Delete', 3, True)
    player = player_service.create_player(
        'Test-Player-Delete', 1, True, 'tokenidelete1')
    number_players = db_session.query(Players).count()
    player_id = player_service.get_player_id(player)
    player_service.delete_player(player_id)
    new_number_players = db_session.query(Players).count()
    assert new_number_players == number_players - 1

def test_get_players_by_match(player_service: PlayerService, match_service: MatchService, db_session):
    # Crear un match y jugadores
    match = match_service.create_match('Test-Match', 3, True)
    players = player_service.get_players_by_match(match.id)
    print("1", players)
    player1 = player_service.create_player('Player1', match.id, False, 'token')
    player2 = player_service.create_player('Player2', match.id, False, 'token2')
    
    # Obtener la lista de jugadores por match_id
    players = player_service.get_players_by_match(match.id)
    print(players)
    # Verificar que la lista de jugadores es correcta
    assert len(players) == 2
    assert players[0].id == player1.id
    assert players[1].id == player2.id

def test_get_players_by_match_no_players(player_service: PlayerService, match_service: MatchService, db_session):
    # Crear un match sin jugadores
    match = match_service.create_match('Test-Match-No-Players', 3, True)
    
    # Obtener la lista de jugadores por match_id
    players1 = player_service.get_players_by_match(match.id)
    print("a", players1)
    # Verificar que la lista de jugadores está vacía
    assert len(players1) == 0

def test_update_turn_success(db_session, match_service: MatchService):
    # Crear un match para la prueba
    match_service.create_match('test_match', 4, True)
    match = db_session.query(Matches).filter(Matches.match_name == 'test_match').one()
    
    # Actualizar el turno del match
    new_turn = 2
    match_service.update_turn(match.id, new_turn)
    
    # Verificar que el turno se ha actualizado correctamente
    updated_match = db_session.query(Matches).filter(Matches.id == match.id).one()
    assert updated_match.current_player_turn == new_turn

def test_update_turn_failure(db_session, match_service: MatchService):
    # Intentar actualizar el turno de un match que no existe
    non_existent_match_id = 9999
    new_turn = 2
    
    with pytest.raises(NoResultFound):
        match_service.update_turn(non_existent_match_id, new_turn)