import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm.exc import NoResultFound
from app.main import app
from app.models.enums import HardShapes, EasyShapes
from app.schemas import UseFigure
from app.routers.players import block_figure
from app.utils.board_shapes_algorithm import rotate_90_degrees, rotate_180_degrees, rotate_270_degrees
from app.utils.utils import FIGURE_COORDINATES

client = TestClient(app)

@pytest.fixture
def setup_mocks():
    with patch("app.routers.players.MatchService") as mock_match_service, \
         patch("app.routers.players.PlayerService") as mock_player_service, \
         patch("app.routers.players.ShapeCardService") as mock_shape_card_service, \
         patch("app.routers.players.BoardService") as mock_board_service, \
         patch("app.routers.players.manager.broadcast_to_game", new_callable=AsyncMock) as mock_broadcast_to_game, \
         patch("app.routers.players.undo_partials_movements") as mock_undo_partials_movements, \
         patch("app.routers.players.rotate_90_degrees") as mock_rotate_90_degrees, \
         patch("app.routers.players.rotate_180_degrees") as mock_rotate_180_degrees, \
         patch("app.routers.players.rotate_270_degrees") as mock_rotate_270_degrees, \
         patch("app.routers.players.check_ban_color") as mock_check_ban_color, \
         patch("app.cruds.tile.TileService.get_tile_by_position") as mock_get_tile_by_position:
        
        yield {
            "mock_match_service": mock_match_service,
            "mock_player_service": mock_player_service,
            "mock_shape_card_service": mock_shape_card_service,
            "mock_board_service": mock_board_service,
            "mock_broadcast_to_game": mock_broadcast_to_game,
            "mock_undo_partials_movements": mock_undo_partials_movements,
            "mock_rotate_90_degrees": mock_rotate_90_degrees,
            "mock_rotate_180_degrees": mock_rotate_180_degrees,
            "mock_rotate_270_degrees": mock_rotate_270_degrees,
            "mock_check_ban_color": mock_check_ban_color,
            "mock_get_tile_by_position": mock_get_tile_by_position
        }

# @pytest.mark.asyncio
# async def test_block_figure_success(setup_mocks):
#     mocks = setup_mocks
#     match = MagicMock(id=1, current_player_turn=1, current_players=[1, 2])
#     player = MagicMock(id=1, turn_order=1, player_name="Player 1")
#     shape_card = MagicMock(id=1, is_visible=True, player_owner=1, is_blocked="NOT BLOCKED", is_hard=False, shape_type= 20)
#     board = MagicMock(id=1)
#     valid_coordinates = FIGURE_COORDINATES["MINI_LINE"]

#     mocks["mock_match_service"].return_value.get_match_by_id.return_value = match
#     mocks["mock_player_service"].return_value.get_player_by_id.return_value = player
#     mocks["mock_shape_card_service"].return_value.get_shape_card_by_id.return_value = shape_card
#     mocks["mock_shape_card_service"].return_value.get_shape_card_by_player.return_value = [shape_card, shape_card, shape_card]
#     mocks["mock_board_service"].return_value.get_board_by_id.return_value = board
#     mocks["mock_board_service"].return_value.get_formed_figures.return_value = [valid_coordinates, rotate_90_degrees(
#         valid_coordinates, (6, 6)), rotate_180_degrees(valid_coordinates, (6, 6)), rotate_270_degrees(valid_coordinates, (6, 6))]

#     request_data = {
#         "figure_id": 1,
#         "coordinates": [(5, 0), (5, 1), (5, 2), (5, 3   )]
#     }

#     response = client.post("/matches/1/player/1/block-figure", json=request_data)

#     assert response.status_code == 200
#     mocks["mock_match_service"].return_value.get_match_by_id.assert_called_once_with(1)
#     mocks["mock_player_service"].return_value.get_player_by_id.assert_called_once_with(1)
#     mocks["mock_shape_card_service"].return_value.get_shape_card_by_id.assert_called_once_with(1)
#     mocks["mock_shape_card_service"].return_value.update_shape_card.assert_called_once_with(1, True, "BLOCKED")
#     mocks["mock_broadcast_to_game"].assert_called()

@pytest.mark.asyncio
async def test_block_figure_match_not_found(setup_mocks):
    mocks = setup_mocks
    mocks["mock_match_service"].return_value.get_match_by_id.side_effect = NoResultFound

    request_data = {
        "figure_id": 1,
        "coordinates": [(0, 0), (1, 0), (2, 0), (3, 0)]
    }

    response = client.post("/matches/1/player/1/block-figure", json=request_data)

    assert response.status_code == 404
    assert response.json() == {"detail": "Match not found"}

@pytest.mark.asyncio
async def test_block_figure_player_not_found(setup_mocks):
    mocks = setup_mocks
    match = MagicMock(id=1, current_player_turn=1)
    mocks["mock_match_service"].return_value.get_match_by_id.return_value = match
    mocks["mock_player_service"].return_value.get_player_by_id.side_effect = ValueError

    request_data = {
        "figure_id": 1,
        "coordinates": [(0, 0), (1, 0), (2, 0), (3, 0)]
    }

    response = client.post("/matches/1/player/1/block-figure", json=request_data)

    assert response.status_code == 404
    assert response.json() == {"detail": "Player not found"}

@pytest.mark.asyncio
async def test_block_figure_not_player_turn(setup_mocks):
    mocks = setup_mocks
    match = MagicMock(id=1, current_player_turn=2)
    player = MagicMock(id=1, turn_order=1, player_name="Player 1")
    mocks["mock_match_service"].return_value.get_match_by_id.return_value = match
    mocks["mock_player_service"].return_value.get_player_by_id.return_value = player

    request_data = {
        "figure_id": 1,
        "coordinates": [(0, 0), (1, 0), (2, 0), (3, 0)]
    }

    response = client.post("/matches/1/player/1/block-figure", json=request_data)

    assert response.status_code == 403
    assert response.json() == {"detail": "It's not player Player 1's turn"}

@pytest.mark.asyncio
async def test_block_figure_card_not_found(setup_mocks):
    mocks = setup_mocks
    match = MagicMock(id=1, current_player_turn=1)
    player = MagicMock(id=1, turn_order=1)
    mocks["mock_match_service"].return_value.get_match_by_id.return_value = match
    mocks["mock_player_service"].return_value.get_player_by_id.return_value = player
    mocks["mock_shape_card_service"].return_value.get_shape_card_by_id.side_effect = NoResultFound

    request_data = {
        "figure_id": 1,
        "coordinates": [(0, 0), (1, 0), (2, 0), (3, 0)]
    }

    response = client.post("/matches/1/player/1/block-figure", json=request_data)

    assert response.status_code == 404
    assert response.json() == {"detail": "Figure Card not found"}

@pytest.mark.asyncio
async def test_block_figure_card_not_visible(setup_mocks):
    mocks = setup_mocks
    match = MagicMock(id=1, current_player_turn=1, current_players=[1, 2])
    player = MagicMock(id=1, turn_order=1)
    shape_card = MagicMock(id=1, is_visible=False, player_owner=1)
    mocks["mock_match_service"].return_value.get_match_by_id.return_value = match
    mocks["mock_player_service"].return_value.get_player_by_id.return_value = player
    mocks["mock_shape_card_service"].return_value.get_shape_card_by_id.return_value = shape_card

    request_data = {
        "figure_id": 1,
        "coordinates": [(0, 0), (1, 0), (2, 0), (3, 0)]
    }

    response = client.post("/matches/1/player/1/block-figure", json=request_data)

    assert response.status_code == 404
    assert response.json() == {"detail": "Figure card doesn't belong to this match"}

@pytest.mark.asyncio
async def test_block_figure_card_already_blocked(setup_mocks):
    mocks = setup_mocks
    match = MagicMock(id=1, current_player_turn=1, current_players=[1, 2])
    player1 = MagicMock(id=1, turn_order=1)
    player2 = MagicMock(id =2, turn_order= 2)
    shape_card = MagicMock(id=1, is_visible=True, player_owner=1, is_blocked="BLOCKED")
    mocks["mock_match_service"].return_value.get_match_by_id.return_value = match
    mocks["mock_player_service"].return_value.get_player_by_id.return_value = player1
    mocks["mock_shape_card_service"].return_value.get_shape_card_by_id.return_value = shape_card
    mocks["mock_player_service"].return_value.get_players_by_match.return_value = [player1, player2]
    mocks["mock_player_service"].return_value.get_player_by_id.return_value = player1

    request_data = {
        "figure_id": 1,
        "coordinates": [(0, 0), (1, 0), (2, 0), (3, 0)]
    }

    response = client.post("/matches/1/player/1/block-figure", json=request_data)

    assert response.status_code == 400
    assert response.json() == {"detail": "Figure card is already blocked"}

@pytest.mark.asyncio
async def test_block_figure_not_enough_cards(setup_mocks):
    mocks = setup_mocks
    match = MagicMock(id=1, current_player_turn=1, current_players=[1, 2])
    player1 = MagicMock(id=1, turn_order=1)
    player2 = MagicMock(id =2, turn_order= 2)
    shape_card = MagicMock(id=1, is_visible=True, player_owner=1, is_blocked="NOT_BLOCKED")
    mocks["mock_match_service"].return_value.get_match_by_id.return_value = match
    mocks["mock_player_service"].return_value.get_player_by_id.return_value = player1
    mocks["mock_shape_card_service"].return_value.get_shape_card_by_id.return_value = shape_card
    mocks["mock_shape_card_service"].return_value.get_shape_card_by_player.return_value = [shape_card, shape_card]
    mocks["mock_player_service"].return_value.get_players_by_match.return_value = [player1, player2]
    mocks["mock_player_service"].return_value.get_player_by_id.return_value = player1

    request_data = {
        "figure_id": 1,
        "coordinates": [(0, 0), (1, 0), (2, 0), (3, 0)]
    }

    response = client.post("/matches/1/player/1/block-figure", json=request_data)

    assert response.status_code == 400
    assert response.json() == {"detail": "Player must have at least 3 figure cards to block one"}

@pytest.mark.asyncio
async def test_block_figure_not_enough_not_blocked_cards(setup_mocks):
    mocks = setup_mocks
    match = MagicMock(id=1, current_player_turn=1, current_players=[1, 2])
    player1 = MagicMock(id=1, turn_order=1)
    player2 = MagicMock(id =2, turn_order= 2)
    shape_card = MagicMock(id=1, is_visible=True, player_owner=1, is_blocked="NOT_BLOCKED")
    blocked_card = MagicMock(id=2, is_visible=True, player_owner=1, is_blocked="BLOCKED")
    mocks["mock_match_service"].return_value.get_match_by_id.return_value = match
    mocks["mock_player_service"].return_value.get_player_by_id.return_value = player1
    mocks["mock_shape_card_service"].return_value.get_shape_card_by_id.return_value = shape_card
    mocks["mock_shape_card_service"].return_value.get_shape_card_by_player.return_value = [shape_card, shape_card, blocked_card]
    mocks["mock_player_service"].return_value.get_players_by_match.return_value = [player1, player2]
    mocks["mock_player_service"].return_value.get_player_by_id.return_value = player1

    request_data = {
        "figure_id": 1,
        "coordinates": [(0, 0), (1, 0), (2, 0), (3, 0)]
    }

    response = client.post("/matches/1/player/1/block-figure", json=request_data)

    assert response.status_code == 400
    assert response.json() == {"detail": "Player must have 3 not blocked cards"}

@pytest.mark.asyncio
async def test_block_figure_board_not_found(setup_mocks):
    mocks = setup_mocks
    match = MagicMock(id=1, current_player_turn=1, current_players=[1, 2])
    player1 = MagicMock(id=1, turn_order=1)
    player2 = MagicMock(id =2, turn_order= 2)
    shape_card = MagicMock(id=1, is_visible=True, player_owner=1, is_blocked="NOT_BLOCKED", shape_type= 17)
    mocks["mock_match_service"].return_value.get_match_by_id.return_value = match
    mocks["mock_player_service"].return_value.get_player_by_id.return_value = player1
    mocks["mock_shape_card_service"].return_value.get_shape_card_by_id.return_value = shape_card
    mocks["mock_shape_card_service"].return_value.get_shape_card_by_player.return_value = [shape_card, shape_card, shape_card]
    mocks["mock_board_service"].return_value.get_board_by_id.side_effect = NoResultFound
    mocks["mock_player_service"].return_value.get_players_by_match.return_value = [player1, player2]
    mocks["mock_player_service"].return_value.get_player_by_id.return_value = player1
    mocks["mock_check_ban_color"].return_value = "YELLOW"
    mocks["mock_get_tile_by_position"].return_value = MagicMock(id=1, color="YELLOW")
    
    request_data = {
        "figure_id": 1,
        "coordinates": [(0, 0), (1, 0), (2, 0), (3, 0)]
    }

    response = client.post("/matches/1/player/1/block-figure", json=request_data)

    assert response.status_code == 404
    assert response.json() == {"detail": "Board not found"}

@pytest.mark.asyncio
async def test_block_figure_conflict_with_coordinates(setup_mocks):
    mocks = setup_mocks
    match = MagicMock(id=1, current_player_turn=1, current_players=[1, 2])
    player1 = MagicMock(id=1, turn_order=1)
    player2 = MagicMock(id =2, turn_order= 2)
    shape_card = MagicMock(id=1, is_visible=True, player_owner=1, is_blocked="NOT_BLOCKED", shape_type=8)
    board = MagicMock(id=1)
    figures_found = [((0, 0), (1, 0), (1, 1), (0, 1))]

    mocks["mock_match_service"].return_value.get_match_by_id.return_value = match
    mocks["mock_player_service"].return_value.get_player_by_id.return_value = player1
    mocks["mock_shape_card_service"].return_value.get_shape_card_by_id.return_value = shape_card
    mocks["mock_shape_card_service"].return_value.get_shape_card_by_player.return_value = [shape_card, shape_card, shape_card]
    mocks["mock_board_service"].return_value.get_board_by_id.return_value = board
    mocks["mock_board_service"].return_value.get_formed_figures.return_value = figures_found
    mocks["mock_rotate_90_degrees"].return_value = figures_found
    mocks["mock_rotate_180_degrees"].return_value = figures_found
    mocks["mock_rotate_270_degrees"].return_value = figures_found
    mocks["mock_player_service"].return_value.get_players_by_match.return_value = [player1, player2]
    mocks["mock_player_service"].return_value.get_player_by_id.return_value = player1

    request_data = {
        "figure_id": 1,
        "coordinates": [(0, 0), (1, 0), (2, 0), (3, 0)]
    }

    response = client.post("/matches/1/player/1/block-figure", json=request_data)

    assert response.status_code == 409
    assert response.json() == {"detail": "Conflict with coordinates and Figure Card"}