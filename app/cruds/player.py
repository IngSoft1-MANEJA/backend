from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from typing import List
from models.models import Players
from database import engine

class PlayerService:
    """
    Servicio para realizar operaciones CRUD sobre la tabla de Matches
    Metodos:
        - __init__ 
        - create_player
        - get_players
        - get_player_by_id
        - get_user_turn_order
        - update_turn_order
        - delete_player
    """
    def __init__(self, db: Session):
        self.db = db

    def create_player(self, db: Session,name : str):
        """
            Crea una nueva instancia de jugador en la base de datos.
            
            Args:
                name: nombre del jugador.
            Returns:
                player: el objeto player creado.
        """

        player = Players(name=name)
        db.add(player)
        db.commit()
        db.refresh(player)
        return player
        
    def get_players(self, db: Session) -> List[Players]:
        """
            Obtiene la lista de todos los jugadores.
            
            Args:
                none.
            Returns:
                Players: Lista de players.
        """
        
        players = db.query(Players).all()
        return players
    
    def get_player_by_id(self, db: Session, player_id : int):
        """
            Obtiene un jugador segun su id.
            
            Args:
                player_id : Id del jugador a buscar
            Returns:
                player: El jugador con el id propuesto.
        """
        try:
            player = db.query(Players).filter(player_id == Players.id).first()
            return player
  
        except NoResultFound:
            raise ValueError("No player with that id")


    def delete_player(self, db: Session, player_id : int):
        """
            Elimina un jugador segun su id.
            
            Args:
                player_id : Id del jugador a eliminar
            Returns:
                none.
        """
        try:
            player = db.query(Players).filter(Players.id == player_id).first()
            db.delete(player)
            db.commit()
        except NoResultFound:
            raise ValueError("No player with that id")
            
    def update_player_with_match(self, db: Session, player_id : int, match_id : int):
        """
            Asocia un jugador a una partida.
            
            Args:
                player_id : Id del jugador a asociar
                match_id : Id de la partida a asociar
            Returns:
                none.
        """
        try:
            player = db.query(Players).filter(Players.id == player_id).first()
            player.match_id = match_id
            db.commit()
        except NoResultFound:
            raise ValueError("No player with that id")
            
    def update_turn_order(self, db: Session, id: int, turn_order : int):
        """
            Actualiza el orden de turno de los jugadores.
            
            Args:
                turn_order : nuevo orden de turno.
            Returns:
                none.
        """        
        try:
            player = db.query(Players).filter(Players.id == id).first()
            player.turn_order = id
            db.commit()
        except NoResultFound:
            raise ValueError("No player with that id")
       

    def get_user_turn_order(self, db: Session, id: int) -> int:
        """
            Obtiene el orden de turno actual.
            
            Args:
                none.
            Returns:
                turn_order: orden de turno.
        """
        player = db.query(Players).filter(Players.id == id).first()
        return player.turn_order
    