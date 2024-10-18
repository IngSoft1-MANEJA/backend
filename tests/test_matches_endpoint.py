from random import seed
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session
from fastapi import status
from unittest.mock import AsyncMock, patch, MagicMock

from app.cruds.board import BoardService
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.cruds.movement_card import MovementCardService
from app.models import Matches, Players, MovementCards
from app.connection_manager import manager
from app.models.models import Boards, Tiles
from app.routers.matches import (create_movement_deck, 
                                 give_movement_card_to_player, 
                                 notify_movement_card_to_player, 
                                 notify_all_players_movements_received, 
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
    assert response.status_code == 200
    data = response.json()
    assert "player_id" in data
    assert "match_id" in data

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
    assert player.session_token == "testtoken"


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


def test_get_matches(client):
    response = client.get("/matches/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_match_by_id(client):
    # Primero, crea un match para obtener su ID
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
    assert response.status_code == 200
    data = response.json()
    match_id = data["match_id"]

    # Ahora, prueba obtener el match por ID
    response = client.get(f"/matches/{match_id}")
    assert response.status_code == 200

    # Imprimir la respuesta completa para diagnóstico
    print(response.json())

    match_data = response.json()
    assert match_data["id"] == match_id
    assert match_data["match_name"] == "Test Lobby"
    assert match_data["max_players"] == 4
    assert match_data["is_public"] is True


def test_get_match_by_id_invalid_id(client):
    response = client.get("/matches/999999")
    assert response.status_code == 404  # Not Found


def test_join_match_success(client, load_matches, db_session):
    manager.create_game_connection(3)
    match = db_session.query(Matches).filter(Matches.id == 3).first()
    current_players = match.current_players
    response = client.post("/matches/3", json={"player_name": "Player 4"})
    assert response.status_code == status.HTTP_200_OK
    match = db_session.query(Matches).filter(Matches.id == 3).first()
    assert match.current_players == current_players + 1


def test_start_match_success(client, load_matches):
    manager.create_game_connection(1)
    with client.websocket_connect("/matches/1/ws/1") as ws1, client.websocket_connect("/matches/1/ws/2") as ws2:
        response = client.patch("/matches/1/start/1")
        assert response.status_code == 200
        data = ws1.receive_json()
        assert data['key'] == "START_MATCH"
        data = ws2.receive_json()
        assert data['key'] == "START_MATCH"

def test_create_movement_deck_success(client, load_matches, db_session):
    match = db_session.query(Matches).filter(Matches.id == 1).first()
    create_movement_deck(db_session, match.id)
    assert len(match.movement_cards) == 49
    
def test_create_movement_deck_invalid(client, load_matches, db_session):
    with pytest.raises(Exception):
        create_movement_deck(999999)
    
class TestStartMatchEndpoint:

    @pytest.fixture(scope="class")
    def cleanup(self, match, db_session):
        yield

        db_session.query(Players).filter(Players.match_id == match.id).delete()
        board = db_session.query(Boards).filter(Boards.match_id == match.id).first()
        db_session.query(Tiles).filter(Tiles.board_id == board.id).delete()
        db_session.query(Boards).filter(Boards.match_id == match.id).delete()
        db_session.query(Matches).filter(Matches.id == match.id).delete()
        db_session.commit()

        manager._games.pop(match.id, None)

    def test_start_match(
        self,
        client,
        db_session,
    ):
        seed(49)

        match_service_a = MatchService(db_session)
        player_service_a = PlayerService(db_session)
        board_service_a = BoardService(db_session)

        match = match_service_a.create_match("Test match", 3, True)
        owner = player_service_a.create_player("test_owner", match.id, True, "testtoken")
        players = []
        for i in range(1, 3):
            player = player_service_a.create_player(
                f"test_player_{i}", match.id, False, "testtoken"
            )
            players.append(player)

        match.current_players += 3
        db_session.commit()

        manager.create_game_connection(match.id)
        with client.websocket_connect(
            f"/matches/{match.id}/ws/{owner.id}"
        ) as websocket1, client.websocket_connect(
            f"/matches/{match.id}/ws/{players[0].id}"
        ) as websocket2, client.websocket_connect(
            f"/matches/{match.id}/ws/{players[1].id}"
        ) as websocket3:

            response = client.patch(f"/matches/{match.id}/start/{owner.id}")
            assert response.status_code == status.HTTP_200_OK

        msg_info = {
            "key": "GET_PLAYER_MATCH_INFO",
            "payload": {
                "turn_order": player.turn_order,
                "board": board_table,
                "current_turn_player": current_player.player_name,
                "opponents": [
                    {
                        "player_name": opponent.player_name,
                        "turn_order": opponent.turn_order
                    }
                    for opponent in players_in_match
                    if opponent.id != player_id
                ]
            }
        }
        mock_send_to_player.assert_any_call(match_id, player_id, msg_info)

        msg_shapes = {
            "key": "PLAYER_RECIEVE_ALL_SHAPES",
            "payload": [
                {"turn_order": player_i.turn_order, "shape_cards": [(shape.id, shape.shape_type) for shape in shape_cards]}
                for player_i in players_in_match
            ]
        }
        mock_send_to_player.assert_any_call(match_id, player_id, msg_shapes)

        msg_movements = {
            "key": "GET_MOVEMENT_CARD",
            "payload": {"movement_card": [(mov.id, mov.mov_type) for mov in movement_cards]}
        }
        mock_send_to_player.assert_any_call(match_id, player_id, msg_movements)


@pytest.mark.asyncio
async def test_start_match_success(client, db_session):
    match_id = 1
    player_id = 1

    match = MagicMock(id=match_id, current_players=4, max_players=4, state="WAITING", players=[MagicMock(id=2), MagicMock(id=3), MagicMock(id=4)])
    player = MagicMock(id=player_id, is_owner=True, match_id=match_id)

    with patch('app.routers.matches.MatchService.get_match_by_id', return_value=match), \
         patch('app.routers.matches.PlayerService.get_player_by_id', return_value=player), \
         patch('app.routers.matches.create_movement_deck'), \
         patch('app.routers.matches.ShapeCardService.create_shape_card'), \
         patch('app.routers.matches.BoardService.create_board', return_value=MagicMock(id=1)), \
         patch('app.routers.matches.BoardService.init_board'), \
         patch('app.routers.matches.MatchService.set_players_order'), \
         patch('app.routers.matches.manager.send_to_player', new_callable=AsyncMock) as mock_send_to_player, \
         patch('app.routers.matches.give_movement_card_to_player'), \
         patch('app.routers.matches.give_shape_card_to_player', new_callable=AsyncMock):

        response = client.patch(f"/matches/{match_id}/start/{player_id}")
        assert response.status_code == status.HTTP_200_OK

        # Verificar que el estado del match se haya actualizado
        assert match.state == "STARTED"

        # Verificar que se hayan enviado los mensajes correctos a los jugadores
        for player in match.players:
            mock_send_to_player.assert_any_call(match_id, player.id, {"key": "START_MATCH", "payload": {}})

    
