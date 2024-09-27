from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound
from typing import List
from models.models import Matches
from database import engine

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class MatchService:
    """
    Servicio para realizar operaciones CRUD sobre la tabla de Matches:
        Metodos disponibles:
            - create_match
            - get_match_by_id
            - get_all_matches
            - update_match
            - delete_match (El cliente desea que no se eliminen matches, pero se puede agregar)
    """

    def create_match(self, name: str, max_players: int, is_public: bool):
        """
            Crea un nuevo match en la database.
            
            Args:
                name: nombre del match.
                max_players: cantidad maxima de jugadores.
                is_public: si el match es publico o privado.
            Returns:
                Matches: el objeto match creado.
        """
        session = Session()
        try:
            match = Matches(match_name=name, max_players=max_players, 
                            is_public=True, is_started=False, amount_players=0)
            session.add(match)
            session.commit()
            session.refresh(match)
        finally:
            session.close()
    
    def get_match_by_id(self, match_id: int):        
        """
            Obtiene un match segun el id dado.
            
            Args:
                match_id: id del match.
            Returns:
                Atributos del match en formato de diccionario.
        """
        session = Session()
        try:
            match = session.query(Matches).filter(Matches.id == match_id).one()
            return {'id ': match.id, 'name': match.match_name, 'max_players': match.max_players,
                    'is_public': match.is_public, 'is_started': match.is_started}
        except NoResultFound:
            raise NoResultFound(f"Match with id {match_id} not found, can't get")
        finally:
            session.close()
            
    def get_all_matches(self, available: bool = False):
        """
            Obtiene la lista de todos los matches, si se quiere obtener solo los disponibles
            se debe pasar el parametro available como True.
            
            Args:
                available: si se quieren obtener solo los matches disponibles.
            Returns:
                Matches: Lista de matches.
        """
        session = Session()
        try:
            if available:
                matches = session.query(Matches).filter(Matches.is_started == False and Matches.max_players < 4).all()
            else:
                matches = session.query(Matches).all()
            return matches
        except NoResultFound:
            raise NoResultFound("No matches found")
        finally:
            session.close()
    
    def update_match(self, match_id: int, is_started: bool, new_amount_players: int):
        """
            Actualiza los atributos de un match en la database.
            
            Args:
                match_id: id del match a actualizar.
                is_public: si el match es publico o privado.
                new_amount_players: nueva cantidad de jugadores.
            Returns:
                Matches: el objeto match actualizado.
        """
        session = Session()
        try:
            match = session.query(Matches).filter(Matches.id == match_id).one()
            match.is_started = is_started
            match.amount_players = new_amount_players
            session.commit()
            session.refresh(match)
            return match
        except NoResultFound:
            raise NoResultFound(f"Match with id {match_id} not found, can't update")
        finally:
            session.close()