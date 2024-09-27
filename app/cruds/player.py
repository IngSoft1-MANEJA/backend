from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound
from typing import List
from models.models import Players
from database import engine

# Crear una sesion para interactuar con la base de datos
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class PlayerService:
    """
    Servicio para realizar operaciones CRUD sobre la tabla de Matches
    Metodos: 
        - create_player
        - get_players
        - get_player_by_id
        - get_user_turn_order
        - update_turn_order
        - delete_player
    """
    def create_player(self, name : str):
        """
            Crea una nueva instancia de jugador en la base de datos.
            
            Args:
                name: nombre del jugador.
            Returns:
                player: el objeto player creado.
        """
        session = Session()
        try:
            player = Players(name=name)
            session.add(player)
            session.commit()
            session.refresh(player)
            return player
        finally:
            session.close()
        
    def get_players(self) -> List[Players]:
        """
            Obtiene la lista de todos los jugadores.
            
            Args:
                none.
            Returns:
                Players: Lista de players.
        """
        session = Session()
        try:
            players = session.query(Players).all()
            return players
        finally:
            session.close()


    def get_player_by_id(self, player_id : int):
        """
            Obtiene un jugador segun su id.
            
            Args:
                player_id : Id del jugador a buscar
            Returns:
                player: El jugador con el id propuesto.
        """
        session = Session()
        try:
            player = session.query(Players).filter(player_id == Players.id).first()
            return player
  
        except NoResultFound:
            raise ValueError("No player with that id")

        finally:
            session.close()

    def delete_player(self, player_id : int):
        """
            Elimina un jugador segun su id.
            
            Args:
                player_id : Id del jugador a eliminar
            Returns:
                none.
        """
        session = Session()
        try:
            player = session.query(Players).filter(Players.id == player_id).first()
            session.delete(player)
            session.commit()
        except NoResultFound:
            raise ValueError("No player with that id")
        finally:
            session.close()
            
    def update_player_with_match(self, player_id : int, match_id : int):
        """
            Asocia un jugador a una partida.
            
            Args:
                player_id : Id del jugador a asociar
                match_id : Id de la partida a asociar
            Returns:
                none.
        """
        session = Session()
        try:
            player = session.query(Players).filter(Players.id == player_id).first()
            player.match_id = match_id
            session.commit()
        except NoResultFound:
            raise ValueError("No player with that id")
        finally:
            session.close()
            
    def update_turn_order(self, turn_order : int):
        """
            Actualiza el orden de turno de los jugadores.
            
            Args:
                turn_order : nuevo orden de turno.
            Returns:
                none.
        """
        session = Session()
        try:
            players = session.query(Players).all()
            for player in players:
                player.turn_order = turn_order
            session.commit()
        finally:
            session.close()

    def get_user_turn_order(self, id: int) -> int:
        """
            Obtiene el orden de turno actual.
            
            Args:
                none.
            Returns:
                turn_order: orden de turno.
        """
        session = Session()
        try:
            player = session.query(Players).filter(Players.id == id).first()
            return player.turn_order
        finally:
            session.close()