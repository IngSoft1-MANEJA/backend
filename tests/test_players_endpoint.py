import pytest
from fastapi.testclient import TestClient
from fastapi import status, HTTPException
from unittest.mock import call, patch, MagicMock, AsyncMock
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm.session import Session

from app.main import app
from app.routers.players import playerWinner
from app.models.enums import ReasonWinning
from app.schemas import PartialMove, Tile
from app.exceptions import PlayerNotConnected
from app.routers.players import validate_partial_move

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_mocks():
    with patch("app.cruds.player.PlayerService.get_player_by_id") as mock_get_player_by_id, \
         patch("app.cruds.match.MatchService.get_match_by_id") as mock_get_match_by_id, \
         patch("app.cruds.player.PlayerService.delete_player") as mock_delete_player, \
         patch("app.cruds.match.MatchService.update_match") as mock_update_match, \
         patch("app.cruds.match.MatchService.delete_match") as mock_delete_match, \
         patch("app.routers.matches.manager.broadcast_to_game") as mock_broadcast_to_game, \
         patch("app.routers.matches.manager.disconnect_player_from_game") as mock_disconnect_player_from_game, \
         patch("app.cruds.movement_card.MovementCardService.get_movement_card_by_id") as mock_get_movement_card_by_id, \
         patch("app.cruds.tile.TileService.get_tile_by_position") as mock_get_tile_by_position, \
         patch("app.cruds.tile.TileService.update_tile_position") as mock_update_tile_position, \
         patch("app.cruds.board.BoardService.get_board_by_match_id") as mock_get_board_by_match_id, \
         patch("app.cruds.board.BoardService.update_list_of_parcial_movements") as mock_update_list_of_parcial_movements, \
         patch("app.cruds.movement_card.MovementCardService.update_card_owner_to_none") as mock_update_card_owner_to_none, \
         patch("app.cruds.movement_card.MovementCardService.add_movement_card_to_player") as mock_add_movement_card_to_player, \
         patch("app.cruds.board.BoardService.print_temporary_movements") as mock_print_temporary_movements, \
         patch("app.cruds.board.BoardService.get_formed_figures") as mock_get_formed_figures, \
         patch("app.cruds.board.BoardService.get_last_temporary_movements") as mock_get_last_temporary_movements, \
         patch("app.routers.players.validate_partial_move", return_value=True) as mock_validate_partial_move, \
         patch("app.routers.players.playerWinner", new_callable=AsyncMock) as mock_player_winner:
        
        yield {
            "mock_get_player_by_id": mock_get_player_by_id,
            "mock_get_match_by_id": mock_get_match_by_id,
            "mock_delete_player": mock_delete_player,
            "mock_update_match": mock_update_match,
            "mock_broadcast_to_game": mock_broadcast_to_game,
            "mock_delete_match": mock_delete_match,
            "mock_disconnect_player_from_game": mock_disconnect_player_from_game,
            "mock_get_movement_card_by_id": mock_get_movement_card_by_id,
            "mock_get_tile_by_position": mock_get_tile_by_position,
            "mock_update_tile_position": mock_update_tile_position,
            "mock_get_board_by_match_id": mock_get_board_by_match_id,
            "mock_update_list_of_parcial_movements": mock_update_list_of_parcial_movements,
            "mock_add_movement_card_to_player": mock_add_movement_card_to_player,
            "mock_get_last_temporary_movements": mock_get_last_temporary_movements,
            "mock_update_card_owner_to_none": mock_update_card_owner_to_none,
            "mock_print_temporary_movements": mock_print_temporary_movements,
            "mock_get_formed_figures": mock_get_formed_figures,
            "mock_validate_partial_move": mock_validate_partial_move,
            "mock_player_winner": mock_player_winner
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
    

def test_leave_player_not_connected(setup_mocks):
    mocks = setup_mocks
    player = MagicMock(id=1, player_name="Player 1", match_id=2, is_owner=False)
    match = MagicMock(id=1, state="WAITING", current_players=2)
    
    mocks["mock_get_player_by_id"].return_value = player
    mocks["mock_get_match_by_id"].return_value = match
    mocks["mock_disconnect_player_from_game"].side_effect = PlayerNotConnected(1,"Player not connected to match")
    
    response = client.delete("/matches/1/left/1")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Player not in match"}


def test_leave_player_match_not_found(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=False)
    mocks["mock_get_match_by_id"].side_effect = NoResultFound("Match not found")
    
    response = client.delete("/matches/999/left/1")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Match not found"}


def test_leave_player_triggers_player_winner(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=False)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="STARTED", current_players=1)
    
    response = client.delete("/matches/1/left/1")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"player_id": 1, "players": "Player 1"}
    mocks["mock_delete_player"].assert_called_once_with(1)
    mocks["mock_update_match"].assert_called_once_with(1, "STARTED", 0)
    mocks["mock_broadcast_to_game"].assert_called_once_with(1, {"key": "PLAYER_LEFT", "payload": {"name": "Player 1"}})
    
    mocks["mock_player_winner"].assert_called_once()
    called_args = mocks["mock_player_winner"].call_args[0]
    assert called_args[0] == 1
    assert called_args[1] == ReasonWinning.FORFEIT
    assert isinstance(called_args[2], Session) 


def test_validate_partial_move_valid():
    partial_move = PartialMove(tiles=[Tile(rowIndex=0, columnIndex=0), Tile(rowIndex=2, columnIndex=2)], movement_card=49)
    assert validate_partial_move(partial_move, "Diagonal")


def test_validate_partial_move_invalid_card_type():
    partial_move = PartialMove(tiles=[Tile(rowIndex=0, columnIndex=0), Tile(rowIndex=1, columnIndex=1)], movement_card=1)
    with pytest.raises(HTTPException) as excinfo:
        validate_partial_move(partial_move, "Invalid Card")
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Movement card not valid"


def test_validate_partial_move_invalid_tile_position():
    partial_move = PartialMove(tiles=[Tile(rowIndex=-1, columnIndex=0), Tile(rowIndex=7, columnIndex=7)], movement_card=8)
    with pytest.raises(HTTPException) as excinfo:
        validate_partial_move(partial_move, "Diagonal")
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Tile position is invalid"


def test_partial_move_success(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=True, turn_order=1)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="STARTED", current_players=2, current_player_turn=1)
    mocks["mock_get_movement_card_by_id"].return_value = MagicMock(mov_type="Diagonal")
    mocks["mock_get_tile_by_position"].side_effect = [
        MagicMock(id=1, position_x=0, position_y=0),
        MagicMock(id=2, position_x=1, position_y=1)
    ]
    mocks["mock_get_board_by_match_id"].return_value = MagicMock(id=1)
    mocks["mock_get_formed_figures"].return_value = [{"figure": "1"}]
    mocks["mock_validate_partial_move"].return_value = True
    
    response = client.post("/matches/1/partial-move/1", json={
        "tiles": [{"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}],
        "movement_card": 1
    })
    
    assert response.status_code == status.HTTP_200_OK
    mocks["mock_update_tile_position"].assert_any_call(1, 1, 1)
    mocks["mock_update_tile_position"].assert_any_call(2, 0, 0)
    mocks["mock_update_list_of_parcial_movements"].assert_called_once()
    mocks["mock_update_card_owner_to_none"].assert_called_once()
    expected_calls = [
        ((1, {"key": "PLAYER_RECEIVE_NEW_BOARD", "payload": {"swapped_tiles": [{"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}]}}),),
        ((1, {"key": "ALLOW_FIGURES", "payload": [{"figure": "1"}]}),)
    ]
    mocks["mock_broadcast_to_game"].assert_has_calls(expected_calls, any_order=True)

def test_partial_move_match_not_found(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_match_by_id"].side_effect = NoResultFound("Match not found")
    
    response = client.post("/matches/1/partial-move/1", json={
        "tiles": [{"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}],
        "movement_card": 1
    })
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Match not found"}


def test_partial_move_player_not_found(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].side_effect = ValueError("Player not found")
    
    response = client.post("/matches/1/partial-move/1", json={
        "tiles": [{"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}],
        "movement_card": 1
    })
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Player not found"}


def test_partial_move_not_player_turn(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=False, turn_order=2)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="STARTED", current_players=2, current_turn=1)
    
    response = client.post("/matches/1/partial-move/1", json={
        "tiles": [{"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}],
        "movement_card": 1
    })
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "It's not player Player 1's turn"}


def test_partial_move_invalid_movement(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=False, turn_order=1)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="STARTED", current_players=2, current_player_turn=1)
    mocks["mock_get_movement_card_by_id"].return_value = MagicMock(mov_type="Line Border")
    
    with patch("app.routers.players.validate_partial_move", return_value=False):
        response = client.post("/matches/1/partial-move/1", json={
            "tiles": [{"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}],
            "movement_card": 1
        })
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid movement"}


def test_partial_move_formed_figures_error(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=False, turn_order=1)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="STARTED", current_players=2, current_player_turn=1)
    mocks["mock_get_movement_card_by_id"].return_value = MagicMock(mov_type="Diagonal")
    mocks["mock_get_tile_by_position"].side_effect = [
        MagicMock(id=1, position_x=0, position_y=0),
        MagicMock(id=2, position_x=1, position_y=1)
    ]
    mocks["mock_get_board_by_match_id"].return_value = MagicMock(id=1)
    mocks["mock_get_formed_figures"].side_effect = Exception("Error with formed figures")

    response = client.post("/matches/1/partial-move/1", json={
        "tiles": [{"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}],
        "movement_card": 1
    })
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error with formed figures"}
   
    
def test_delete_partial_move_success(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=True, turn_order=1)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="STARTED", current_players=2, current_player_turn=1)
    mocks["mock_get_movement_card_by_id"].return_value = MagicMock(mov_type="Diagonal")
    mocks["mock_get_last_temporary_movements"].return_value = MagicMock(tile1=MagicMock(id=1, position_x=0, position_y=0), tile2=MagicMock(id=2, position_x=1, position_y=1), id_mov=1)
    mocks["mock_get_board_by_match_id"].return_value = MagicMock(id=1)
    mocks["mock_get_formed_figures"].return_value = []
    
    response = client.delete("/matches/1/partial-move/1")
    
    assert response.status_code == status.HTTP_200_OK
    mocks["mock_update_tile_position"].assert_any_call(1, 1, 1)
    mocks["mock_update_tile_position"].assert_any_call(2, 0, 0)
    mocks["mock_add_movement_card_to_player"].assert_called_once()
    
    expected_calls = [
        call(1, {"key": "UNDO_PARTIAL_MOVE", "payload": {"tiles": [{"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}]}}),
        call(1, {"key": "ALLOW_FIGURES", "payload": []})
    ]
    mocks["mock_broadcast_to_game"].assert_has_calls(expected_calls, any_order=True)


def test_delete_partial_move_match_not_found(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_match_by_id"].side_effect = NoResultFound("Match not found")
    
    response = client.delete("/matches/1/partial-move/1")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Match not found"}


def test_delete_partial_move_player_not_found(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].side_effect = ValueError("Player not found")
    
    response = client.delete("/matches/1/partial-move/1")   
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Player not found"}


def test_delete_partial_move_not_player_turn(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=False, turn_order=2)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="STARTED", current_players=2, current_player_turn=1)
    
    response = client.delete("/matches/1/partial-move/1")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "It's not player Player 1's turn"}


def test_delete_partial_move_no_movements_to_undo(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=True, turn_order=1)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="STARTED", current_players=2, current_player_turn=1)
    mocks["mock_get_last_temporary_movements"].return_value = None
    
    response = client.delete("/matches/1/partial-move/1")
    
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "No movements to undo"}


def test_delete_partial_move_movement_card_not_found(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=True, turn_order=1)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="STARTED", current_players=2, current_player_turn=1)
    mocks["mock_get_last_temporary_movements"].return_value = MagicMock(tile1=MagicMock(id=1, position_x=0, position_y=0), tile2=MagicMock(id=2, position_x=1, position_y=1), id_mov=1)
    mocks["mock_get_board_by_match_id"].return_value = MagicMock(id=1)
    mocks["mock_get_movement_card_by_id"].side_effect = NoResultFound("Movement card not found")
    
    response = client.delete("/matches/1/partial-move/1")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Movement card not found"}


def test_delete_partial_move_tile_not_found(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=True, turn_order=1)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="STARTED", current_players=2, current_player_turn=1)
    mocks["mock_get_last_temporary_movements"].return_value = MagicMock(tile1=MagicMock(id=1, position_x=0, position_y=0), tile2=MagicMock(id=2, position_x=1, position_y=1), id_mov=1)
    mocks["mock_get_board_by_match_id"].return_value = MagicMock(id=1)
    mocks["mock_get_movement_card_by_id"].return_value = MagicMock(mov_type="Diagonal")
    mocks["mock_update_tile_position"].side_effect = NoResultFound("Tile not found")
    
    response = client.delete("/matches/1/partial-move/1")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Tile not found"}


def test_delete_partial_move_formed_figures_error(setup_mocks):
    mocks = setup_mocks
    mocks["mock_get_player_by_id"].return_value = MagicMock(id=1, player_name="Player 1", match_id=1, is_owner=True, turn_order=1)
    mocks["mock_get_match_by_id"].return_value = MagicMock(id=1, state="STARTED", current_players=2, current_player_turn=1)
    mocks["mock_get_last_temporary_movements"].return_value = MagicMock(tile1=MagicMock(id=1, position_x=0, position_y=0), tile2=MagicMock(id=2, position_x=1, position_y=1), id_mov=1)
    mocks["mock_get_board_by_match_id"].return_value = MagicMock(id=1)
    mocks["mock_get_movement_card_by_id"].return_value = MagicMock(mov_type="Diagonal")
    mocks["mock_get_formed_figures"].side_effect = Exception("Error with formed figures")
    
    response = client.delete("/matches/1/partial-move/1")
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error with formed figures"}
    assert isinstance(called_args[2], Session)


@pytest.mark.asyncio
async def test_owner_leave_match(setup_mocks):
    mocks = setup_mocks
    owner = MagicMock(id=1, player_name="Owner", match_id=1, is_owner=True)
    player2 = MagicMock(id=2, player_name="Player 2", match_id=1, is_owner=False)
    match = MagicMock(id=1, state="WAITING", current_players=2, players=[owner, player2])
    
    mocks["mock_get_player_by_id"].return_value = owner
    mocks["mock_get_match_by_id"].return_value = match

    response = client.delete("/matches/1/left/1")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "The match has been canceled because the owner has left."}
    mocks["mock_broadcast_to_game"].assert_called_once_with(1, {
        "key": "PLAYER_LEFT",
        "payload": {
            "owner_name": "Owner",
            "is_owner": True
        }
    })
    mocks["mock_disconnect_player_from_game"].assert_called()
    mocks["mock_delete_match"].assert_called_once_with(1)
    
    