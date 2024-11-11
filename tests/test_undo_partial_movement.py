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
async def test_undo_partials_movements_with_movements_no_create_figure():
    board = MagicMock()
    board.id = 1
    board.temporary_movements = [MagicMock(), MagicMock()]

    player_id = 1
    match_id = 1
    db = MagicMock()

    movement1 = MagicMock()
    movement1.create_figure = False
    movement1.tile1 = MagicMock(id=1, position_x=0, position_y=0)
    movement1.tile2 = MagicMock(id=2, position_x=1, position_y=1)
    movement1.id_mov = 10

    movement2 = MagicMock()
    movement2.create_figure = False
    movement2.tile1 = MagicMock(id=3, position_x=2, position_y=2)
    movement2.tile2 = MagicMock(id=4, position_x=3, position_y=3)
    movement2.id_mov = 20

    movements_list = [movement1, movement2]
    movements_iter = iter(movements_list)

    def mock_get_last_temporary_movements(board_id):
        return next(movements_iter)

    with patch('app.routers.players.BoardService') as MockBoardService, \
         patch('app.routers.players.TileService') as MockTileService, \
         patch('app.routers.players.MovementCardService') as MockMovementCardService, \
         patch('app.routers.players.manager') as mock_manager, \
         patch('copy.copy', side_effect=lambda x: x), \
         patch('asyncio.sleep', new_callable=AsyncMock):
        
        board_service = MockBoardService.return_value
        board_service.get_last_temporary_movements.side_effect = mock_get_last_temporary_movements
        tile_service = MockTileService.return_value
        movement_card_service = MockMovementCardService.return_value
        mock_manager.broadcast_to_game = AsyncMock()

        movement_card_service.get_movement_card_by_id.side_effect = lambda id: MagicMock(id=id, mov_type='SWAP')

        result = await undo_partials_movements(board, player_id, match_id, db)

        assert result == [(10, 'SWAP'), (20, 'SWAP')]
        assert board_service.get_last_temporary_movements.call_count == 2
        assert movement_card_service.add_movement_card_to_player.call_count == 2
        assert tile_service.update_tile_position.call_count == 4  # Two updates per movement
        assert mock_manager.broadcast_to_game.call_count == 1

@pytest.mark.asyncio
async def test_undo_partials_movements_with_create_figure():
    board = MagicMock()
    board.id = 1
    board.temporary_movements = [MagicMock(), MagicMock()]

    player_id = 1
    match_id = 1
    db = MagicMock()

    movement1 = MagicMock()
    movement1.create_figure = False
    movement1.tile1 = MagicMock(id=1, position_x=0, position_y=0)
    movement1.tile2 = MagicMock(id=2, position_x=1, position_y=1)
    movement1.id_mov = 10

    movement2 = MagicMock()
    movement2.create_figure = True  # Should break the loop
    movement2.tile1 = MagicMock(id=3, position_x=2, position_y=2)
    movement2.tile2 = MagicMock(id=4, position_x=3, position_y=3)
    movement2.id_mov = 20

    movements_list = [movement1, movement2]
    movements_iter = iter(movements_list)

    def mock_get_last_temporary_movements(board_id):
        return next(movements_iter)

    with patch('app.routers.players.BoardService') as MockBoardService, \
         patch('app.routers.players.TileService') as MockTileService, \
         patch('app.routers.players.MovementCardService') as MockMovementCardService, \
         patch('app.routers.players.manager') as mock_manager, \
         patch('copy.copy', side_effect=lambda x: x), \
         patch('asyncio.sleep', new_callable=AsyncMock):
        
        board_service = MockBoardService.return_value
        board_service.get_last_temporary_movements.side_effect = mock_get_last_temporary_movements
        tile_service = MockTileService.return_value
        movement_card_service = MockMovementCardService.return_value
        mock_manager.broadcast_to_game = AsyncMock()

        movement_card_service.get_movement_card_by_id.return_value = MagicMock(id=10, mov_type='SWAP')

        result = await undo_partials_movements(board, player_id, match_id, db)

        assert result == [(10, 'SWAP')]
        assert board_service.get_last_temporary_movements.call_count == 1
        movement_card_service.add_movement_card_to_player.assert_called_once_with(player_id, 10)
        assert tile_service.update_tile_position.call_count == 2
        mock_manager.broadcast_to_game.assert_called_once()

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