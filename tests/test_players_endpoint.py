import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import NoResultFound

from app.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_mocks():
    with patch("app.cruds.player.PlayerService.get_player_by_id") as mock_get_player_by_id, \
         patch("app.cruds.match.MatchService.get_match_by_id") as mock_get_match_by_id, \
         patch("app.cruds.player.PlayerService.delete_player") as mock_delete_player, \
         patch("app.cruds.match.MatchService.update_match") as mock_update_match, \
         patch("app.routers.matches.manager.broadcast_to_game") as mock_broadcast_to_game, \
         patch("app.routers.matches.manager.disconnect_player_from_game") as mock_disconnect_player_from_game:
        
        yield {
            "mock_get_player_by_id": mock_get_player_by_id,
            "mock_get_match_by_id": mock_get_match_by_id,
            "mock_delete_player": mock_delete_player,
            "mock_update_match": mock_update_match,
            "mock_broadcast_to_game": mock_broadcast_to_game,
            "mock_disconnect_player_from_game": mock_disconnect_player_from_game
        }

def test_leave_player_success(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=False)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="WAITING", current_players=2)
    
    response = client.delete("/matches/1/left/1")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"player_id": 1, "players": "Player 1"}
    mocks["mock_delete_player"].assert_called_once_with(1)
    mocks["mock_update_match"].assert_called_once_with(1, "WAITING", 1)
    mocks["mock_broadcast_to_game"].assert_called_once_with(1, {"key": "PLAYER_LEFT", "payload": {"name": "Player 1"}})

def test_leave_player_not_in_match(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=2, player_name="Player 2", match_id=2, is_owner=False)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="WAITING", current_players=2)
    
    response = client.delete("/matches/1/left/2")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Player not in match"}

def test_leave_player_owner_cannot_leave(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=3, player_name="Player 3", match_id=1, is_owner=True)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="WAITING", current_players=2)
    
    response = client.delete("/matches/1/left/3")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Owner cannot leave match"}

def test_leave_player_not_connected(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=4, player_name="Player 4", match_id=1, is_owner=False)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="WAITING", current_players=2)
    mocks["mock_disconnect_player_from_game"].side_effect = Exception("Player not connected to match")
    
    response = client.delete("/matches/1/left/4")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Player not connected to match"}

def test_leave_player_match_not_found(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=False)
    mocks["mock_get_match_by_id"].side_effect = NoResultFound("Match not found")
    
    response = client.delete("/matches/999/left/1")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Match not found"}