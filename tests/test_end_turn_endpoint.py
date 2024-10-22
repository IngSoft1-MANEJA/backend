import pytest
from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app  
from app.models.models import Matches, Players
from app.routers.matches import manager

@pytest.fixture(scope="function")
def setup_mocks():
    with patch("app.cruds.match.MatchService.get_match_by_id") as mock_get_match_by_id, \
         patch("app.cruds.match.MatchService.update_turn") as mock_update_turn, \
         patch("app.cruds.player.PlayerService.get_player_by_id") as mock_get_player_by_id, \
         patch("app.routers.matches.manager.broadcast_to_game") as mock_broadcast_to_game, \
         patch("app.cruds.player.PlayerService.get_player_by_turn") as mock_get_player_by_turn, \
         patch("app.cruds.board.BoardService.get_board_by_match_id") as mock_get_board_by_match_id, \
         patch("app.routers.players.end_turn_logic") as mock_end_turn_logic, \
         patch("app.routers.players.give_movement_card_to_player") as mock_give_movement_card_to_player, \
         patch("app.routers.players.notify_movement_card_to_player", new_callable=AsyncMock) as mock_notify_movement_card_to_player, \
         patch("app.routers.players.give_shape_card_to_player", new_callable=AsyncMock) as mock_give_shape_card_to_player, \
         patch("app.routers.players.notify_all_players_movements_received", new_callable=AsyncMock) as mock_notify_all_players_movements_received, \
         patch("app.connection_manager.ConnectionManager.send_to_player", new_callable=AsyncMock) as mock_send_to_player:
        
        yield {
            "mock_get_player_by_id": mock_get_player_by_id,
            "mock_get_match_by_id": mock_get_match_by_id,
            "mock_update_turn": mock_update_turn,
            "mock_broadcast_to_game": mock_broadcast_to_game,
            "mock_get_player_by_turn": mock_get_player_by_turn,
            "mock_end_turn_logic": mock_end_turn_logic,
            "mock_give_movement_card_to_player": mock_give_movement_card_to_player,
            "mock_notify_movement_card_to_player": mock_notify_movement_card_to_player,
            "mock_give_shape_card_to_player": mock_give_shape_card_to_player,
            "mock_notify_all_players_movements_received": mock_notify_all_players_movements_received,
            "mock_send_to_player": mock_send_to_player,
            "mock_get_board_by_match_id": mock_get_board_by_match_id
        }

@pytest.mark.asyncio
async def test_end_turn_success(client, setup_mocks, db_session):
    mocks = setup_mocks
    player1 = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=True, turn_order=1)
    player2 = MagicMock(id=2, player_name="Player 2", match_id=1, is_owner=False, turn_order=2)
    match = MagicMock(id=1, state="STARTED", current_players=2, current_player_turn=1)
    board = MagicMock(id=1, match_id=1)
    movements = [(1, "Line"), (2, "Line Between"), (3, "Line Between")]
    
    mocks["mock_get_player_by_id"].side_effect = [player1, player2, player1]  # Añadir player1 para la llamada desde give_shape_card_to_player
    mocks["mock_get_match_by_id"].return_value = match
    mocks["mock_end_turn_logic"].return_value = player2
    mocks["mock_give_movement_card_to_player"].return_value = movements
    mocks["mock_get_board_by_match_id"].return_value = board
    
    response = client.patch("/matches/1/end-turn/1")
    
    print(f"Response status: {response.status_code}")
    print(f"Response json: {response.json()}")
    
    assert response.status_code == status.HTTP_200_OK
    mocks["mock_end_turn_logic"].assert_called_once_with(player1, match, db_session)
    mocks["mock_notify_movement_card_to_player"].assert_called_once_with(1, 1, movements)
    
    mocks["mock_give_movement_card_to_player"].assert_called_once_with(1, db_session)
    mocks["mock_get_board_by_match_id"].assert_called_once_with(1)
    mocks["mock_notify_all_players_movements_received"].assert_called_once_with(player1, match)
    mocks["mock_give_shape_card_to_player"].assert_called_once_with(1, db_session, is_init=False)
    mocks["mock_broadcast_to_game"].assert_called_once_with(1, {
        "key": "END_PLAYER_TURN", 
        "payload": {
            "current_player_name": "Player 1",
            "next_player_name": "Player 2",
            "next_player_turn": 2
        }
    })
    

@pytest.mark.asyncio
async def test_end_turn_match_not_found(client, setup_mocks, db_session):
    mocks = setup_mocks
    player = MagicMock(id=1, player_name="Player 1", match_id=1)
    mocks["mock_get_player_by_id"].return_value = player
    mocks["mock_get_match_by_id"].side_effect = Exception("Match not found")
    
    response = client.patch("/matches/1/end-turn/1")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Match not found"
    mocks["mock_get_player_by_id"].assert_called_once_with(1)
    mocks["mock_get_match_by_id"].assert_called_once_with(1)


@pytest.mark.asyncio
async def test_end_turn_player_not_found(client, setup_mocks, db_session):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].side_effect = Exception("Player not found")
    
    response = client.patch("/matches/1/end-turn/1")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Player not found"
    mocks["mock_get_player_by_id"].assert_called_once_with(1)
    mocks["mock_get_match_by_id"].assert_not_called()

def test_end_turn_logic_max_turn(setup_mocks, client, db_session):
    mocks = setup_mocks
    player1 = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=False, turn_order=1)
    player2 = MagicMock(id=2, player_name="Player 2", match_id=1, is_owner=False, turn_order=2)
    match = MagicMock(id=1, state="STARTED", current_players=2, current_player_turn=1)

    # Simula el comportamiento de los mocks
    mocks["mock_get_player_by_id"].return_value = player1
    mocks["mock_get_match_by_id"].return_value = match
    mocks["mock_end_turn_logic"].return_value = player2  # Mockea la función end_turn_logic

    # Realiza la petición al endpoint
    response = client.patch("/matches/1/end-turn/1")

    # Afirmaciones
    assert response.status_code == status.HTTP_200_OK

    # Verifica que se haya llamado a end_turn_logic con los parámetros correctos
    mocks["mock_end_turn_logic"].assert_called_once_with(player1, match, db_session)

    # Verifica que el resto de la lógica se ejecuta como es esperado
    mocks["mock_give_movement_card_to_player"].assert_called_once_with(1, db_session)
    mocks["mock_broadcast_to_game"].assert_called_once_with(1, {
        "key": "END_PLAYER_TURN",
        "payload": {
            "current_player_name": "Player 1",
            "next_player_name": "Player 2",
            "next_player_turn": 2
        }
    })


def test_end_turn_logic_not_player_turn(setup_mocks, client, db_session):
    mocks = setup_mocks
    player1 = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=False, turn_order=2)
    match = MagicMock(id=1, state="STARTED", current_players=2, current_player_turn=1)  # Es el turno de otro jugador
    
    # Configuramos los mocks
    mocks["mock_get_player_by_id"].return_value = player1
    mocks["mock_get_match_by_id"].return_value = match
    
    # Mockeamos end_turn_logic para lanzar la excepción HTTP 403
    mocks["mock_end_turn_logic"].side_effect = HTTPException(status_code=403, detail=f"It's not player {player1.player_name}'s turn")

    # Hacemos la petición al endpoint
    response = client.patch("/matches/1/end-turn/1")

    # Afirmamos que el status code sea 403
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Afirmamos que el mensaje de error sea el esperado
    assert response.json() == {"detail": "It's not player Player 1's turn"}

    # Verifica que se haya llamado a end_turn_logic con los parámetros correctos
    mocks["mock_end_turn_logic"].assert_called_once_with(player1, match, db_session)

