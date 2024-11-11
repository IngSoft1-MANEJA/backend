import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.routers.players import undo_partials_movements
from app.cruds.board import BoardService
from app.cruds.tile import TileService
from app.cruds.movement_card import MovementCardService
from app.connection_manager import manager
import asyncio

@pytest.mark.asyncio
async def test_undo_partials_movements_no_temporary_movements():
    board = MagicMock()
    board.id = 1
    board.temporary_movements = []

    player_id = 1
    match_id = 1
    db = MagicMock()

    with patch('app.routers.players.BoardService') as MockBoardService, \
         patch('app.routers.players.TileService') as MockTileService, \
         patch('app.routers.players.MovementCardService') as MockMovementCardService, \
         patch('app.routers.players.manager') as mock_manager, \
         patch('asyncio.sleep', new_callable=AsyncMock):
        
        board_service = MockBoardService.return_value
        tile_service = MockTileService.return_value
        movement_card_service = MockMovementCardService.return_value
        mock_manager.broadcast_to_game = AsyncMock()

        result = await undo_partials_movements(board, player_id, match_id, db)

        assert result == []
        board_service.get_last_temporary_movements.assert_not_called()
        tile_service.update_tile_position.assert_not_called()
        movement_card_service.get_movement_card_by_id.assert_not_called()
        movement_card_service.add_movement_card_to_player.assert_not_called()
        mock_manager.broadcast_to_game.assert_not_called()

@pytest.mark.asyncio
async def test_undo_partials_movements_tiles_empty():
    board = MagicMock()
    board.id = 1
    board.temporary_movements = []

    player_id = 1
    match_id = 1
    db = MagicMock()

    with patch('app.routers.players.BoardService') as MockBoardService, \
         patch('app.routers.players.manager') as mock_manager, \
         patch('asyncio.sleep', new_callable=AsyncMock):

        board_service = MockBoardService.return_value
        mock_manager.broadcast_to_game = AsyncMock()

        result = await undo_partials_movements(board, player_id, match_id, db)

        assert result == []
        mock_manager.broadcast_to_game.assert_not_called()

@pytest.mark.asyncio
async def test_undo_partials_movements_exception_handling():
    board = MagicMock()
    board.id = 1
    board.temporary_movements = [MagicMock()]

    player_id = 1
    match_id = 1
    db = MagicMock()

    with patch('app.routers.players.BoardService') as MockBoardService, \
         patch('app.routers.players.manager') as mock_manager, \
         patch('asyncio.sleep', new_callable=AsyncMock):

        board_service = MockBoardService.return_value
        board_service.get_last_temporary_movements.side_effect = Exception("Error")
        mock_manager.broadcast_to_game = AsyncMock()

        with pytest.raises(Exception) as e:
            await undo_partials_movements(board, player_id, match_id, db)

        assert str(e.value) == "Error"