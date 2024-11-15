from random import seed
from unittest import mock
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from fastapi import status
from unittest.mock import AsyncMock, patch, MagicMock

from app.cruds.board import BoardService
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.cruds.movement_card import MovementCardService
from app.models import Matches, Players, MovementCards
from app.connection_manager import manager
from app.models.models import Boards, Tiles
from app.routers.players import (give_movement_card_to_player, 
                                 notify_movement_card_to_player, 
                                 give_shape_card_to_player)

def test_create_match(client, db_session):
    response = client.post(
        "/matches/",
        json={
            "lobby_name": "Test Lobby",
            "max_players": 4,
            "is_public": True,
            "player_name": "Test Player",
            "token": "testtoken"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "player_id" in data
    assert "match_id" in data
    assert "token" in data

    # Verifica que el match y el player se hayan creado en la base de datos
    match = db_session.query(Matches).filter(
        Matches.id == data["match_id"]).first()
    assert match is not None
    assert match.match_name == "Test Lobby"
    assert match.max_players == 4
    assert match.is_public is True

    player = db_session.query(Players).filter(
        Players.id == data["player_id"]).first()
    assert player is not None
    assert player.player_name == "Test Player"
    assert player.match_id == match.id
    assert player.is_owner is True
    assert player.session_token == data["token"]


def test_create_match_invalid_data(client):
    # Prueba con datos inválidos
    response = client.post(
        "/matches/",
        json={
            "lobby_name": "",
            "max_players": -1,
            "is_public": "not_a_boolean",
            "player_name": "",
            "token": ""
        }
    )
    assert response.status_code == 422  # Unprocessable Entity


def test_join_match_success(client, load_matches, db_session):
    manager.create_game_connection(3)
    match = db_session.query(Matches).filter(Matches.id == 3).first()
    current_players = match.current_players
    response = client.post("/matches/3", json={"player_name": "Player 4", "password":"AAA"})
    assert response.status_code == status.HTTP_200_OK
    match = db_session.query(Matches).filter(Matches.id == 3).first()
    assert match.current_players == current_players + 1

def test_join_match_not_found(client):
    response = client.post("/matches/99", json={"player_name": "Player 4"})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_join_match_is_full(client):
    with mock.patch("app.cruds.match.MatchService.get_match_by_id", return_value=MagicMock(current_players=2, max_players=2)):
        response = client.post("/matches/1", json={"player_name": "Player 3"})
    assert response.status_code == status.HTTP_409_CONFLICT

def test_join_match_with_invalid_password(client):
    with mock.patch("app.cruds.match.MatchService.get_match_by_id", return_value=MagicMock(current_players=2, max_players=3, is_public=False, password="AAA")):
        response = client.post("/matches/1", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_join_match_with_incorrect_password(client):
    with mock.patch("app.cruds.match.MatchService.get_match_by_id", return_value=MagicMock(current_players=2, max_players=3, is_public=False, password="AAA")):
        response = client.post("/matches/1", json={"player_name": "Player 3", "password": "BBB"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_start_match_success(client, load_matches):
    manager.create_game_connection(1)
    with client.websocket_connect("/matches/1/ws/1") as ws1, client.websocket_connect("/matches/1/ws/2") as ws2, patch("app.routers.players.turn_timeout") as mock_turn_timeout:
        response = client.patch("/matches/1/start/1")
        assert response.status_code == 200
        data = ws1.receive_json()
        assert data['key'] == "START_MATCH"
        data = ws2.receive_json()
        assert data['key'] == "START_MATCH"

def test_start_match_not_enough_players(client, load_data_for_test):
    manager.create_game_connection(1)
    with client.websocket_connect("/matches/1/ws/1") as ws1:
        response = client.patch("/matches/1/start/1")
        assert response.status_code == 404

def test_create_movement_deck_success(client, load_matches, movement_card_service, db_session):
    match = db_session.query(Matches).filter(Matches.id == 1).first()
    movement_card_service.create_movement_deck(match.id)
    assert len(match.movement_cards) == 49
    
def test_create_movement_deck_invalid(client, load_matches, movement_card_service, db_session):
    with pytest.raises(Exception):
        movement_card_service.create_movement_deck(999999)

@pytest.mark.asyncio
async def test_notify_movement_card_to_player():
    player_id = 1
    match_id = 1
    buff_movement = [(1, "move")]

    msg_user = {
        "key": "GET_MOVEMENT_CARD",
        "payload": {"movement_card": buff_movement}
    }

    with patch('app.routers.matches.manager.send_to_player', new_callable=AsyncMock) as mock_send_to_player:
        await notify_movement_card_to_player(player_id, match_id, buff_movement)
        mock_send_to_player.assert_called_once_with(match_id, player_id, msg_user)

@pytest.mark.asyncio
async def test_give_shape_card_to_player_initial():
    db_session = MagicMock(spec=Session)
    player_id = 1
    is_init = True

    player = MagicMock(id=player_id, player_name="Player1", turn_order=1, match_id=1)
    shape_card_service = MagicMock()
    shape_card_service.get_visible_cards.return_value = []
    shape_card_service.get_visible_cards.return_value = [MagicMock(id=1, shape_type="circle")]

    with patch('app.routers.players.PlayerService.get_player_by_id', return_value=player), \
         patch('app.routers.players.ShapeCardService', return_value=shape_card_service), \
         patch('app.routers.players.manager.broadcast_to_game', new_callable=AsyncMock) as mock_broadcast_to_game:
        
        await give_shape_card_to_player(player_id, db_session, is_init)
        
        shape_card_service.update_shape_card.assert_called_once()
        mock_broadcast_to_game.assert_not_called()

@pytest.mark.asyncio
async def test_give_shape_card_to_player_non_initial():
    db_session = MagicMock(spec=Session)
    player_id = 1
    is_init = False

    player = MagicMock(id=player_id, player_name="Player1", turn_order=1, match_id=1)
    shape_card_service = MagicMock()
    shape_card_service.get_visible_cards.return_value = []
    shape_card_service.get_visible_cards.return_value = [MagicMock(id=1, shape_type="circle")]

    with patch('app.routers.players.PlayerService.get_player_by_id', return_value=player), \
         patch('app.routers.players.ShapeCardService', return_value=shape_card_service), \
         patch('app.routers.players.manager.broadcast_to_game', new_callable=AsyncMock) as mock_broadcast_to_game:
        
        await give_shape_card_to_player(player_id, db_session, is_init)
        
        shape_card_service.update_shape_card.assert_called_once()
        mock_broadcast_to_game.assert_called_once()
    
def test_give_movement_card_to_player_enough_cards():
    db_session = MagicMock(spec=Session)
    player_id = 1

    player = MagicMock(id=player_id, player_name="Player1", match_id=1, movement_cards=[])
    movement_card = MagicMock(id=1, mov_type="move")

    with patch('app.routers.matches.PlayerService.get_player_by_id', return_value=player), \
         patch('app.routers.matches.MovementCardService.get_movement_cards_without_owner', return_value=[movement_card] * 3), \
         patch('app.routers.matches.MovementCardService.add_movement_card_to_player') as mock_add_movement_card_to_player:
        
        movements_given = give_movement_card_to_player(player_id, db_session)
        
        assert len(movements_given) == 3
        mock_add_movement_card_to_player.assert_called_with(player_id, movement_card.id)

def test_give_movement_card_to_player_no_cards():
    db_session = MagicMock(spec=Session)
    player_id = 1

    player = MagicMock(id=player_id, player_name="Player1", match_id=1, movement_cards=[])
    movement_card = MagicMock(id=1, mov_type="move")

    with patch('app.routers.matches.PlayerService.get_player_by_id', return_value=player), \
            patch('app.routers.matches.MovementCardService.get_movement_cards_without_owner', return_value=[]), \
            patch('app.routers.matches.MovementCardService.add_movement_card_to_player') as mock_add_movement_card_to_player:
        
        movements_given = give_movement_card_to_player(player_id, db_session)
        
        assert len(movements_given) == 0
        mock_add_movement_card_to_player.assert_not_called()

@pytest.mark.asyncio
async def test_start_match_success2(client, db_session):
    match_id = 1
    player_id = 1

    match = MagicMock(id=match_id, current_players=4, max_players=4, state="WAITING", players=[MagicMock(id=2), MagicMock(id=3), MagicMock(id=4)])
    player = MagicMock(id=player_id, is_owner=True, match_id=match_id)

    with patch('app.routers.matches.MatchService.get_match_by_id', return_value=match), \
         patch('app.routers.matches.PlayerService.get_player_by_id', return_value=player), \
         patch('app.routers.matches.MovementCardService.create_movement_deck'), \
         patch('app.routers.matches.ShapeCardService.create_shape_card'), \
         patch('app.routers.matches.BoardService.create_board', return_value=MagicMock(id=1)), \
         patch('app.routers.matches.BoardService.init_board'), \
         patch('app.routers.matches.MatchService.set_players_order'), \
         patch('app.routers.matches.manager.send_to_player', new_callable=AsyncMock) as mock_send_to_player, \
         patch('app.routers.matches.give_movement_card_to_player'), \
         patch('app.routers.matches.give_shape_card_to_player', new_callable=AsyncMock), \
         patch("app.routers.matches.turn_timeout") as turn_timeout:

        response = client.patch(f"/matches/{match_id}/start/{player_id}")
        assert response.status_code == status.HTTP_200_OK

        # Verificar que el estado del match se haya actualizado
        assert match.state == "STARTED"

        