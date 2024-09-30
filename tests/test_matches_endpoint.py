import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import status

from app.main import app
from app.database import Base, get_db, init_db, delete_db, engine
from app.models import Matches, Players
from app.routers.matches import manager
from tests.populate_test_db import load_data_for_test

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.sqlite"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_match():
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
    db = TestingSessionLocal()
    match = db.query(Matches).filter(Matches.id == data["match_id"]).first()
    print(match)
    assert match is not None
    assert match.match_name == "Test Lobby"
    assert match.max_players == 4
    assert match.is_public is True

    player = db.query(Players).filter(Players.id == data["player_id"]).first()
    assert player is not None
    assert player.player_name == "Test Player"
    assert player.match_id == match.id
    assert player.is_owner is True
    assert player.session_token == "testtoken"

def test_create_match_invalid_data():
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

def test_get_matches():
    response = client.get("/matches/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_match_by_id():
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

def test_get_match_by_id_invalid_id():
    response = client.get("/matches/999999")
    assert response.status_code == 404  # Not Found

def test_joinGame_success():
    load_data_for_test()
    manager.create_game_connection(1)
    with client.websocket_connect("/matches/1/ws/1") as websocket:
        player_name = "Test Player 2"
        response = client.post("/matches/1/", json={"player_name": player_name})
        assert response.status_code == status.HTTP_200_OK
        data = websocket.receive_json()
        assert data == {"key": "PLAYER_JOIN", "payload": f"Player {player_name} has joined to the match."}

"""

def test_joinGame_failure_gameDoesntExist(client):

    response = client.patch("/games/1/join", json={"playerNickname": "p2"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"Error": "Partida 1 no existe."}


def test_joinGame_failure_playerAlreadyInGame(client, dataListGames):

    response = client.patch("/games/1/join", json={"playerNickname": "p0"})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"Error": "Jugador p0 ya se encuentra en la partida 1"}


def test_joinGame_failure_gameStarted(client, dataListGames):

    response = client.patch("/games/3/join", json={"playerNickname": "player_test"})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"Error": "La partida g3 ya esta empezada."}


def test_joinGame_failure_gameIsFull(client, dataListGames):

    response = client.patch("/games/2/join", json={"playerNickname": "player_test"})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"Error": "La partida g2 ya esta llena."}

"""