
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import BackgroundTasks
import pytest
from app.routers.players import turn_timeout

@pytest.mark.asyncio
@patch("app.routers.players.manager.broadcast_to_game", new_callable=AsyncMock)  # Mock de la función de broadcast
@patch("app.routers.players.MovementCardService")
@patch("app.routers.players.TileService")
@patch("app.routers.players.BoardService")
@patch("app.routers.players.MatchService")
@patch("app.routers.players.PlayerService")
async def test_turn_timeout_success(mock_manager, mock_movement_service, mock_tile_service, mock_board_service, mock_match_service, mock_player_service, client, db_session):
    match = MagicMock(id=1, current_players=4, max_players=4, state="STARTED", players=[MagicMock(id=2), MagicMock(id=3), MagicMock(id=4)])
    turn_order = 1
    mock_movement_service.return_value.get_movement_card_by_id.return_value.id = 1
    mock_match_service.return_value.get_match_by_id.return_value = match
    mock_player_service.return_value.get_player_by_turn.return_value.turn_order = 1
    mock_player_service.return_value.get_player_by_turn.return_value.player_name = "Player1"
    background_tasks = BackgroundTasks()

    response = await turn_timeout(match.id, db_session, turn_order, background_tasks)
    assert response == None
    
