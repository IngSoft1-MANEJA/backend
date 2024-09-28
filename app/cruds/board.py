from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from typing import List
from models.models import Boards
from database import engine
from models.enums import Colors

from app.exceptions import *

class BoardService:
    """
    Servicio para realizar operaciones CRUD sobre la tabla de Boards
    Metodos:
            - __init__
            - create_board
            - get_all_boards
            - get_board_by_id
            - update_ban_color
            - delete_board
    """
    def __init__(self, db):
        """ Constructor de la clase, guardamos en el atributo
            db: La session de la base de datos."""
        self.db = db

    def create_board(self, match_id : int):
        """
        Crea un nuevo tablero en la base de datos.
        Args:
            match_id: Id de la partida a la cual pertenece el tablero.
        Returns:
            new_board: Tablero creado.
        """
        new_board = Boards(match_id=match_id)
        self.db.add(new_board)
        self.db.commit()
        return new_board
    
    def get_all_boards(self) -> List[Boards]:
        """
        Obtiene todos los tableros de la base de datos.
        Returns:
            boards: Lista de tableros.
        """
        boards = self.db.query(Boards).all()
        return boards

    def get_board_by_id(self, board_id : int) -> Boards:
        """
        Obtiene un tablero de la base de datos por su id.
        Args:
            board_id: Id del tablero.
        Returns:
            board: Tablero.
        """
        board = self.db.query(Boards).filter(Boards.id == board_id).one()
        return board

    def update_ban_color(self, board_id : int, ban_color : str):
        """
        Actualiza el color del ban de un tablero.
        Args:
            board_id: Id del tablero.
            ban_color: Color del ban.
        """
    
        if ban_color not in Colors.__members__: 
            raise ColorNotAvailable(ban_color)
        
        board = self.db.query(Boards).filter(Boards.id == board_id).one()
        board.ban_color = ban_color
        self.db.commit()
    
    def delete_board(self, board_id : int):
        """
        Elimina un tablero de la base de datos.
        Args:
            board_id: Id del tablero.
        """
        board = self.db.query(Boards).filter(Boards.id == board_id).one()
        self.db.delete(board)
        self.db.commit()