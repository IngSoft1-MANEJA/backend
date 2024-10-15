import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app  
from app.models.models import Matches, Players
from app.routers.matches import manager

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_mocks():
    with patch("app.cruds.match.MatchService.get_match_by_id") as mock_get_match_by_id, \
         patch("app.cruds.match.MatchService.update_turn") as mock_update_turn, \
         patch("app.cruds.player.PlayerService.get_player_by_id") as mock_get_player_by_id, \
         patch("app.routers.matches.manager.broadcast_to_game") as mock_broadcast_to_game, \
         patch("app.cruds.player.PlayerService.get_player_by_turn") as mock_get_player_by_turn:
        
        yield {
            "mock_get_player_by_id": mock_get_player_by_id,
            "mock_get_match_by_id": mock_get_match_by_id,
            "mock_update_turn": mock_update_turn,
            "mock_broadcast_to_game": mock_broadcast_to_game,
            "mock_get_player_by_turn": mock_get_player_by_turn
        }


def test_end_turn_success(setup_mocks):
    mocks = setup_mocks
    player1 = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=False, turn_order=1)
    player2 = MagicMock(id=2, player_name="Player 2", match_id=1, is_owner=False, turn_order=2)
    
    mocks["mock_get_player_by_id"].side_effect = [player1, player2]
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="WAITING", current_players=2, current_player_turn=1)
    mocks["mock_get_player_by_turn"].return_value = player2  

    response = client.patch("/matches/1/end-turn/1")
    
    assert response.status_code == status.HTTP_200_OK
    mocks["mock_update_turn"].assert_called_once_with(1, 2)
    mocks["mock_broadcast_to_game"].assert_called_once_with(1, {
        "key": "END_PLAYER_TURN", 
        "payload": {
            "current_player_name": "Player 1",
            "next_player_name": "Player 2",
            "next_player_turn": 2
        }
    })
    

def test_end_turn_max_player(setup_mocks):
    mocks = setup_mocks
    player1 = MagicMock(id=2, player_name="Player 1", match_id=1, is_owner=False, turn_order=2)
    player2 = MagicMock(id=1, player_name="Player 2", match_id=1, is_owner=False, turn_order=1)
    
    mocks["mock_get_player_by_id"].side_effect = [player1, player2]
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="WAITING", current_players=2, current_player_turn= 2)
    mocks["mock_get_player_by_turn"].return_value = player2  
    
    response = client.patch("/matches/1/end-turn/2")
    
    assert response.status_code == status.HTTP_200_OK
    mocks["mock_update_turn"].assert_called_once_with(1, turn=1)
    mocks["mock_broadcast_to_game"].assert_called_once_with(1, {
        "key": "END_PLAYER_TURN", 
        "payload": {
            "current_player_name": "Player 1",
            "next_player_name": "Player 2",
            "next_player_turn": 1
        }
    })


def test_end_turn_match_not_found(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_match_by_id"].return_value = None

    response = client.patch("/matches/1/end-turn/1")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Match not found"}


def test_end_turn_player_not_found(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="WAITING", current_players=2, current_player_turn=1)
    mocks["mock_get_player_by_id"].return_value = None

    response = client.patch("/matches/1/end-turn/1")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Player not found"}


def test_end_turn_not_player_turn(setup_mocks):
    mocks = setup_mocks
    player1 = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=False, turn_order=2)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="WAITING", current_players=2, current_player_turn=1)
    mocks["mock_get_player_by_id"].return_value = player1

    response = client.patch("/matches/1/end-turn/1")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "It's not player Player 1's turn"}