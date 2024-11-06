from copy import copy
from datetime import datetime
from random import shuffle
from sqlalchemy import DateTime
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from typing import List
from app.models.models import Matches, Players
from app.models.enums import MatchState
import app.utils.utils as utils


class MatchService:
    """
    Servicio para realizar operaciones CRUD sobre la tabla de Matches:
    """

    def __init__(self, db: Session):
        """ Constructor de la clase, guardamos en el atributo
            db: La session de la base de datos."""
        self.db = db

    def create_match(self, name: str, max_players: int, public: bool):
        """
            Crea un nuevo match en la database.

            Args:
                name: nombre del match.
                max_players: cantidad maxima de jugadores.
                is_public: si el match es publico o privado.
            Returns:
                Matches: el objeto match creado.
        """
        try:
            utils.validate_match_name(name)
            utils.validate_max_players(max_players)
            match = Matches(match_name=name, max_players=max_players, 
                            is_public=public, state = MatchState.WAITING.value, current_players=1)
            self.db.add(match)
            self.db.commit()
            self.db.refresh(match)
            return match
        except Exception as e:
            raise e

    def set_players_order(self, match: Matches) -> List[Players]:
        """Setea el orden de los jugadores en el match de manera random.

        Setea el current_player_turn a 1.
        
        Returns:
            List[Players]: Lista de jugadores con el orden seteado.
        """
        players = self.db.query(Players).filter(Players.match_id == match.id).all()
        shuffle(players)

        for i, player in enumerate(players, start=1):
            player.turn_order = i

        match.current_player_turn = 1

        self.db.commit()

        return players

    def get_match_by_id(self, match_id: int):        
        """
            Obtiene un match segun el id dado.

            Args:
                match_id: id del match.
            Returns:
                Atributos del match en formato de diccionario.
        """

        try:
            match = self.db.query(Matches).filter(Matches.id == match_id).one()
            return match
        except NoResultFound:
            raise NoResultFound(
                f"Match with id {match_id} not found, can't get")

    def get_match_id(self, match: Matches):
        """
            Obtiene el id de un match.

            Args:
                match: objeto match.
            Returns:
                int: id del match.
        """
        return match.id

    def get_all_matches(self, available: bool = False):
        """
            Obtiene la lista de todos los matches, si se quiere obtener solo los disponibles
            se debe pasar el parametro available como True.

            Args:
                available: si se quieren obtener solo los matches disponibles.
            Returns:
                Matches: Lista de matches.
        """
        try:
            if available:
                matches = self.db.query(Matches).filter(
                    Matches.state == MatchState.WAITING.value, Matches.current_players < Matches.max_players).all()
            else:
                matches = self.db.query(Matches).all()
            return matches
        except NoResultFound:
            raise NoResultFound("No matches found")
    
    
    def update_match(self, match_id: int, new_state: str = None, new_amount_players: int = None, new_started_turn_time: DateTime = None):
        """
            Actualiza los atributos de un match en la database.

            Args:
                match_id: id del match a actualizar.
                new_state: si el match ha comenzado.
                new_amount_players: nueva cantidad de jugadores.
            Returns:
                No Returns.
        """
        try:
            match = self.db.query(Matches).filter(Matches.id == match_id).one()
            if new_state:
                match.state = new_state
            if new_amount_players != None:
                match.current_players = new_amount_players
            if new_started_turn_time != None:
                match.started_turn_time = new_started_turn_time
            self.db.commit()
            self.db.refresh(match)
        except NoResultFound:
            raise NoResultFound(
                f"Match with id {match_id} not found, can't update")

# El cliente no desea eliminar matches, pero lo dejamos ya hecho
    def delete_match(self, match_id: int):
        """
            Elimina un match de la database.

            Args:
                match_id: id del match a eliminar.
            Returns:
                No Returns.
        """
        try:
            match = self.db.query(Matches).filter(Matches.id == match_id).one()
            self.db.delete(match)
            self.db.commit()
        except NoResultFound:
            raise NoResultFound(
                f"Match with id {match_id} not found, can't delete")
        except Exception as e:
            raise e

    def update_turn(self, match_id: int, turn: int):
        try:
            match = self.db.query(Matches).filter(Matches.id == match_id).one()
            match.current_player_turn = turn
            # self.db.add(match)
            self.db.commit()
            self.db.refresh(match)
        except NoResultFound:
            raise NoResultFound(
                f"Match with id {match_id} not found, can't update")