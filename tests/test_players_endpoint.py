import pytest
from fastapi import status, HTTPException
from unittest.mock import call, patch, MagicMock, AsyncMock
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm.session import Session

from app.models.enums import EasyShapes, ReasonWinning
from app.schemas import PartialMove, Tile
from app.exceptions import PlayerNotConnected
from app.routers.players import validate_partial_move
from app.utils.board_shapes_algorithm import rotate_90_degrees, rotate_180_degrees, rotate_270_degrees
from app.utils.utils import FIGURE_COORDINATES


@pytest.fixture(scope="function")
def setup_player_mocks():
    with patch("app.cruds.player.PlayerService.get_player_by_id") as mock_get_player_by_id, \
            patch("app.cruds.player.PlayerService.delete_player") as mock_delete_player:
        yield {
            "mock_get_player_by_id": mock_get_player_by_id,
            "mock_delete_player": mock_delete_player,
        }


@pytest.fixture(scope="function")
def setup_match_mocks():
    with patch("app.cruds.match.MatchService.get_match_by_id") as mock_get_match_by_id, \
            patch("app.cruds.match.MatchService.update_match") as mock_update_match, \
            patch("app.cruds.match.MatchService.delete_match") as mock_delete_match:
        yield {
            "mock_get_match_by_id": mock_get_match_by_id,
            "mock_update_match": mock_update_match,
            "mock_delete_match": mock_delete_match,
        }


@pytest.fixture(scope="function")
def setup_board_mocks():
    with patch("app.cruds.board.BoardService.get_board_by_match_id") as mock_get_board_by_match_id, \
            patch("app.cruds.board.BoardService.update_list_of_parcial_movements") as mock_update_list_of_parcial_movements, \
            patch("app.cruds.board.BoardService.print_temporary_movements") as mock_print_temporary_movements, \
            patch("app.cruds.board.BoardService.get_formed_figures") as mock_get_formed_figures, \
            patch("app.cruds.board.BoardService.get_last_temporary_movements") as mock_get_last_temporary_movements, \
            patch("app.cruds.board.BoardService.get_board_by_id") as mock_get_board_by_id, \
            patch("app.cruds.board.BoardService.get_ban_color") as mock_get_ban_color:
        yield {
            "mock_get_board_by_match_id": mock_get_board_by_match_id,
            "mock_update_list_of_parcial_movements": mock_update_list_of_parcial_movements,
            "mock_print_temporary_movements": mock_print_temporary_movements,
            "mock_get_formed_figures": mock_get_formed_figures,
            "mock_get_last_temporary_movements": mock_get_last_temporary_movements,
            "mock_get_board_by_id": mock_get_board_by_id,
            "mock_get_ban_color": mock_get_ban_color,
        }


@pytest.fixture(scope="function")
def setup_tile_mocks():
    with patch("app.cruds.tile.TileService.get_tile_by_position") as mock_get_tile_by_position, \
            patch("app.cruds.tile.TileService.get_tile_by_id") as mock_get_tile_by_id, \
            patch("app.cruds.tile.TileService.update_tile_position") as mock_update_tile_position:
        yield {
            "mock_get_tile_by_position": mock_get_tile_by_position,
            "mock_update_tile_position": mock_update_tile_position,
            "mock_get_tile_by_id": mock_get_tile_by_id,
        }


@pytest.fixture(scope="function")
def setup_movement_card_mocks():
    with patch("app.cruds.movement_card.MovementCardService.get_movement_card_by_id") as mock_get_movement_card_by_id, \
            patch("app.cruds.movement_card.MovementCardService.update_card_owner_to_none") as mock_update_card_owner_to_none, \
            patch("app.cruds.movement_card.MovementCardService.add_movement_card_to_player") as mock_add_movement_card_to_player:
        yield {
            "mock_get_movement_card_by_id": mock_get_movement_card_by_id,
            "mock_update_card_owner_to_none": mock_update_card_owner_to_none,
            "mock_add_movement_card_to_player": mock_add_movement_card_to_player,
        }


@pytest.fixture(scope="function")
def setup_broadcast_mocks():
    with patch("app.routers.matches.manager.broadcast_to_game") as mock_broadcast_to_game, \
            patch("app.routers.matches.manager.disconnect_player_from_game") as mock_disconnect_player_from_game:
        yield {
            "mock_broadcast_to_game": mock_broadcast_to_game,
            "mock_disconnect_player_from_game": mock_disconnect_player_from_game,
        }


@pytest.fixture(scope="function")
def setup_validation_mocks():
    with patch("app.routers.players.validate_partial_move", return_value=True) as mock_validate_partial_move, \
            patch("app.routers.players.playerWinner", new_callable=AsyncMock) as mock_player_winner:
        yield {
            "mock_validate_partial_move": mock_validate_partial_move,
            "mock_player_winner": mock_player_winner,
        }


@pytest.fixture(scope="function")
def setup_shape_card_mocks():
    with patch("app.cruds.shape_card.ShapeCardService.get_shape_card_by_id", return_value=MagicMock(id=1, player_owner=1, is_visible=True, is_hard=False, shape_type=EasyShapes.MINI_LINE.value)) as get_shape_card_by_id, \
            patch("app.cruds.shape_card.ShapeCardService.delete_shape_card") as delete_shape_card:
        yield {
            "get_shape_card_by_id": get_shape_card_by_id,
            "delete_shape_card": delete_shape_card,
        }

def test_leave_player_success(setup_player_mocks, setup_match_mocks, setup_broadcast_mocks, client):
    player_mocks = setup_player_mocks
    match_mocks = setup_match_mocks
    broadcast_mocks = setup_broadcast_mocks

    player_mocks["mock_get_player_by_id"].return_value = MagicMock(
        id=1, player_name="Player 1", match_id=1, is_owner=False)
    match_mocks["mock_get_match_by_id"].return_value = MagicMock(
        id=1, state="WAITING", current_players=2)

    response = client.delete("/matches/1/left/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"player_id": 1, "players": "Player 1"}
    player_mocks["mock_delete_player"].assert_called_once_with(1)
    match_mocks["mock_update_match"].assert_called_once_with(1, "WAITING", 1)
    broadcast_mocks["mock_broadcast_to_game"].assert_called_once_with(
        1, {"key": "PLAYER_LEFT", "payload": {"name": "Player 1"}})


def test_leave_player_not_in_match(setup_player_mocks, setup_match_mocks, client):
    player_mocks = setup_player_mocks
    match_mocks = setup_match_mocks

    player_mocks["mock_get_player_by_id"].return_value = MagicMock(
        id=2, player_name="Player 2", match_id=2, is_owner=False)
    match_mocks["mock_get_match_by_id"].return_value = MagicMock(
        id=1, state="WAITING", current_players=2)

    response = client.delete("/matches/1/left/2")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Player not in match"}


def test_leave_player_not_connected(setup_player_mocks, setup_match_mocks, setup_broadcast_mocks, client):
    player_mocks = setup_player_mocks
    match_mocks = setup_match_mocks
    broadcast_mocks = setup_broadcast_mocks

    player = MagicMock(id=1, player_name="Player 1", match_id=2, is_owner=False)
    match = MagicMock(id=1, state="WAITING", current_players=2)

    player_mocks["mock_get_player_by_id"].return_value = player
    match_mocks["mock_get_match_by_id"].return_value = match
    broadcast_mocks["mock_disconnect_player_from_game"].side_effect = PlayerNotConnected(
        1, "Player not connected to match")

    response = client.delete("/matches/1/left/1")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Player not in match"}


def test_leave_player_match_not_found(setup_player_mocks, setup_match_mocks, client):
    player_mocks = setup_player_mocks
    match_mocks = setup_match_mocks

    player_mocks["mock_get_player_by_id"].return_value = MagicMock(
        id=1, player_name="Player 1", match_id=1, is_owner=False)
    match_mocks["mock_get_match_by_id"].side_effect = NoResultFound(
        "Match not found")

    response = client.delete("/matches/999/left/1")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Match not found"}


def test_leave_player_triggers_player_winner(setup_player_mocks, setup_match_mocks, setup_broadcast_mocks, setup_validation_mocks, client):
    player_mocks = setup_player_mocks
    match_mocks = setup_match_mocks
    broadcast_mocks = setup_broadcast_mocks
    validation_mocks = setup_validation_mocks

    player_mocks["mock_get_player_by_id"].return_value = MagicMock(
        id=1, player_name="Player 1", match_id=1, is_owner=False)
    match_mocks["mock_get_match_by_id"].return_value = MagicMock(
        id=1, state="STARTED", current_players=1)

    response = client.delete("/matches/1/left/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"player_id": 1, "players": "Player 1"}
    player_mocks["mock_delete_player"].assert_called_once_with(1)
    match_mocks["mock_update_match"].assert_called_once_with(1, "STARTED", 0)
    broadcast_mocks["mock_broadcast_to_game"].assert_called_once_with(
        1, {"key": "PLAYER_LEFT", "payload": {"name": "Player 1"}})

    validation_mocks["mock_player_winner"].assert_called_once()
    called_args = validation_mocks["mock_player_winner"].call_args[0]
    assert called_args[0] == 1
    assert called_args[1] == ReasonWinning.FORFEIT
    assert isinstance(called_args[2], Session)


def test_validate_partial_move_valid():
    partial_move = PartialMove(tiles=[Tile(rowIndex=0, columnIndex=0), Tile(
        rowIndex=2, columnIndex=2)], movement_card=49)
    assert validate_partial_move(partial_move, "Diagonal")


def test_validate_partial_move_invalid_card_type():
    partial_move = PartialMove(tiles=[Tile(rowIndex=0, columnIndex=0), Tile(
        rowIndex=1, columnIndex=1)], movement_card=1)
    with pytest.raises(HTTPException) as excinfo:
        validate_partial_move(partial_move, "Invalid Card")
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Movement card not valid"


def test_validate_partial_move_invalid_tile_position():
    partial_move = PartialMove(tiles=[Tile(
        rowIndex=-1, columnIndex=0), Tile(rowIndex=7, columnIndex=7)], movement_card=8)
    with pytest.raises(HTTPException) as excinfo:
        validate_partial_move(partial_move, "Diagonal")
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Tile position is invalid"


def test_partial_move_success(setup_player_mocks, setup_match_mocks, setup_board_mocks, setup_tile_mocks, setup_movement_card_mocks, setup_broadcast_mocks, setup_validation_mocks, client):
    player_mocks = setup_player_mocks
    match_mocks = setup_match_mocks
    board_mocks = setup_board_mocks
    tile_mocks = setup_tile_mocks
    movement_card_mocks = setup_movement_card_mocks
    broadcast_mocks = setup_broadcast_mocks
    validation_mocks = setup_validation_mocks

    player_mocks["mock_get_player_by_id"].return_value = MagicMock(
        id=1, player_name="Player 1", match_id=1, is_owner=True, turn_order=1)
    match_mocks["mock_get_match_by_id"].return_value = MagicMock(
        id=1, state="STARTED", current_players=2, current_player_turn=1)
    movement_card_mocks["mock_get_movement_card_by_id"].return_value = MagicMock(
        mov_type="Diagonal")
    tile_mocks["mock_get_tile_by_position"].side_effect = [
        MagicMock(id=1, position_x=0, position_y=0),
        MagicMock(id=2, position_x=1, position_y=1)
    ]
    board_mocks["mock_get_board_by_match_id"].return_value = MagicMock(id=1)
    board_mocks["mock_get_formed_figures"].return_value = []
    validation_mocks["mock_validate_partial_move"].return_value = True

    response = client.post("/matches/1/partial-move/1", json={
        "tiles": [{"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}],
        "movement_card": 1
    })

    assert response.status_code == 200
    tile_mocks["mock_update_tile_position"].assert_any_call(1, 1, 1)
    tile_mocks["mock_update_tile_position"].assert_any_call(2, 0, 0)
    board_mocks["mock_update_list_of_parcial_movements"].assert_called_once()
    movement_card_mocks["mock_update_card_owner_to_none"].assert_called_once()
    expected_calls = [
        ((1, {"key": "PLAYER_RECEIVE_NEW_BOARD", "payload": {"swapped_tiles": [
         {"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}]}}),),
        ((1, {"key": "ALLOW_FIGURES", "payload": []}),)
    ]
    broadcast_mocks["mock_broadcast_to_game"].assert_has_calls(
        expected_calls, any_order=True)


def test_partial_move_match_not_found(setup_match_mocks, client):
    match_mocks = setup_match_mocks

    match_mocks["mock_get_match_by_id"].side_effect = NoResultFound(
        "Match not found")

    response = client.post("/matches/1/partial-move/1", json={
        "tiles": [{"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}],
        "movement_card": 1
    })

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Match not found"}


def test_partial_move_player_not_found(setup_player_mocks, setup_match_mocks, client):
    player_mocks = setup_player_mocks
    match_mocks = setup_match_mocks

    # Mock para la búsqueda del match
    match_mocks["mock_get_match_by_id"].return_value = {"id": 1, "name": "Test Match"}

    # Mock para la búsqueda del jugador
    player_mocks["mock_get_player_by_id"].side_effect = ValueError("Player not found")

    response = client.post("/matches/1/partial-move/1", json={
        "tiles": [{"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}],
        "movement_card": 1
    })

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Player not found"}


def test_partial_move_not_player_turn(setup_player_mocks, setup_match_mocks, client):
    player_mocks = setup_player_mocks
    match_mocks = setup_match_mocks

    player_mocks["mock_get_player_by_id"].return_value = MagicMock(
        id=1, player_name="Player 1", match_id=1, is_owner=False, turn_order=2)
    match_mocks["mock_get_match_by_id"].return_value = MagicMock(
        id=1, state="STARTED", current_players=2, current_turn=1)

    response = client.post("/matches/1/partial-move/1", json={
        "tiles": [{"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}],
        "movement_card": 1
    })

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "It's not player Player 1's turn"}


def test_partial_move_invalid_movement(setup_player_mocks, setup_match_mocks, setup_movement_card_mocks, client):
    player_mocks = setup_player_mocks
    match_mocks = setup_match_mocks
    movement_card_mocks = setup_movement_card_mocks

    player_mocks["mock_get_player_by_id"].return_value = MagicMock(
        id=1, player_name="Player 1", match_id=1, is_owner=False, turn_order=1)
    match_mocks["mock_get_match_by_id"].return_value = MagicMock(
        id=1, state="STARTED", current_players=2, current_player_turn=1)
    movement_card_mocks["mock_get_movement_card_by_id"].return_value = MagicMock(
        mov_type="Line Border")

    with patch("app.routers.players.validate_partial_move", return_value=False):
        response = client.post("/matches/1/partial-move/1", json={
            "tiles": [{"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}],
            "movement_card": 1
        })

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid movement"}


def test_delete_partial_move_success(setup_player_mocks, setup_match_mocks, setup_board_mocks, setup_tile_mocks, setup_movement_card_mocks, setup_broadcast_mocks, client):
    mocks_player = setup_player_mocks
    mocks_match = setup_match_mocks
    mocks_board = setup_board_mocks
    mocks_tile = setup_tile_mocks
    mocks_movement_card = setup_movement_card_mocks
    mocks_broadcast = setup_broadcast_mocks

    mocks_player["mock_get_player_by_id"].return_value = MagicMock(
        id=1, player_name="Player 1", match_id=1, is_owner=True, turn_order=1)
    mocks_match["mock_get_match_by_id"].return_value = MagicMock(
        id=1, state="STARTED", current_players=2, current_player_turn=1)
    mocks_movement_card["mock_get_movement_card_by_id"].return_value = MagicMock(
        mov_type="Diagonal")
    mocks_board["mock_get_last_temporary_movements"].return_value = MagicMock(tile1=MagicMock(
        id=1, position_x=0, position_y=0), tile2=MagicMock(id=2, position_x=1, position_y=1), id_mov=1)
    mocks_board["mock_get_board_by_match_id"].return_value = MagicMock(id=1)
    mocks_board["mock_get_formed_figures"].return_value = []
    mocks_board["mock_get_ban_color"].return_value = "red"

    response = client.delete("/matches/1/partial-move/1")

    assert response.status_code == 200
    mocks_tile["mock_update_tile_position"].assert_any_call(1, 1, 1)
    mocks_tile["mock_update_tile_position"].assert_any_call(2, 0, 0)
    mocks_movement_card["mock_add_movement_card_to_player"].assert_called_once()

    expected_calls = [
        call(1, {"key": "UNDO_PARTIAL_MOVE", "payload": {"tiles": [
             {"rowIndex": 0, "columnIndex": 0}, {"rowIndex": 1, "columnIndex": 1}]}}),
        call(1, {"key": "ALLOW_FIGURES", "payload": []})
    ]
    mocks_broadcast["mock_broadcast_to_game"].assert_has_calls(
        expected_calls, any_order=True)


def test_delete_partial_move_match_not_found(setup_match_mocks, client):
    mocks_match = setup_match_mocks
    mocks_match["mock_get_match_by_id"].side_effect = NoResultFound(
        "Match not found")

    response = client.delete("/matches/1/partial-move/1")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Match not found"}


def test_delete_partial_move_player_not_found(setup_player_mocks, setup_match_mocks, client):
    mocks_player = setup_player_mocks
    mocks_match = setup_match_mocks
    mocks_match["mock_get_match_by_id"].return_value = {"id": 1, "name": "Test Match"}
    mocks_player["mock_get_player_by_id"].side_effect = ValueError("Player not found")

    response = client.delete("/matches/1/partial-move/1")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Player not found"}


def test_delete_partial_move_not_player_turn(setup_player_mocks, setup_match_mocks, client):
    mocks_player = setup_player_mocks
    mocks_match = setup_match_mocks

    mocks_player["mock_get_player_by_id"].return_value = MagicMock(
        id=1, player_name="Player 1", match_id=1, is_owner=False, turn_order=2)
    mocks_match["mock_get_match_by_id"].return_value = MagicMock(
        id=1, state="STARTED", current_players=2, current_player_turn=1)

    response = client.delete("/matches/1/partial-move/1")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "It's not player Player 1's turn"}


def test_delete_partial_move_no_movements_to_undo(setup_player_mocks, setup_match_mocks, setup_board_mocks, client):
    mocks_player = setup_player_mocks
    mocks_match = setup_match_mocks
    mocks_board = setup_board_mocks

    mocks_player["mock_get_player_by_id"].return_value = MagicMock(
        id=1, player_name="Player 1", match_id=1, is_owner=True, turn_order=1)
    mocks_match["mock_get_match_by_id"].return_value = MagicMock(
        id=1, state="STARTED", current_players=2, current_player_turn=1)
    mocks_board["mock_get_last_temporary_movements"].return_value = None

    response = client.delete("/matches/1/partial-move/1")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "No movements to undo"}


def test_delete_partial_move_movement_card_not_found(setup_player_mocks, setup_match_mocks, setup_board_mocks, setup_movement_card_mocks, client):
    mocks_player = setup_player_mocks
    mocks_match = setup_match_mocks
    mocks_board = setup_board_mocks
    mocks_movement_card = setup_movement_card_mocks

    mocks_player["mock_get_player_by_id"].return_value = MagicMock(
        id=1, player_name="Player 1", match_id=1, is_owner=True, turn_order=1)
    mocks_match["mock_get_match_by_id"].return_value = MagicMock(
        id=1, state="STARTED", current_players=2, current_player_turn=1)
    mocks_board["mock_get_last_temporary_movements"].return_value = MagicMock(tile1=MagicMock(
        id=1, position_x=0, position_y=0), tile2=MagicMock(id=2, position_x=1, position_y=1), id_mov=1)
    mocks_board["mock_get_board_by_match_id"].return_value = MagicMock(id=1)
    mocks_movement_card["mock_get_movement_card_by_id"].side_effect = NoResultFound(
        "Movement card not found")

    response = client.delete("/matches/1/partial-move/1")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Movement card not found"}


def test_delete_partial_move_tile_not_found(setup_player_mocks, setup_match_mocks, setup_board_mocks, setup_tile_mocks, setup_movement_card_mocks, client):
    mocks_player = setup_player_mocks
    mocks_match = setup_match_mocks
    mocks_board = setup_board_mocks
    mocks_tile = setup_tile_mocks
    mocks_movement_card = setup_movement_card_mocks

    mocks_player["mock_get_player_by_id"].return_value = MagicMock(
        id=1, player_name="Player 1", match_id=1, is_owner=True, turn_order=1)
    mocks_match["mock_get_match_by_id"].return_value = MagicMock(
        id=1, state="STARTED", current_players=2, current_player_turn=1)
    mocks_board["mock_get_last_temporary_movements"].return_value = MagicMock(tile1=MagicMock(
        id=1, position_x=0, position_y=0), tile2=MagicMock(id=2, position_x=1, position_y=1), id_mov=1)
    mocks_board["mock_get_board_by_match_id"].return_value = MagicMock(id=1)
    mocks_movement_card["mock_get_movement_card_by_id"].return_value = MagicMock(
        mov_type="Diagonal")
    mocks_tile["mock_update_tile_position"].side_effect = NoResultFound(
        "Tile not found")

    response = client.delete("/matches/1/partial-move/1")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Tile not found"}


def test_delete_partial_move_formed_figures_error(setup_player_mocks, 
                                                  setup_match_mocks, setup_board_mocks, 
                                                  setup_movement_card_mocks, 
                                                  setup_tile_mocks, 
                                                  setup_broadcast_mocks, client):
    mocks_player = setup_player_mocks
    mocks_match = setup_match_mocks
    mocks_board = setup_board_mocks
    mocks_movement_card = setup_movement_card_mocks
    mocks_tile = setup_tile_mocks
    mocks_broadcast = setup_broadcast_mocks

    mocks_player["mock_get_player_by_id"].return_value = MagicMock(
        id=1, player_name="Player 1", match_id=1, is_owner=True, turn_order=1)
    mocks_match["mock_get_match_by_id"].return_value = MagicMock(
        id=1, state="STARTED", current_players=2, current_player_turn=1)
    mocks_board["mock_get_last_temporary_movements"].return_value = MagicMock(tile1=MagicMock(
        id=1, position_x=0, position_y=0), tile2=MagicMock(id=2, position_x=1, position_y=1), id_mov=1)
    mocks_board["mock_get_board_by_match_id"].return_value = MagicMock(id=1)
    mocks_movement_card["mock_get_movement_card_by_id"].return_value = MagicMock(
        mov_type="Diagonal")
    mocks_board["mock_get_formed_figures"].side_effect = Exception(
        "Error with formed figures")
    mocks_tile["mock_get_tile_by_id"].return_value = MagicMock(
        id=1, position_x=0, position_y=0)
    mocks_broadcast["mock_broadcast_to_game"].return_value = None

    response = client.delete("/matches/1/partial-move/1")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error with formed figures"}


@pytest.mark.asyncio
async def test_owner_leave_match(setup_player_mocks, setup_match_mocks, setup_broadcast_mocks, client):
    mocks_player = setup_player_mocks
    mocks_match = setup_match_mocks
    mocks_broadcast = setup_broadcast_mocks

    owner = MagicMock(id=1, player_name="Owner", match_id=1, is_owner=True)
    player2 = MagicMock(id=2, player_name="Player 2", match_id=1, is_owner=False)
    match = MagicMock(id=1, state="WAITING", current_players=2, players=[owner, player2])

    mocks_player["mock_get_player_by_id"].return_value = owner
    mocks_match["mock_get_match_by_id"].return_value = match

    response = client.delete("/matches/1/left/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "message": "The match has been canceled because the owner has left."
    }
    mocks_broadcast["mock_broadcast_to_game"].assert_called_once_with(1, {
        "key": "PLAYER_LEFT",
        "payload": {
            "owner_name": "Owner",
            "is_owner": True
        }
    })
    mocks_broadcast["mock_disconnect_player_from_game"].assert_called()
    mocks_match["mock_delete_match"].assert_called_once_with(1)

def test_use_figure_without_use_movements(setup_player_mocks, setup_match_mocks, setup_board_mocks, setup_shape_card_mocks, client):
    mocks_player = setup_player_mocks
    mocks_match = setup_match_mocks
    mocks_board = setup_board_mocks
    mocks_shape_card = setup_shape_card_mocks

    owner = MagicMock(id=1, player_name="Owner", turn_order=1,
                      match_id=1, is_owner=True, shape_cards=MagicMock(id=1))
    player2 = MagicMock(id=2, player_name="Player 2",
                        turn_order=2, match_id=1, is_owner=False)

    mocks_match['mock_get_match_by_id'].return_value = MagicMock(
        id=1, current_players=2, current_player_turn=1, players=[owner, player2])
    mocks_player['mock_get_player_by_id'].return_value = owner
    mocks_board['mock_get_board_by_id'].return_value = MagicMock(id=1, match_id=1, temporary_movements=[MagicMock(
        id_mov=1, tile1=MagicMock(position_x=0, position_y=0), tile2=MagicMock(position_x=1, position_y=1))])
    mocks_shape_card["delete_shape_card"].return_value = None

    valid_coordinates = FIGURE_COORDINATES["MINI_LINE"]
    mocks_board['mock_get_formed_figures'].return_value = [valid_coordinates, rotate_90_degrees(
        valid_coordinates, (6, 6)), rotate_180_degrees(valid_coordinates, (6, 6)), rotate_270_degrees(valid_coordinates, (6, 6))]

    response = client.post("/matches/1/player/1/use-figure",
                           json={"figure_id": 1, "coordinates": [[0, 1], [0, 2], [0, 3], [0, 4]]})
    print(response.json())
    assert (response.status_code == 409)
    assert (response.json() == {"detail": "Conflict with coordinates and Figure Card"})


def test_use_figure_with_movement_return(setup_player_mocks, setup_match_mocks, setup_board_mocks, setup_movement_card_mocks, setup_shape_card_mocks, client):
    mocks_player = setup_player_mocks
    mocks_match = setup_match_mocks
    mocks_board = setup_board_mocks
    mocks_movement_card = setup_movement_card_mocks
    mocks_shape_card = setup_shape_card_mocks

    owner = MagicMock(id=1, player_name="Owner",
                      turn_order=1, match_id=1, is_owner=True)
    player2 = MagicMock(id=2, player_name="Player 2",
                        turn_order=2, match_id=1, is_owner=False)

    mocks_match['mock_get_match_by_id'].return_value = MagicMock(
        id=1, current_players=2, current_player_turn=1, players=[owner, player2])
    mocks_player['mock_get_player_by_id'].return_value = owner
    mocks_board['mock_get_board_by_id'].return_value = MagicMock(
        id=1, match_id=1, temporary_movements=[any])
    valid_coordinates = FIGURE_COORDINATES["MINI_LINE"]
    mocks_board['mock_get_formed_figures'].return_value = [valid_coordinates, rotate_90_degrees(
        valid_coordinates, (6, 6)), rotate_180_degrees(valid_coordinates, (6, 6)), rotate_270_degrees(valid_coordinates, (6, 6))]
    mocks_board["mock_get_last_temporary_movements"].return_value = MagicMock(
        id_mov=1, create_figure=False, tile1=MagicMock(position_x=0, position_y=0), tile2=MagicMock(position_x=1, position_y=1))
    mocks_movement_card['mock_get_movement_card_by_id'].return_value = MagicMock(
        id=1, mov_type=1)
    mocks_shape_card["delete_shape_card"].return_value = None

    response = client.post("/matches/1/player/1/use-figure",
                           json={"figure_id": 1, "coordinates": [[0, 1], [0, 2], [0, 3], [0, 4]]})
    print(response.json())
    assert (response.status_code == 409)
    assert (response.json() == {"detail": "Conflict with coordinates and Figure Card"})