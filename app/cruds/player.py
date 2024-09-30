from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from typing import List
from app.models.models import Players
from app.utils.utils import validate_player_name

class PlayerService:
    """
    Servicio para realizar operaciones CRUD sobre la tabla de Players
    Metodos:
        - __init__ 
        - create_player
        - get_player_id
        - get_players
        - get_player_by_id
        - get_user_turn_order
        - update_turn_order
        - delete_player
    """
    def __init__(self, db: Session):
        """ Constructor de la clase, guardamos en el atributo
            db: La session de la base de datos."""
        self.db = db

    def create_player(self, name: str, match_to_link: int, owner: bool, token: str):
        """
            Crea una nueva instancia de jugador en la base de datos.
            
            Args:
                name: nombre del jugador.
                match_to_link: id del match al que se vincula el jugador.
                owner: si el jugador es el dueño del match.
                token: token de sesión del jugador.
            Returns:
                player: el objeto player creado.
        """
        validate_player_name(name)
        player = Players(player_name=name, match_id=match_to_link, is_owner=owner, session_token=token)
        self.db.add(player)
        self.db.commit()
        self.db.refresh(player)
        return player
    
    
    def get_player_id(self, player: Players) -> int:
        """
            Obtiene el id del jugador pasado por parametro.
            
            Args:
                player: Objeto jugador.
            Returns:
                player_id: id del jugador.
        """
        return player.id
        
    def get_players(self) -> List[Players]:
        """
            Obtiene la lista de todos los jugadores.
            
            Args:
                none.
            Returns:
                Players: Lista de players.
        """
        players = self.db.query(Players).all()
        return players
    
    def get_player_by_id(self, player_id: int) -> Players:
        """
            Obtiene un jugador según su id.
            
            Args:
                player_id: Id del jugador a buscar.
            Returns:
                Atributos del jugador en formato de diccionario.
        """
        try:
            player = self.db.query(Players).filter(Players.id == player_id).first()
            if player is None:
                raise NoResultFound
            return player
        except NoResultFound:
            raise ValueError("No player with that id")


    def delete_player(self, player_id: int):
        """
            Elimina un jugador según su id.
            
            Args:
                player_id: Id del jugador a eliminar.
            Returns:
                none.
        """
        try:
            
            player = self.db.query(Players).filter(Players.id == player_id).first()
            if player is None:
                raise NoResultFound
            self.db.delete(player)
            self.db.commit()
        except NoResultFound:
            raise ValueError("No player with that id")
            
            
    def update_player_with_match(self, player_id: int, match_id: int):
        """
            Asocia un jugador a una partida.
            
            Args:
                player_id: Id del jugador a asociar.
                match_id: Id de la partida a asociar.
            Returns:
                none.
        """
        try:
            player = self.db.query(Players).filter(Players.id == player_id).first()
            if player is None:
                raise NoResultFound
            player.match_id = match_id
            self.db.commit()
        except NoResultFound:
            raise ValueError("No player with that id")
            
            
    def update_turn_order(self, id: int, turn_order: int):
        """
            Actualiza el orden de turno de los jugadores.
            
            Args:
                id: Id del jugador.
                turn_order: nuevo orden de turno.
            Returns:
                none.
        """        
        try:
            player = self.db.query(Players).filter(Players.id == id).first()
            if player is None:
                raise NoResultFound
            player.turn_order = turn_order
            self.db.commit()
        except NoResultFound:
            raise ValueError("No player with that id")


    def get_user_turn_order(self, id: int) -> int:
        """
            Obtiene el orden de turno actual.
            
            Args:
                id: Id del jugador.
            Returns:
                turn_order: orden de turno.
        """
        player = self.db.query(Players).filter(Players.id == id).first()
        if player is None:
            raise ValueError("No player with that id")
        return player.turn_order