from asyncio import sleep
from copy import copy
from datetime import datetime, timedelta
import os
from random import randint

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.connection_manager import manager
from app.cruds.board import BoardService
from app.cruds.match import MatchService
from app.cruds.movement_card import MovementCardService
from app.cruds.player import PlayerService
from app.cruds.shape_card import ShapeCardService
from app.cruds.tile import TileService
from app.cruds.board import BoardService
from app.cruds.shape_card import ShapeCardService
from app.connection_manager import manager
from app.database import get_db
from app.exceptions import *
from app.logger import logging
from app.models import enums
from app.models.enums import EasyShapes, HardShapes, ReasonWinning
from app.models.models import Matches, Players
from app.schemas import PartialMove, UseFigure
from app.utils.board_shapes_algorithm import (Coordinate, Figure,
                                              rotate_90_degrees,
                                              rotate_180_degrees,
                                              rotate_270_degrees,
                                              translate_shape_to_bottom_left)
from app.utils.utils import (FIGURE_COORDINATES, validate_diagonal,
                             validate_inverse_diagonal, validate_inverse_l,
                             validate_l, validate_line, validate_line_between,
                             validate_line_border)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matches")


async def notify_movement_card_to_player(player_id: int, match_id: int, buff_movement: list[tuple[int, str]]):
    """
        Notifica al jugador que se le dio una carta de movimiento.
        Args:
            - player_id : id del jugador.
            - match_id : id de la partida.
            - buff_movement : lista de tuplas con el id y tipo de movimiento.
        Returns:
            None, se comunica mediante websockets.
    """
    msg_user = {"key": "GET_MOVEMENT_CARD",
                "payload": {"movement_card": buff_movement}}
    await manager.send_to_player(match_id, player_id, msg_user)


async def notify_all_players_movements_received(player: Players, match: Matches):
    """
        Notifica a los demás jugadores que un jugador recibió una carta de movimiento.
        Args:
            - player : jugador que recibió la carta.
            - match : partida en la que se encuentra.
        Returns:
            None, se comunica mediante websockets.
    """
    for player_i in match.players:
        if player_i.id != player.id:
            msg_all = {"key": "PLAYER_RECEIVE_MOVEMENT_CARD",
                       "payload": {"player": player.player_name}}
            await manager.send_to_player(match.id, player_i.id, msg_all)


async def give_shape_card_to_player(player_id: int, db: Session, is_init: bool):
    """
        Da hasta 3 cartas de figuras al jugador.

        Args:
            - player_id : id del jugador.
            - db : Session de la base de datos.
            - is_init : booleano que indica si es el inicio de la partida.
    """
    player_service = PlayerService(db)
    shape_card_service = ShapeCardService(db)

    player = player_service.get_player_by_id(player_id)
    visible_cards = shape_card_service.get_visible_cards(player_id, True)
    ShapeDeck = shape_card_service.get_visible_cards(player_id, False)
    CardsToGive = 3 - len(visible_cards)
    ShapesGiven = []
    for i in range(CardsToGive):
        if not ShapeDeck:
            break  # No hay más cartas en el mazo
        shape = ShapeDeck.pop(randint(0, len(ShapeDeck) - 1))
        shape_card_service.update_shape_card(shape.id, True, False)
        ShapesGiven.append((shape.id, shape.shape_type))
    if not is_init:
        msg_all = {"key": "PLAYER_RECEIVE_SHAPE_CARD",
                   "payload": [{"player": player.player_name, "turn_order": player.turn_order, "shape_cards": ShapesGiven}]}
        await manager.broadcast_to_game(player.match_id, msg_all)


async def playerWinner(match_id: int, reason: ReasonWinning, db: Session):
    match_service = MatchService(db)
    player_service = PlayerService(db)

    players = player_service.get_players_by_match(match_id)[0]
    player_id = players.id
    player_service.delete_player(player_id)
    match_service.update_match(match_id, "FINISHED", 0)
    reason_winning = reason.value

    msg = {"key": "WINNER", "payload": {
        "player_id": player_id, "reason": reason_winning}}

    try:
        await manager.broadcast_to_game(match_id, msg)
    except RuntimeError as e:
        # Manejar el caso en que el WebSocket ya esté cerrado
        logger.error("Error al enviar mensaje: %s", e)
     


async def player_winner_by_no_shapes(player_winner: Players, match: Matches, db: Session):
    """
        Esta funcion maneja el caso en el que un jugador gana por no tener mas 
        figuras
        Args:
            - player_winner: Jugador ganador
            - match: Partida
            - db: Session de la base de datos
        Returns:
            - None, notifica a los jugadores que el jugador ha ganado
    """   
    cant_shapes = len(ShapeCardService(db).get_shape_card_by_player(player_winner.id))
    
    if cant_shapes == 0:
        msg_win = {
            "key" : "WINNER",
            "payload": {
                "player_id": player_winner.id,
                "reason": "NORMAL"
            }
        }
        PlayerService(db).delete_player(player_winner.id)
        MatchService(db).update_match(match.id, "FINISHED", 0)
        try:
            await manager.broadcast_to_game(match.id, msg_win)
        except RuntimeError as e:
            print(f"Error al enviar mensaje: {e}")

def end_turn_logic(player: Players, match: Matches, db: Session):
    match_service = MatchService(db)
    player_service = PlayerService(db)

    if player.turn_order != match.current_player_turn:
        raise HTTPException(
            status_code=403, detail=f"It's not player {player.player_name}'s turn")

    active_players = player_service.get_players_by_match(match.id)
    # Ordeno la lista por orden de turnos
    active_players.sort(key=lambda p: p.turn_order)
    next_player = None

    for p in active_players:  # For para encontrar el siguiente turno
        if p.turn_order > match.current_player_turn:
            next_player = p
            break
    # Si no hay es porque el siguiente jugador es el primero
    if not next_player:
        next_player = active_players[0]

    match_service.update_turn(match.id, next_player.turn_order)

    return next_player


async def owner_leave(owner: Players, match: Matches, db: Session):
    """
    Handles the owner leaving the match:
        - If the match has not started, notify other players that the owner has left.
          Then delete the match.
    Args:
        owner (Players): The owner player of the match.
        match (Matches): The match the player belongs to.
        db (Session): Database session.
    Returns:
        dict: Message indicating the match has been canceled.
    """
    match_service = MatchService(db)

    # Disconnect the owner from the game
    try:
        manager.disconnect_player_from_game(match.id, owner.id)
    except PlayerNotConnected:
        pass

    # Notify other players that the owner has left
    msg = {
        "key": "PLAYER_LEFT",
        "payload": {
            "owner_name": owner.player_name,
            "is_owner": True
        }
    }
    try:
        await manager.broadcast_to_game(match.id, msg)
    except RuntimeError as e:
        print(f"Error al enviar mensaje: {e}")

    # Disconnect all players from the game and delete the match
    for player in match.players:
        if player.id != owner.id:
            try:
                manager.disconnect_player_from_game(match.id, player.id)
            except PlayerNotConnected:
                print(f"Player {player.id} not connected")
                pass

    match_service.delete_match(match.id)

    return {"message": "The match has been canceled because the owner has left."}


async def turn_timeout(match_id: int, db: Session, turn_order: int, background_tasks):
    timer = int(os.getenv("TURN_TIMER"))
    await sleep(timer)
    match = db.get(Matches, match_id)
    logger.info("timestamp DB: %s", match.started_turn_time)
    logger.info("Now: %s", datetime.now())
    logger.info("Turn order DB: %s", turn_order)
    logger.info("Turn order: %s", turn_order)
    if match is not None and match.current_player_turn == turn_order and datetime.now() - match.started_turn_time >= timedelta(seconds=timer-1):
        logger.info("IF Timeout")
        movement_card_service = MovementCardService(db)
        tile_service = TileService(db)
        board_service = BoardService(db)
        player_service = PlayerService(db)
        
        try:
            player = player_service.get_player_by_turn(turn_order, match_id)
            match = MatchService(db).get_match_by_id(match_id)
            board = board_service.get_board_by_match_id(match_id)
        except Exception as e:
            logger.error(e)
            return None
        logger.info("Current Player turn: %s, %s", player.turn_order, player.player_name)
        movements = []
        tiles = []
        for _ in range(len(board.temporary_movements)):
            try:
                last_movement = board_service.get_last_temporary_movements(
                    board.id)
            except NoResultFound as e:
                logger.error(e)
                return None
        
            tile1 = last_movement.tile1
            tile2 = last_movement.tile2

            try:
                movement = movement_card_service.get_movement_card_by_id(
                    last_movement.id_mov)
                movement_card_service.add_movement_card_to_player(player.id, movement.id)
            except NoResultFound as e:
                logger.error(e)
                return None
            
            movements.append((movement.id, movement.mov_type))
            tiles = [{"rowIndex": tile1.position_x, "columnIndex": tile1.position_y}, {
            "rowIndex": tile2.position_x, "columnIndex": tile2.position_y}]
            aux_tile = copy(tile1)
            
            try:
                tile_service.update_tile_position(
                    tile1.id, tile2.position_x, tile2.position_y)
                tile_service.update_tile_position(
                    tile2.id, aux_tile.position_x, aux_tile.position_y)
            except NoResultFound as e:
                logger.error(e)
                return None
            
            await sleep(1)
            msg = {"key": "UNDO_PARTIAL_MOVE", "payload": {"tiles": tiles}}
            await manager.broadcast_to_game(match_id, msg)
                
        
        next_player = end_turn_logic(player, match, db)
        logger.info("Next Player turn: %s, %s", next_player.turn_order, next_player.player_name)
        movements += give_movement_card_to_player(player.id, db)

        await notify_movement_card_to_player(player.id, match_id, movements)
        await notify_all_players_movements_received(player, match)
        await give_shape_card_to_player(player.id, db, is_init=False)

        msg = {
            "key": "END_PLAYER_TURN",
            "payload": {
                "current_player_turn": player.turn_order,
                "current_player_name": player.player_name,
                "next_player_name": next_player.player_name,
                "next_player_turn": next_player.turn_order
            }
        }
        await manager.broadcast_to_game(match.id, msg)

        background_tasks.add_task(turn_timeout, match_id, db, next_player.turn_order, background_tasks)
        logger.info("Getting out IF")
    logger.info("End function")
    


def give_movement_card_to_player(player_id: int, db: Session) -> list[tuple[int, str]]:
    """
    Da hasta 3 cartas de movimiento al jugador.
    Args:
        - player_id : id del jugador.
        - db : Session de la base de datos.
    Returns:
        Lista de cartas dadas al jugador.
    """
    player_service = PlayerService(db)
    movement_service = MovementCardService(db)

    player = player_service.get_player_by_id(player_id)
    match_id = player.match_id
    list_movs = player.movement_cards
    movs_to_give = 3 - len(list_movs)
    movements_given = []

    while movs_to_give > 0:
        movements = movement_service.get_movement_cards_without_owner(match_id)
        if not movements:
            break  # No hay más cartas en el mazo
        movement = movements[randint(0, len(movements) - 1)]
        movement_service.add_movement_card_to_player(player_id, movement.id)
        movements_given.append((movement.id, movement.mov_type))
        movs_to_give -= 1

    return movements_given


@router.delete("/{match_id}/left/{player_id}")
async def leave_player(player_id: int, match_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to handle a player leaving a match.
    Args:
        player_id (int): The ID of the player leaving the match.
        match_id (int): The ID of the match the player is leaving.
        db (Session): Database session dependency.
    Raises:
        HTTPException: If the player is not found.
        HTTPException: If the match is not found.
        HTTPException: If the player is not part of the match.
        HTTPException: If the player is the owner and the match is in the "WAITING" state.
    Returns:
        dict: A dictionary containing the player ID and player name of the player who left the match.
    """
    match_service = MatchService(db)
    player_service = PlayerService(db)

    try:
        player_to_delete = player_service.get_player_by_id(player_id)
    except ValueError:
        raise HTTPException(
            status_code=404, detail=f"Player not found with id: {player_id}")

    try:
        match_to_leave = match_service.get_match_by_id(match_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Match not found")

    if player_to_delete.match_id != match_id:
        raise HTTPException(status_code=404, detail="Player not in match")

    player_name = player_to_delete.player_name

    if player_to_delete.is_owner and match_to_leave.state == "WAITING":
        return await owner_leave(player_to_delete, match_to_leave, db)

    next_player = None
    if player_to_delete.turn_order == match_to_leave.current_player_turn:
        next_player = end_turn_logic(player_to_delete, match_to_leave, db)

    player_service.delete_player(player_id)

    try:
        manager.disconnect_player_from_game(match_id, player_id)
    except PlayerNotConnected:
        pass

    match_service.update_match(
        match_id, match_to_leave.state, match_to_leave.current_players - 1)

    msg = {"key": "PLAYER_LEFT", "payload": {"name": player_name}}
    try:
        await manager.broadcast_to_game(match_id, msg)
        print(f"Player {player_name} left the match")
    except RuntimeError as e:
        print(f"Error al enviar mensaje: {e}")

    if next_player:
        msg = {
            "key": "END_PLAYER_TURN",
            "payload": {
                "current_player_name": player_name,
                "next_player_name": next_player.player_name,
                "next_player_turn": next_player.turn_order
            }
        }
        await manager.broadcast_to_game(match_id, msg)

    if match_to_leave.current_players == 1 and match_to_leave.state == "STARTED":
        await playerWinner(match_id, ReasonWinning.FORFEIT, db)

    return {"player_id": player_id, "players": player_name}


@router.patch("/{match_id}/end-turn/{player_id}", status_code=200)
async def end_turn(match_id: int, player_id: int, db: Session = Depends(get_db), background_tasks = BackgroundTasks()):
    movement_card_service = MovementCardService(db)
    board_service = BoardService(db)
    tile_service = TileService(db)
    
    try:
        player = PlayerService(db).get_player_by_id(player_id)
    except:
        raise HTTPException(status_code=404, detail=f"Player not found")
    try:
        match = MatchService(db).get_match_by_id(match_id)
    except:
        raise HTTPException(status_code=404, detail=f"Match not found")
    try:
        board = board_service.get_board_by_match_id(match_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Board not found")

    movements = []
    tiles = []
    for _ in range(len(board.temporary_movements)):
        try:
            last_movement = board_service.get_last_temporary_movements(
                board.id)
        except NoResultFound as e:
            raise HTTPException(status_code=404, detail=e)
    
        tile1 = last_movement.tile1
        tile2 = last_movement.tile2

        try:
            movement = movement_card_service.get_movement_card_by_id(
                last_movement.id_mov)
            movement_card_service.add_movement_card_to_player(player_id, movement.id)
        except NoResultFound as e:
            raise HTTPException(status_code=404, detail=e)
        
        movements.append((movement.id, movement.mov_type))
        tiles = [{"rowIndex": tile1.position_x, "columnIndex": tile1.position_y}, {
        "rowIndex": tile2.position_x, "columnIndex": tile2.position_y}]
        aux_tile = copy(tile1)
        
        try:
            tile_service.update_tile_position(
                tile1.id, tile2.position_x, tile2.position_y)
            tile_service.update_tile_position(
                tile2.id, aux_tile.position_x, aux_tile.position_y)
        except NoResultFound as e:
            raise HTTPException(status_code=404, detail=e)
        
        await sleep(1)
        msg = {"key": "UNDO_PARTIAL_MOVE", "payload": {"tiles": tiles}}
        await manager.broadcast_to_game(match_id, msg)
            
    
    next_player = end_turn_logic(player, match, db)
    movements += give_movement_card_to_player(player_id, db)

    await notify_movement_card_to_player(player_id, match_id, movements)
    await notify_all_players_movements_received(player, match)
    await give_shape_card_to_player(player.id, db, is_init=False)

    msg = {
        "key": "END_PLAYER_TURN",
        "payload": {
            "current_player_turn": player.turn_order,
            "current_player_name": player.player_name,
            "next_player_name": next_player.player_name,
            "next_player_turn": next_player.turn_order
        }
    }
    await manager.broadcast_to_game(match.id, msg)

    background_tasks.add_task(turn_timeout, match_id, db, match.current_player_turn, background_tasks)
    return JSONResponse(None, background=background_tasks)


def validate_partial_move(partialMove: PartialMove, card_type: str):
    if len(partialMove.tiles) != 2:
        raise HTTPException(
            status_code=400, detail="Partial move must have 2 tiles")

    if card_type not in enums.Movements._value2member_map_:
        raise HTTPException(status_code=400, detail="Movement card not valid")

    tile1 = partialMove.tiles[0]
    tile2 = partialMove.tiles[1]
    movement_card = card_type

    if (tile1.rowIndex < 0 or tile1.rowIndex >= 6 or
        tile1.columnIndex < 0 or tile1.columnIndex >= 6 or
        tile2.rowIndex < 0 or tile2.rowIndex >= 6 or
            tile2.columnIndex < 0 or tile2.columnIndex >= 6):
        raise HTTPException(status_code=400, detail="Tile position is invalid")

    if movement_card == "Diagonal":
        return validate_diagonal(tile1, tile2)
    elif movement_card == "Inverse Diagonal":
        return validate_inverse_diagonal(tile1, tile2)
    elif movement_card == "Line":
        return validate_line(tile1, tile2)
    elif movement_card == "Line Between":
        return validate_line_between(tile1, tile2)
    elif movement_card == "L":
        return validate_l(tile1, tile2)
    elif movement_card == "Inverse L":
        return validate_inverse_l(tile1, tile2)
    elif movement_card == "Line Border":
        return validate_line_border(tile1, tile2)
    else:
        raise HTTPException(status_code=400, detail="Movement card not valid")


@router.post("/{match_id}/partial-move/{player_id}", status_code=200)
async def partial_move(match_id: int, player_id: int, partialMove: PartialMove, db: Session = Depends(get_db)):
    match_service = MatchService(db)
    player_service = PlayerService(db)
    movement_service = MovementCardService(db)

    try:
        match = match_service.get_match_by_id(match_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Match not found")

    try:
        player = player_service.get_player_by_id(player_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Player not found")

    if player.turn_order != match.current_player_turn:
        raise HTTPException(
            status_code=403, detail=f"It's not player {player.player_name}'s turn")

    try:
        card_type = movement_service.get_movement_card_by_id(
            partialMove.movement_card).mov_type
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Movement card not found")

    if validate_partial_move(partialMove, card_type):
        tile_service = TileService(db)
        board_service = BoardService(db)

        try:
            board = board_service.get_board_by_match_id(match_id)
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Board not found")

        formed_figures = board_service.get_formed_figures(match.board.id)
        try:
            tile1 = tile_service.get_tile_by_position(
                partialMove.tiles[0].rowIndex, partialMove.tiles[0].columnIndex, board.id)
            tile2 = tile_service.get_tile_by_position(
                partialMove.tiles[1].rowIndex, partialMove.tiles[1].columnIndex, board.id)
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Tile not found")

        aux_tile = copy(tile1)
        tile_service.update_tile_position(
            tile1.id, tile2.position_x, tile2.position_y)
        tile_service.update_tile_position(
            tile2.id, aux_tile.position_x, aux_tile.position_y)

        create_figure = False
        new_formed_figures = board_service.get_formed_figures(match.board.id)

        for figure in formed_figures:
            try:
                new_formed_figures.remove(figure)
            except ValueError:
                continue

        if new_formed_figures:
            create_figure = True

        board_service.update_list_of_parcial_movements(
            board.id, [tile1, tile2], partialMove.movement_card, create_figure)
        try:
            movement_service.update_card_owner_to_none(
                partialMove.movement_card)
        except NoResultFound:
            raise HTTPException(
                status_code=404, detail="Movement card not found")

        tiles = [{"rowIndex": tile1.position_x, "columnIndex": tile1.position_y}, {
            "rowIndex": tile2.position_x, "columnIndex": tile2.position_y}]
        msg = {"key": "PLAYER_RECEIVE_NEW_BOARD",
               "payload": {"swapped_tiles": tiles}}
        await manager.broadcast_to_game(match_id, msg)

        # Send Info about figures coordinates
        board_figures = None
        try:
            match = MatchService(db).get_match_by_id(match_id)
            board_figures = BoardService(db).get_formed_figures(match.board.id)
        except Exception:
            raise HTTPException(
                status_code=500, detail="Error with formed figures")

        msg = {
            "key": "ALLOW_FIGURES",
            "payload": board_figures
        }

        await manager.broadcast_to_game(match_id, msg)

    else:
        raise HTTPException(status_code=400, detail="Invalid movement")


@router.delete("/{match_id}/partial-move/{player_id}", status_code=200)
async def delete_partial_move(match_id: int, player_id: int, db: Session = Depends(get_db)):
    match_service = MatchService(db)
    player_service = PlayerService(db)
    tile_service = TileService(db)
    board_service = BoardService(db)
    movement_service = MovementCardService(db)

    try:
        match = match_service.get_match_by_id(match_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Match not found")

    try:
        player = player_service.get_player_by_id(player_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Player not found")

    if player.turn_order != match.current_player_turn:
        raise HTTPException(
            status_code=403, detail=f"It's not player {player.player_name}'s turn")

    try:
        board = board_service.get_board_by_match_id(match_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Board not found")

    last_movement = board_service.get_last_temporary_movements(board.id)

    if last_movement == None:
        raise HTTPException(status_code=409, detail="No movements to undo")

    tile1 = last_movement.tile1
    tile2 = last_movement.tile2
    movement_id = last_movement.id_mov

    try:
        movement_type = movement_service.get_movement_card_by_id(
            movement_id).mov_type
        movement_service.add_movement_card_to_player(player_id, movement_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Movement card not found")

    aux_tile = copy(tile1)

    try:
        tile_service.update_tile_position(
            tile1.id, tile2.position_x, tile2.position_y)
        tile_service.update_tile_position(
            tile2.id, aux_tile.position_x, aux_tile.position_y)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Tile not found")

    tiles = [{"rowIndex": tile1.position_x, "columnIndex": tile1.position_y}, {
        "rowIndex": tile2.position_x, "columnIndex": tile2.position_y}]
    movement_card = (movement_id, movement_type)

    msg = {"key": "UNDO_PARTIAL_MOVE", "payload": {"tiles": tiles}}
    await manager.broadcast_to_game(match_id, msg)

    # Send Info about figures coordinates
    board_figures = None
    try:
        match = MatchService(db).get_match_by_id(match_id)
        board_figures = BoardService(db).get_formed_figures(match.board.id)
    except Exception:
        raise HTTPException(
            status_code=500, detail="Error with formed figures")

    msg = {"key": "ALLOW_FIGURES", "payload": board_figures}
    await manager.broadcast_to_game(match_id, msg)

    return {"tiles": tiles, "movement_card": movement_card}


@router.post("/{match_id}/player/{player_id}/use-figure", status_code=200)
async def use_figure(match_id: int, player_id: int, request: UseFigure, db: Session = Depends(get_db)):
    match_service = MatchService(db)
    player_service = PlayerService(db)
    shape_card_service = ShapeCardService(db)
    board_service = BoardService(db)
    tile_service = TileService(db)
    movement_card_service = MovementCardService(db)

    try:
        match = match_service.get_match_by_id(match_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Match not found")

    try:
        player = player_service.get_player_by_id(player_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Player not found")

    if player.turn_order != match.current_player_turn:
        raise HTTPException(
            status_code=403, detail=f"It's not player {player.player_name}'s turn")

    try:
        shape_card = shape_card_service.get_shape_card_by_id(request.figure_id)

        if not shape_card.is_visible or shape_card.player_owner != player_id:
            raise HTTPException(
                status_code=404, detail="Figure card doesn't belong to Player")
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Figure Card not found")
    
    if shape_card.is_hard:
        shape_type = HardShapes(shape_card.shape_type)
    else:
        shape_type = EasyShapes(shape_card.shape_type)
         
    valid_coordinates = FIGURE_COORDINATES[shape_type.name]
    all_valid_rotations = [valid_coordinates, rotate_90_degrees(valid_coordinates, (6, 6)), rotate_180_degrees(
        valid_coordinates, (6, 6)), rotate_270_degrees(valid_coordinates, (6, 6))]

    try:
        board = board_service.get_board_by_id(match.board.id)

        figures_found = list(map(lambda x: Figure(x), board_service.get_formed_figures(board.id)))
        coordinates = request.coordinates
        figure_to_find = Figure(tuple(map(lambda x: Coordinate(x[0], x[1]), coordinates)))

        if not figure_to_find in figures_found or not Figure(translate_shape_to_bottom_left(figure_to_find, (6,6))) in all_valid_rotations:
            raise HTTPException(
                status_code=409, detail="Conflict with coordinates and Figure Card")

        movements = []
        tiles = []
        for _ in range(len(board.temporary_movements)):
            
            last_movement = board_service.get_last_temporary_movements(
                board.id)
            if last_movement.create_figure:
                break
            tile1 = last_movement.tile1
            tile2 = last_movement.tile2

            movement = movement_card_service.get_movement_card_by_id(
                last_movement.id_mov)
            movement_card_service.add_movement_card_to_player(player_id, movement.id)
            
            movements.append((movement.id, movement.mov_type))
            tiles.append((
                {"rowIndex": tile1.position_x, "columnIndex": tile1.position_y}, {
                    "rowIndex": tile2.position_x, "columnIndex": tile2.position_y}
            ))

            aux_tile = copy(tile1)
            tile_service.update_tile_position(
                tile1.id, tile2.position_x, tile2.position_y)
            tile_service.update_tile_position(
                tile2.id, aux_tile.position_x, aux_tile.position_y)

        figure_name = shape_card_service.get_shape_card_by_id(request.figure_id).shape_type
        shape_card_service.delete_shape_card(request.figure_id)
        
        for i in range(len(board.temporary_movements)):
            last_movement = board_service.get_last_temporary_movements(board.id)
            
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Tile not found")

    if tiles:
        for tiles_to_swap in tiles:
            msg = {"key": "UNDO_PARTIAL_MOVE", "payload": {"tiles": tiles_to_swap}}
            await manager.broadcast_to_game(match_id, msg)
            await sleep(1)

    msg2 = {
        "key": "COMPLETED_FIGURE",
        "payload": {
            "figure_id": request.figure_id,
            "figure_name": figure_name
        }
    }
    await manager.broadcast_to_game(match_id, msg2)
    await sleep(1)
    await player_winner_by_no_shapes(player, match, db)        

    figures_found = board_service.get_formed_figures(board.id)

    allow_figures_event = {
        "key": "ALLOW_FIGURES",
        "payload": figures_found
    }

    await manager.broadcast_to_game(match_id, allow_figures_event)

    return {"movement_cards": movements}
