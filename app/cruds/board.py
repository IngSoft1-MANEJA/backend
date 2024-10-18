from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from itertools import cycle
from random import shuffle

from app.cruds.tile import TileService
from app.models.enums import Colors
from app.models.models import Boards, Tiles
from app.utils.utils import validate_color, validate_turn, validate_board

class BoardService:
    """
    Servicio para realizar operaciones CRUD sobre la tabla de Boards
    """

    def __init__(self, db: Session):
        """ Constructor de la clase, guardamos en el atributo
            db: La session de la base de datos."""
        self.db = db

    def create_board(self, match_id : int, ban_color : str = None):
        """
        Crea un nuevo tablero en la base de datos.
        Args:
            match_id: Id de la partida a la cual pertenece el tablero.
            ban_color: Color del ban.
        Returns:
            new_board: Tablero creado.
        """
        new_board = Boards(match_id=match_id)
        if ban_color:
            validate_color(ban_color)
            new_board.ban_color = ban_color

        self.db.add(new_board)
        self.db.commit()
        return new_board

    def init_board(self, board_id: int):
        """Initializes the board with the tiles.

        Args:
            board_id (int): Id of the board in the db.
        """

        table = [color.value for color in Colors] * 9
        shuffle(table)

        tile_service = TileService(self.db)
        table_iter = iter(table)
        for i in range(6):
            for j in range(6):
                color = next(table_iter)
                tile_service.create_tile(board_id, color, i, j)

        self.db.commit()

    def get_board_table(self, board_id: int) -> List[List[str]]:
        """Obtiene la representacion del tablero en una matriz de colores.

        Args:
            board_id (int): id de la tabla a obtener.

        Returns:
            List[List[str]]: matriz de colores del tablero.
        """

        tiles = (
            self.db.query(Tiles)
            .filter(Tiles.board_id == board_id)
            .order_by(Tiles.position_x, Tiles.position_y)
            .all()
        )
        board = [
            [tile.color for tile in tiles[i * 6 : (i + 1) * 6]]
            for i in range(6)
        ]
        return board

    def get_all_boards(self) -> List[Boards]:
        """
        Obtiene todos los tableros de la base de datos.
        Returns:
            boards: Lista de tableros.
        """
        boards = self.db.query(Boards).all()
        return boards

    def get_board_by_id(self, board_id: int) -> Boards:
        """
        Obtiene un tablero de la base de datos por su id.
        Args:
            board_id: Id del tablero.
        Returns:
            board: Tablero.
        """
        board = self.db.query(Boards).filter(Boards.id == board_id).one()
        validate_board(board.id)
        return board

    def update_ban_color(self, board_id: int, ban_color: str):
        """
        Actualiza el color del ban de un tablero.
        Args:
            board_id: Id del tablero.
            ban_color: Color del ban.
        """
        validate_color(ban_color)

        board = self.db.query(Boards).filter(Boards.id == board_id).one()
        board.ban_color = ban_color
        self.db.commit()

    def delete_board(self, board_id: int):
        """
        Elimina un tablero de la base de datos.
        Args:
            board_id: Id del tablero.
        """
        board = self.db.query(Boards).filter(Boards.id == board_id).one()
        validate_board(board.id)
        self.db.delete(board)
        self.db.commit()

    def get_board_by_match_id(self, match_id: int) -> Boards:
        """
        Obtiene un tablero de la base de datos por su id de partida.
        Args:
            match_id: Id de la partida.
        Returns:
            board: Tablero.
        """
        try:
            board = self.db.query(Boards).filter(Boards.match_id == match_id).one()
            return board
        
        except NoResultFound:
            raise NoResultFound("Board not found with match_id {match_id}") 
    
    def update_list_of_parcial_movements(self, board_id: int, list_of_parcial_movements: List[Tiles], id_mov: int):
        """
        Actualiza la lista de movimientos parciales de un tablero.
        Args:
            board_id: Id del tablero.
            list_of_parcial_movements: Lista de movimientos parciales.
        """
        try:
            board = self.db.query(Boards).filter(Boards.id == board_id).one()
            board.add_temporary_movement(list_of_parcial_movements[0], list_of_parcial_movements[1], id_mov) 
            self.db.commit()
            
        except NoResultFound:
            raise NoResultFound("Board not found with id {board_id}")
        
    def print_temporary_movements(self, board_id: int):
        """
        Obtiene la lista de movimientos temporales de un tablero.
        Args:
            board_id: Id del tablero.
        Returns:
            list_of_parcial_movements: Lista de movimientos temporales.
        """
        try:
            board = self.db.query(Boards).filter(Boards.id == board_id).one()
            board.print_temporary_movements()
        
        except NoResultFound:
            raise NoResultFound("Board not found with id {board_id}")
        
    def get_last_temporary_movements(self, board_id: int):
        """
        Elimina la lista de movimientos temporales de un tablero.
        Args:
            board_id: Id del tablero.
        """
        try:
            board = self.db.query(Boards).filter(Boards.id == board_id).one()
            movement = board.get_last_movement()
            return movement
        
        except NoResultFound:
            raise NoResultFound("Board not found with id {board_id}")