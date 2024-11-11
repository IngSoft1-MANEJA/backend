import pytest
from unittest.mock import MagicMock, patch
from app.models import ShapeCards
from app.routers.players import unlock_figures
from app.cruds.shape_card import ShapeCardService
from app.connection_manager import manager
from asyncio import Future

@pytest.mark.asyncio
async def test_unlock_figures_shape_card_blocked():
    shape_card = MagicMock()
    shape_card.is_blocked = "BLOCKED"  
    db = MagicMock()
    player_id = 1
    match_id = 1

    with patch('app.cruds.shape_card.ShapeCardService') as MockShapeCardService:
        shape_card_service = MockShapeCardService.return_value

        await unlock_figures(shape_card, player_id, match_id, db)

        shape_card_service.get_visible_cards.assert_not_called()
        

@pytest.mark.asyncio
async def test_unlock_figures_no_visible_cards():
    shape_card = MagicMock()
    shape_card.is_blocked = "NOT_BLOCKED"
    shape_card.id = 1
    shape_card.shape_type = "Figura1"
    db = MagicMock()
    player_id = 1
    match_id = 1

    with patch('app.cruds.shape_card.ShapeCardService') as MockShapeCardService:
        shape_card_service = MockShapeCardService.return_value
        shape_card_service.get_visible_cards.return_value = []

        await unlock_figures(shape_card, player_id, match_id, db)

        shape_card_service.get_visible_cards.assert_called_once_with(player_id, True)
        

@pytest.mark.asyncio
async def test_unlock_figures_no_cards_satisfy_conditions():
    shape_card = MagicMock()
    shape_card.is_blocked = "NOT_BLOCKED"
    shape_card.id = 1
    shape_card.shape_type = "Figura1"
    db = MagicMock()
    player_id = 1
    match_id = 1

    visible_cards = [
        MagicMock(id=2, is_visible=True, is_blocked="NOT_BLOCKED", shape_type="Figura2"),
        MagicMock(id=3, is_visible=False, is_blocked="BLOCKED", shape_type="Figura3"),
    ]

    with patch('app.cruds.shape_card.ShapeCardService') as MockShapeCardService:
        shape_card_service = MockShapeCardService.return_value
        shape_card_service.get_visible_cards.return_value = visible_cards

        await unlock_figures(shape_card, player_id, match_id, db)

        shape_card_service.update_shape_card.assert_not_called()
       

@pytest.mark.asyncio
async def test_unlock_figures_unlocks_card():
    shape_card = MagicMock()
    shape_card.is_blocked = "NOT_BLOCKED"
    shape_card.id = 1
    shape_card.shape_type = "Figura1"
    db = MagicMock()
    player_id = 1
    match_id = 1

    visible_cards = [
        MagicMock(id=2, is_visible=True, is_blocked="BLOCKED", shape_type="Figura2"),
        MagicMock(id=3, is_visible=True, is_blocked="NOT_BLOCKED", shape_type="Figura3"),
    ]

    with patch('app.cruds.shape_card.ShapeCardService') as MockShapeCardService, \
         patch('app.api.websocket.manager') as MockManager:
        shape_card_service = MockShapeCardService.return_value
        shape_card_service.get_visible_cards.return_value = visible_cards

        future = Future()
        future.set_result(None)
        MockManager.broadcast_to_game.return_value = future

        await unlock_figures(shape_card, player_id, match_id, db)

        shape_card_service.update_shape_card.assert_called_once_with(2, True, "UNLOCKED")
        msg = {"key": "UNLOCK_FIGURE", "payload": {"figure_id": 2}}
        MockManager.broadcast_to_game.assert_awaited_once_with(match_id, msg)

@pytest.mark.asyncio
async def test_unlock_figures_visible_cards_length_not_two():
    shape_card = MagicMock()
    shape_card.is_blocked = "NOT_BLOCKED"
    shape_card.id = 1
    shape_card.shape_type = "Figura1"
    db = MagicMock()
    player_id = 1
    match_id = 1

    visible_cards = [
        MagicMock(id=2, is_visible=True, is_blocked="BLOCKED", shape_type="Figura2"),
        MagicMock(id=3, is_visible=True, is_blocked="NOT_BLOCKED", shape_type="Figura3"),
        MagicMock(id=4, is_visible=True, is_blocked="NOT_BLOCKED", shape_type="Figura4"),
    ]

    with patch('app.cruds.shape_card.ShapeCardService') as MockShapeCardService, \
         patch('app.api.websocket.manager') as MockManager:
        shape_card_service = MockShapeCardService.return_value
        shape_card_service.get_visible_cards.return_value = visible_cards

        await unlock_figures(shape_card, player_id, match_id, db)

        shape_card_service.update_shape_card.assert_not_called()
        MockManager.broadcast_to_game.assert_not_called()

@pytest.mark.asyncio
async def test_unlock_figures_multiple_cards_unlocked():
    shape_card = MagicMock()
    shape_card.is_blocked = "NOT_BLOCKED"
    shape_card.id = 1
    shape_card.shape_type = "Figura1"
    db = MagicMock()
    player_id = 1
    match_id = 1

    visible_cards = [
        MagicMock(id=2, is_visible=True, is_blocked="BLOCKED", shape_type="Figura2"),
        MagicMock(id=3, is_visible=True, is_blocked="BLOCKED", shape_type="Figura3"),
    ]

    with patch('app.cruds.shape_card.ShapeCardService') as MockShapeCardService, \
         patch('app.api.websocket.manager') as MockManager:
        shape_card_service = MockShapeCardService.return_value
        shape_card_service.get_visible_cards.return_value = visible_cards

        future = Future()
        future.set_result(None)
        MockManager.broadcast_to_game.return_value = future

        await unlock_figures(shape_card, player_id, match_id, db)

        assert shape_card_service.update_shape_card.call_count == 2
        shape_card_service.update_shape_card.assert_any_call(2, True, "UNLOCKED")
        shape_card_service.update_shape_card.assert_any_call(3, True, "UNLOCKED")

        msg1 = {"key": "UNLOCK_FIGURE", "payload": {"figure_id": 2}}
        msg2 = {"key": "UNLOCK_FIGURE", "payload": {"figure_id": 3}}
        assert MockManager.broadcast_to_game.await_count == 2
        MockManager.broadcast_to_game.assert_any_await(match_id, msg1)
        MockManager.broadcast_to_game.assert_any_await(match_id, msg2)