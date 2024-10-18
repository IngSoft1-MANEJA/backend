import copy
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from sqlalchemy import select

from app.exceptions import *
from app.cruds.match import MatchService
from app.cruds.player import PlayerService
from app.cruds.tile import TileService
from app.cruds.board import BoardService
from app.connection_manager import manager
from app.database import get_db
from app.models import enums
from app.models.enums import ReasonWinning
from app.models.models import Players, Matches
from app.routers.matches import give_movement_card_to_player, give_shape_card_to_player, notify_all_players_movements_received, notify_movement_card_to_player
from app.schemas import PartialMove
from app.utils.utils import validate_diagonal, validate_inverse_diagonal, validate_line, validate_line_between, validate_inverse_l, validate_l, validate_line_border

router = APIRouter(prefix="/matches")

async def playerWinner(match_id: int, reason: ReasonWinning, db: Session):
    match_service = MatchService(db)
    player_service = PlayerService(db) 
    
    players = player_service.get_players_by_match(match_id)[0]
    player_id = players.id
    player_service.delete_player(player_id)
    match_service.update_match(match_id, "FINISHED", 0)
    reason_winning = reason.value
    
    msg = {"key": "WINNER", "payload": {"player_id": player_id, "reason": reason_winning}}
    
    try:
        await manager.broadcast_to_game(match_id, msg)
    except RuntimeError as e:
        # Manejar el caso en que el WebSocket ya esté cerrado
        print(f"Error al enviar mensaje: {e}")
        

@router.delete("/{match_id}/left/{player_id}")
async def leave_player(player_id: int, match_id: int, db: Session = Depends(get_db)):
    try:
        match_service = MatchService(db)
        player_service = PlayerService(db)
        try:
            player_to_delete = player_service.get_player_by_id(player_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Player not found with id: {player_id}") 
               
        match_to_leave = match_service.get_match_by_id(match_id)

        player_name = player_to_delete.player_name
        player_match = player_to_delete.match_id

        if player_match != match_id:
            raise HTTPException(status_code=404, detail="Player not in match")

        # IN LOBBY
        if match_to_leave.state == "WAITING":
            if player_to_delete.is_owner:
                raise HTTPException(status_code=400, detail="Owner cannot leave match")
                
        match_to_leave = match_service.get_match_by_id(match_id)
        player_service.delete_player(player_id)

        try:
            manager.disconnect_player_from_game(match_id, player_id)
        except PlayerNotConnected:
            # El jugador ya ha sido desconectado, no hacer nada
            pass
        
        match_service.update_match(match_id, match_to_leave.state, match_to_leave.current_players - 1)
        
        msg = {"key": "PLAYER_LEFT", "payload": {"name": player_name}}
        
        try:
            await manager.broadcast_to_game(match_id, msg)
        except RuntimeError as e:
            # Manejar el caso en que el WebSocket ya esté cerrado
            print(f"Error al enviar mensaje: {e}")

        # Si el jugador se quiere salir en su turno, debo pasar el turno al siguiente y luego avisar
        if player_to_delete.turn_order == match_to_leave.current_player_turn:
            next_player = end_turn_logic(player_to_delete, match_to_leave, db)
            
            msg= {
                "key": "END_PLAYER_TURN", 
                "payload": {
                    "current_player_name": player_name,
                    "next_player_name": next_player.player_name,
                    "next_player_turn": next_player.turn_order
                }
            }
            await manager.broadcast_to_game(match_id, msg)
        
        if (match_to_leave.current_players) == 1 and match_to_leave.state == "STARTED":
            await playerWinner(match_id, ReasonWinning.FORFEIT, db)
        
        return {"player_id": player_id, "players": player_name}

    except PlayerNotConnected as e:
        raise HTTPException(
            status_code=404, detail="Player not connected to match")    
    except GameConnectionDoesNotExist as e:
        raise HTTPException(status_code=404, detail="Match not found")
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Match not found")
    

def end_turn_logic(player: Players, match:Matches, db: Session):
    match_service = MatchService(db)
    player_service = PlayerService(db)
    
    if player.turn_order != match.current_player_turn:
        raise HTTPException(status_code=403, detail=f"It's not player {player.player_name}'s turn")
    
    if match.current_player_turn == match.current_players:
        match_service.update_turn(match.id, turn=1)
    else:
        match_service.update_turn(match.id, match.current_player_turn + 1) 
    
    next_player = player_service.get_player_by_turn(turn_order= match.current_player_turn, match_id= match.id)
    
    return next_player


@router.patch("/{match_id}/end-turn/{player_id}", status_code=200)
async def end_turn(match_id: int, player_id: int, db: Session = Depends(get_db)):
    try:
        player = PlayerService(db).get_player_by_id(player_id)
    except:
        raise HTTPException(status_code=404, detail=f"Player not found")
    try:
        match = MatchService(db).get_match_by_id(match_id)
    except:
        raise HTTPException(status_code=404, detail=f"Match not found")
    
    next_player = end_turn_logic(player, match, db)
    
    print(f"Calling give_movement_card_to_player with player_id: {player_id}")
    movs = give_movement_card_to_player(player_id, db)
    print(f"Movements: {movs}")
    
    await notify_movement_card_to_player(player_id, match_id, movs)
    print("Notified movements")
    await notify_all_players_movements_received(player, match)
    print("Notified all players movements received")
    await give_shape_card_to_player(player.id, db, is_init=False)
    
    msg = {
        "key": "END_PLAYER_TURN", 
        "payload": {
            "current_player_name": player.player_name,
            "next_player_name": next_player.player_name,
            "next_player_turn": next_player.turn_order
        }
    }
    await manager.broadcast_to_game(match.id, msg)
    
    
def validate_partial_move(partialMove: PartialMove):
    if len(partialMove.tiles) != 2:
        raise HTTPException(status_code=400, detail="Partial move must have 2 tiles")
    
    if partialMove.movement_card not in enums.Movements._value2member_map_:
        raise HTTPException(status_code=400, detail="Movement card not valid")
    
    tile1 = partialMove.tiles[0]
    tile2 = partialMove.tiles[1]
    movement_card = partialMove.movement_card
    
    if (tile1.rowIndex < 0 or tile1.rowIndex >= 6 or
    tile1.columnIndex < 0 or tile1.columnIndex >= 6 or
    tile2.rowIndex < 0 or tile2.rowIndex >= 6 or
    tile2.columnIndex < 0 or tile2.columnIndex >= 6):
        raise HTTPException(status_code=400, detail="Tile position is invalid")
    
    #path = "validate_" + movement_card.lower()
    #path(tile1, tile2)
    
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
    
    try:
        match = match_service.get_match_by_id(match_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Match not found")
    
    try:
        player = player_service.get_player_by_id(player_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if player.turn_order != match.current_player_turn:
        raise HTTPException(status_code=403, detail=f"It's not player {player.player_name}'s turn")
    
    try:
        if validate_partial_move(partialMove):
            tile_service = TileService(db)
            board_service = BoardService(db)
            
            board = board_service.get_board_by_match_id(match_id)
            tile1 = tile_service.get_tile_by_position(partialMove.tiles[0].rowIndex, partialMove.tiles[0].columnIndex, board.id)
            tile2 = tile_service.get_tile_by_position(partialMove.tiles[1].rowIndex, partialMove.tiles[1].columnIndex, board.id)
            print("tile 1 antes", partialMove.tiles[0].rowIndex, partialMove.tiles[0].columnIndex)
            print("tile 1", tile1)

            print("tile 2 antes", partialMove.tiles[1].rowIndex, partialMove.tiles[1].columnIndex)
            print("tile 2", tile2)

            aux_tile = copy.copy(tile1)
            tile_service.update_tile_position(tile1.id, tile2.position_x, tile2.position_y)
            tile_service.update_tile_position(tile2.id, aux_tile.position_x, aux_tile.position_y)
            
            board_service.update_list_of_parcial_movements(board.id, [tile1, tile2])
            board_service.print_temporary_movements(board.id)
            board_table = board_service.get_board_table(board.id)
            msg = {"key": "PLAYER_RECEIVE_NEW_BOARD", "payload": {"board": board_table}}
            await manager.broadcast_to_game(match_id, msg)
            
        else:
            raise HTTPException(status_code=400, detail="Invalid movement")
        
    
    except HTTPException as e:
        raise e
    

@router.delete("/{match_id}/partial-move/{player_id}", status_code=200)
def delete_partial_move(match_id: int, player_id: int, db: Session = Depends(get_db)):
    match_service = MatchService(db)
    player_service = PlayerService(db)
    
    try:
        match = match_service.get_match_by_id(match_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Match not found")
    
    try:
        player = player_service.get_player_by_id(player_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if player.turn_order != match.current_player_turn:
        raise HTTPException(status_code=403, detail=f"It's not player {player.player_name}'s turn")
    
    try:
        tile_service = TileService(db)
        board_service = BoardService(db)
        
        board = board_service.get_board_by_id(match_id)
        last_movement = board_service.get_last_temporary_movements(board.id)
        tile1 = last_movement.tile1
        tile2 = last_movement.tile2
    
        aux_tile = copy.copy(tile1)
        tile_service.update_tile_position(tile1.id, tile2.position_x, tile2.position_y)
        tile_service.update_tile_position(tile2.id, aux_tile.position_x, aux_tile.position_y)
        
        board_service.print_temporary_movements(board.id)
        
    except HTTPException as e:
        raise e
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Tile not found")