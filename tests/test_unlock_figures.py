import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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

        shape_card_service.get_visible_cards.assert_not_called()
        

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
    shape_card.is_visible = True
    shape_card2 = MagicMock()
    shape_card2.is_blocked = "BLOCKED"
    shape_card2.id = 2
    shape_card2.shape_type = "Figura2"
    shape_card2.is_visible = True
    db = MagicMock()
    player_id = 1
    match_id = 1

    visible_cards = [
        shape_card,
        shape_card2,
    ]

    with patch('app.routers.players.ShapeCardService') as MockShapeCardService, \
        patch('app.routers.players.manager') as MockManager:

        shape_card_service = MockShapeCardService.return_value
        shape_card_service.get_visible_cards.return_value = visible_cards

        # Aquí configuramos broadcast_to_game como AsyncMock
        MockManager.broadcast_to_game = AsyncMock()

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
         patch('app.routers.players.manager') as MockManager:
        shape_card_service = MockShapeCardService.return_value
        shape_card_service.get_visible_cards.return_value = visible_cards

        await unlock_figures(shape_card, player_id, match_id, db)

        shape_card_service.update_shape_card.assert_not_called()
        MockManager.broadcast_to_game.assert_not_called()
