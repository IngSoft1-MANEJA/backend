from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import Session
from random import shuffle, randint


from app.cruds.board import BoardService
from app.exceptions import *
from app.connection_manager import manager
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.cruds.movement_card import MovementCardService
from app.cruds.shape_card import ShapeCardService
from app.models.enums import *
from app.schemas import *
from app.database import get_db
from app.utils.utils import MAX_SHAPE_CARDS

router = APIRouter(prefix="/matches")


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


@router.get("/", response_model=list[MatchOut])
def get_matches(db: Session = Depends(get_db)):
    try:
        match_service = MatchService(db)
        matches = match_service.get_all_matches(available=True)
        return matches
    except:
        raise HTTPException(status_code=404, detail="No matches found")


@router.get("/{match_id}", response_model=MatchOut)
def get_match_by_id(match_id: int, db: Session = Depends(get_db)):
    try:
        match_service = MatchService(db)
        match = match_service.get_match_by_id(match_id)
        return match
    except:
        raise HTTPException(status_code=404, detail="Match not found")


@router.post("/", status_code=200)
def create_match(match: MatchCreateIn, db: Session = Depends(get_db)):
    match_service = MatchService(db)
    player_service = PlayerService(db)

    match1 = match_service.create_match(
        match.lobby_name, match.max_players, match.is_public)
    new_player = player_service.create_player(
        match.player_name, match1.id, True, match.token)
    manager.create_game_connection(match1.id)

    return {"player_id": new_player.id, "match_id": match1.id}


@router.post("/{match_id}")
async def join_player_to_match(match_id: int, playerJoinIn: PlayerJoinIn, db: Session = Depends(get_db)):
    try:
        match_service = MatchService(db)
        match = match_service.get_match_by_id(match_id)
        if match.current_players >= match.max_players:
            raise HTTPException(status_code=404, detail="Match is full")
        player_service = PlayerService(db)
        player = player_service.create_player(
            playerJoinIn.player_name, match_id, False, "123")
        match.current_players = match.current_players + 1
        players = [player.player_name for player in match.players]
        db.commit()
        msg = {"key": "PLAYER_JOIN", "payload": {"name": player.player_name}}

        try:
            await manager.broadcast_to_game(match_id, msg)
        except Exception as e:
            print(f"Error al enviar mensaje: {e}")
        return {"player_id": player.id, "players": players}
    except Exception as e:
        print("el error cuando se quiere unir es: ", e)
        raise HTTPException(status_code=500, detail="Error DB")

# ==================================== Auxiliares para el inicio de la partida ====================================

def create_movement_deck(db: Session, match_id: int):
    movement_service = MovementCardService(db)

    for mov in Movements:  # Por cada tipo de enum
        for _ in range(7):
            movement_service.create_movement_card(mov.value, match_id)
    
async def give_movement_card_to_player(player_id: int, db: Session, is_init: bool):
    """
        Da hasta 3 cartas de movimiento al jugador.
        Args:
            - player_id : id del jugador.
            - db : Session de la base de datos.
            - is_init : booleano que indica si es el inicio de la partida.
        Returns:
            None, comunica mediante websockets
    """
    player = PlayerService(db).get_player_by_id(player_id)
    match_id = player.match_id
    players = PlayerService(db).get_players_by_match(match_id)
    movement_service = MovementCardService(db)
    movements_given = []  # Lista de movimientos que se le dan al jugador

    while len(player.movement_cards) < 3:
        movements = movement_service.get_movement_card_by_match(match_id)
        movement = movements[randint(0, len(movements) - 1)]
        MovementCardService(db).add_movement_card_to_player(
            player_id, movement.id)
        # Agrego a la lista dada
        movements_given.append((movement.id, movement.mov_type))

    msg_user = {"key": "GET_MOVEMENT_CARD",
                "payload": {"movement_card": movements_given}}
    await manager.send_to_player(match_id, player_id, msg_user)

    # Se avisa a los demas jugadores que se le dio una carta de movimiento
    if is_init == False:  # Si no es el inicio de la partida
        for player_i in players:
            if player_i.id != player_id:
                msg_all = {"key": "PLAYER_RECEIVE_MOVEMENT_CARD",
                            "payload": {"player": player.player_name}}
                await manager.broadcast_to_game(match_id, msg_all)


async def give_shape_card_to_player(player_id: int, db: Session, is_init: bool):
    """
        Da hasta 3 cartas de figuras al jugador.

        Args:
            - player_id : id del jugador.
            - db : Session de la base de datos.
            - is_init : booleano que indica si es el inicio de la partida.
    """
    player = PlayerService(db).get_player_by_id(player_id)
    ShapeDeck = ShapeCardService(db).get_visible_cards(player_id, False)
    CardsToGive = 3 - len(ShapeCardService(db).get_visible_cards(player_id, True))
    ShapesGiven = []

    for i in range(CardsToGive):
        shape = ShapeDeck[randint(0, len(ShapeDeck) - 1)]
        ShapeCardService(db).update_shape_card(shape.id, True, False)
        ShapesGiven.append((shape.id, shape.shape_type))

    msg_all = {"key": "PLAYER_RECEIVE_SHAPE_CARD",
                "payload": {"player": player.player_name, "turn_order": player.turn_order, "shape_cards": ShapesGiven}}
    if is_init == False:
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

            for player_i in match.players:
                msg = {"key": "START_MATCH",
                       "payload": {}}
                await manager.send_to_player(match_id, player_i.id, msg)

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
    except Exception as e:
        print(f"Error al obtener informacion de la partida: {e}")
        raise HTTPException(
            status_code=404, detail="Error al obtener informacion de la partida")

    msg_info = {
        "key": "GET_PLAYER_MATCH_INFO",
        "payload": {
            "turn_order": player.turn_order,
            "board": board_table,
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
    await give_movement_card_to_player(player_id, db, True)
    await give_shape_card_to_player(player_id, db, True)
    
    msg_shapes = {
        "key": "PLAYER_RECIEVE_ALL_SHAPES",
        "payload": {[
            {
                "player": player.player_name,
                "shape_cards": ShapeCardService(db).get_visible_cards(player_id, True)
            }
            for player_i in players_in_match
        ]}
    }
    await manager.send_to_player(match_id, player_id, msg_shapes)
