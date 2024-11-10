from typing import Optional, Annotated
from fastapi import (APIRouter, Query, WebSocket, WebSocketDisconnect, Depends, 
                     HTTPException, Security)
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import Session
from random import shuffle, randint


from app.cruds.board import BoardService
from app.connection_manager import manager
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.cruds.movement_card import MovementCardService
from app.cruds.shape_card import ShapeCardService
from app.exceptions import GameConnectionDoesNotExist, PlayerAlreadyConnected, PlayerNotConnected
from app.models.enums import *
from app.models.models import Matches, Players
from app.schemas import *
from app.database import get_db
from app.utils.utils import MAX_SHAPE_CARDS
from app.logger import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matches")

@router.websocket("/ws")
async def create_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    match_service = MatchService(db)
    await websocket.accept()
    try:
        index = manager.add_anonymous_connection(websocket) ##
        matches = match_service.get_all_matches(True)
        matches = [MatchOut.model_validate(match).model_dump() 
                   for match in matches]
        msg = {"key": "MATCHES_LIST", "payload": {"matches": matches}}
        await websocket.send_json(msg)
        await manager.keep_alive_matches(index, lambda x, y: on_filter_matches(x,y, db))
    except WebSocketDisconnect:
        manager.remove_anonymous_connection(websocket)
    except Exception as e:
        logger.error("Error al enviar mensaje: %s", e)

@router.websocket("/{game_id}/ws/{player_id}")
async def create_websocket_connection(game_id: int, player_id: int, websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        if manager._games == {}:
            match_service = MatchService(db)
            matches = match_service.get_all_matches()
            match_ids = [match.id for match in matches]
            for match_id in match_ids:
                manager.create_game_connection(match_id)
        try:
            manager.connect_player_to_game(game_id, player_id, websocket)
            await manager.keep_alive(websocket)
        except GameConnectionDoesNotExist:
            await websocket.send_json(
                {"Error": f"Conexión a la partida {game_id} no existe"}
            )
            await websocket.close()
        except PlayerAlreadyConnected:
            await websocket.send_json(
                {
                    "Error": f"Jugador {player_id} ya tiene una conexión activa a la partida {game_id}"
                }
            )
            await websocket.close()
            raise WebSocketDisconnect

    except WebSocketDisconnect:
        try:
            manager.disconnect_player_from_game(game_id, player_id)
        except PlayerNotConnected:
            # El jugador ya ha sido desconectado, no hacer nada
            pass

async def notify_matches_list(db):
    try:
        for conn in manager._connections:
            filtered_matches = on_filter_matches(conn["match_name"], 
                                                 conn["max_players"], db)
            matches = [MatchOut.model_validate(match).model_dump() 
                    for match in filtered_matches]
            msg = {"key": "MATCHES_LIST", "payload": {"matches": matches}}
            await conn["websocket"].send_json(msg)
        
    except Exception as e:
        logger.error("Error al enviar mensaje: %s", e)


def on_filter_matches(
    match_name: Optional[str],
    max_players: Optional[int],
    db: Session
):
    """
        Obtiene todas las partidas que coincidan con los filtros, si no tiene
        filtros devuelve todas las partidas disponibles.
        Args:
            - s : string a buscar en el nombre de la partida.
            - max_players : cantidad máxima de jugadores en la partida.
            - db : Session de la base de datos.
        Returns:
            - Lista de partidas en esquema MatchOut.
    """
    matches = MatchService(db).get_all_matches(True)

    if not match_name and not max_players:
        return matches

    filtered_matches = matches
    if match_name:
        filtered_matches = [
            match for match in filtered_matches if match_name.lower() in match.match_name.lower()]
    if max_players:
        filtered_matches = [
            match for match in filtered_matches if match.max_players == max_players]

    return filtered_matches


@router.get("/{match_id}", response_model=MatchOut)
def get_match_by_id(match_id: int, db: Session = Depends(get_db)):
    try:
        match_service = MatchService(db)
        match = match_service.get_match_by_id(match_id)
        return match
    except:
        raise HTTPException(status_code=404, detail="Match not found")


@router.post("/", status_code=200)
async def create_match(match: MatchCreateIn, db: Session = Depends(get_db)):
    match_service = MatchService(db)
    player_service = PlayerService(db)

    match1 = match_service.create_match(
        match.lobby_name, match.max_players, match.is_public)
    new_player = player_service.create_player(
        match.player_name, match1.id, True, match.token)
    manager.create_game_connection(match1.id)
    
    await notify_matches_list(db)

    return {"player_id": new_player.id, "match_id": match1.id}


@router.post("/{match_id}", status_code=200,
             response_model=PlayerJoinOut,
             responses={404: {"description": "Match not found"},
                        409: {"description": "Match is full"}})
async def join_player_to_match(match_id: int, playerJoinIn: PlayerJoinIn, db: Session = Depends(get_db)):
    """
    Create a player and add them to the match.
    """
    match_service = MatchService(db)
    player_service = PlayerService(db)

    try:
        match = match_service.get_match_by_id(match_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail="Match not found")

    if match.current_players >= match.max_players:
        raise HTTPException(status_code=409, detail="Match is full")

    player = player_service.create_player(
        playerJoinIn.player_name, match_id, False, "123")
    match.current_players = match.current_players + 1
    players = [player.player_name for player in match.players]
    db.commit()
    msg = {"key": "PLAYER_JOIN", "payload": {"name": player.player_name}}
    try:
        await manager.broadcast_to_game(match_id, msg)
    except Exception as e:
        logger.error("Error al enviar mensaje: %s", e)
        
    await notify_matches_list(db)

    return {"player_id": player.id, "players": players}

# ==================================== Auxiliares para el inicio de la partida ====================================


def create_movement_deck(db: Session, match_id: int):
    movement_service = MovementCardService(db)

    for mov in Movements:  # Por cada tipo de enum
        for _ in range(7):
            movement_service.create_movement_card(mov.value, match_id)


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
    player = PlayerService(db).get_player_by_id(player_id)
    visible_cards = ShapeCardService(db).get_visible_cards(player_id, True)
    ShapeDeck = ShapeCardService(db).get_visible_cards(player_id, False)
    CardsToGive = 3 - len(visible_cards)
    ShapesGiven = []

    for i in range(CardsToGive):
        if not ShapeDeck:
            break  # No hay más cartas en el mazo
        shape = ShapeDeck.pop(randint(0, len(ShapeDeck) - 1))
        ShapeCardService(db).update_shape_card(shape.id, True, "NOT_BLOCKED")
        ShapesGiven.append((shape.id, shape.shape_type))

    if not is_init:
        msg_all = {"key": "PLAYER_RECEIVE_SHAPE_CARD",
                   "payload": [{"player": player.player_name, "turn_order": player.turn_order, "shape_cards": ShapesGiven}]}
        await manager.broadcast_to_game(player.match_id, msg_all)
# =============================================================================================================


@router.patch("/{match_id}/start/{player_id}", status_code=200)
async def start_match(match_id: int, player_id: int, db: Session = Depends(get_db)):
    try:
        match_service = MatchService(db)
        match = match_service.get_match_by_id(match_id)
        movement_service = MovementCardService(db)
        shape_service = ShapeCardService(db)

        if match.current_players < match.max_players or match.state != MatchState.WAITING.value:
            raise HTTPException(status_code=404, detail="Not enough players")

        player_service = PlayerService(db)
        player = player_service.get_player_by_id(player_id)

        if player.is_owner and player.match_id == match_id:
            match.state = MatchState.STARTED.value
            create_movement_deck(db, match_id)  # crea el mazo movs

            # ===================== Configuro los mazos ==================================
            shapes = [(shape.value, True) for shape in HardShapes] * 2
            shapes += [(shape.value, False) for shape in EasyShapes] * 2
            shuffle(shapes)

            # Crea el mazo de figuras para cada jugador
            for player in match.players:
                for _ in range(int(MAX_SHAPE_CARDS / match.max_players)):
                    shape = shapes.pop()
                    shape_service.create_shape_card(
                        shape[0], shape[1], False, player.id)

            # ============== Creo el tablero y lo configuro ================
            board_service = BoardService(db)
            board = board_service.create_board(match_id)
            board_service.init_board(board.id)
            _ = match_service.set_players_order(match)

            for player_i in match.players:
                msg = {"key": "START_MATCH",
                       "payload": {}}
                await manager.send_to_player(match_id, player_i.id, msg)

                give_movement_card_to_player(player_i.id, db)
                await give_shape_card_to_player(player_i.id, db, True)

            return {"message": "Match started successfully"}

        raise HTTPException(status_code=404, detail="Match not found")
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Match not found")


@router.get("/{match_id}/player/{player_id}")
async def get_match_info_to_player(match_id: int, player_id: int, db: Session = Depends(get_db)):
    """
        Devuelve informacion de la partida al jugador:
            - Tablero con sus fichas
            - Cartas de movimiento propias
            - Cartas de figuras de los demás jugadores
            - Lista de oponentes con su nombre y orden de turno

        Args:
            match_id: id de la partida.
            player_id: id del jugador.
            db: Session de la base de datos.
        Returns:
            None, comunica mediante websockets.
    """
    try:
        match = MatchService(db).get_match_by_id(match_id)
        player = PlayerService(db).get_player_by_id(player_id)
        board_table = BoardService(db).get_board_table(match.board.id)
        players_in_match = PlayerService(db).get_players_by_match(match_id)
        deck_size = ShapeCardService(db).get_deck_size(player_id)
    except Exception as e:
        print(f"Error al obtener informacion de la partida: {e}")
        raise HTTPException(
            status_code=404, detail="Error al obtener informacion de la partida")

    current_player = PlayerService(db).get_player_by_turn(
        match.current_player_turn, match_id)
    msg_info = {
        "key": "GET_PLAYER_MATCH_INFO",
        "payload": {
            "turn_order": player.turn_order,
            "board": board_table,
            "current_turn_player": current_player.player_name,
            "deck_size": deck_size,
            "ban_color": match.board.ban_color,
            "opponents": [
                {
                    "player_name": opponent.player_name,
                    "turn_order": opponent.turn_order
                }
                for opponent in players_in_match
                if opponent.id != player_id
            ]
        }
    }
    await manager.send_to_player(match_id, player_id, msg_info)

    # Se le envian las cartas de movimiento y figuras
    s_service = ShapeCardService(db)
    m_service = MovementCardService(db)

    payload_list = []
    for player_i in players_in_match:
        shapes_p = s_service.get_visible_cards(player_i.id, True)
        all_shapes = [(shape.id, shape.shape_type) for shape in shapes_p]

        payload = {"turn_order": player_i.turn_order,
                   "shape_cards": all_shapes}
        payload_list.append(payload)

    msg_shapes = {
        "key": "PLAYER_RECIEVE_ALL_SHAPES",
        "payload": payload_list
    }

    await manager.send_to_player(match_id, player_id, msg_shapes)

    movements = m_service.get_movement_card_by_user(player_id)
    all_movements = [(mov.id, mov.mov_type) for mov in movements]
    await notify_movement_card_to_player(player_id, match_id, all_movements)

    # Send Info about figures coordinates
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

    await manager.send_to_player(match_id, player_id, msg)
