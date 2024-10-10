from random import seed
import pytest
from fastapi import status

from app.cruds.board import BoardService
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.models import Matches, Players
from app.connection_manager import manager
from app.models.models import Boards, Tiles


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

            board = db_session.query(Boards).filter(Boards.match_id == match.id).first()
            board_table = board_service_a.get_board_table(board.id)

            owner = db_session.query(Players).filter(Players.match_id == match.id, Players.is_owner == True).first()

            players = db_session.query(Players).filter(Players.match_id == match.id, Players.is_owner == False).all()

            data = websocket1.receive_json()
            assert data["key"] == "START_MATCH"
            payload = data["payload"]

            assert payload["player_name"] == owner.player_name
            assert payload["turn_order"] == owner.turn_order
            assert payload["board"] == board_table
            assert payload["opponents"] == [
                {
                    "player_name": players[1].player_name,
                    "turn_order": players[1].turn_order,
                },
                {
                    "player_name": players[0].player_name,
                    "turn_order": players[0].turn_order,
                },
            ]

            data = websocket2.receive_json()
            assert data["key"] == "START_MATCH"
            payload = data["payload"]

            assert payload["player_name"] == players[0].player_name
            assert payload["turn_order"] == players[0].turn_order
            assert payload["board"] == board_table
            assert payload["opponents"] == [
                {
                    "player_name": players[1].player_name,
                    "turn_order": players[1].turn_order,
                },
                {"player_name": owner.player_name, "turn_order": owner.turn_order},
            ]

            data = websocket3.receive_json()
            assert data["key"] == "START_MATCH"
            payload = data["payload"]

            assert payload["player_name"] == players[1].player_name
            assert payload["turn_order"] == players[1].turn_order
            assert payload["board"] == board_table
            assert payload["opponents"] == [
                {
                    "player_name": players[0].player_name,
                    "turn_order": players[0].turn_order,
                },
                {"player_name": owner.player_name, "turn_order": owner.turn_order},
            ]
    
