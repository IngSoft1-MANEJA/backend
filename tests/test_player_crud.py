import pytest
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.models.models import Players
import app.exceptions as e
from tests.config import *


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
