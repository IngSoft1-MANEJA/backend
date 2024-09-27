from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound
from typing import List
from models.models import MovementCards
from database import engine

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class MovementCardService:
    """
    Servicio para realizar operaciones CRUD sobre la tabla de MovementCards
    Metodos: 
        - create_movement_card
        - get_movement_cards
        - get_movement_card_by_id
        - get_movement_card_by_user
        - delete_movement_card
        - delete_movement_card_from_user
        
    """
    def create_movement_card(self, movement : str, color : str):
        """
            Crea una nueva instancia de carta de movimiento en la base de datos.
            
            Args:
                movement: movimiento de la carta.
                color: color de la carta.
            Returns:
                movement_card: el objeto movement_card creado.
        """
        session = Session()
        try:
            movement_card = MovementCards(movement=movement, color=color)
            session.add(movement_card)
            session.commit()
            session.refresh(movement_card)
            return movement_card
        finally:
            session.close()
        
    def get_movement_cards(self) -> List[MovementCards]:
        """
            Obtiene la lista de todas las cartas de movimiento.
            
            Args:
                none.
            Returns:
                MovementCards: Lista de movement_cards.
        """
        session = Session()
        try:
            movement_cards = session.query(MovementCards).all()
            return movement_cards
        finally:
            session.close()
    
    def get_movement_card_by_id(self, movement_card_id : int):
        """
            Obtiene una carta de movimiento segun su id.
            
            Args:
                movement_card_id : Id de la carta a buscar
        """
        session = Session()
        try:
            movement_card = session.query(MovementCards).filter(MovementCards.id == movement_card_id).one()
            return movement_card
        except NoResultFound:
            raise NoResultFound(f"Movement card with id {movement_card_id} not found, can't get")
        finally:
            session.close()
        
    def get_movement_card_by_user(self, user_id : int) -> List[MovementCards]:
        """
            Obtiene la lista de cartas de movimiento de un usuario.
            
            Args:
                user_id : Id del usuario.
            Returns:
                MovementCards: Lista de movement_cards.
        """
        session = Session()
        try:
            movement_cards = session.query(MovementCards).filter(MovementCards.user_id == user_id).all()
            return movement_cards
        finally:
            session
            
    def delete_movement_card(self, movement_card_id : int):
        """
            Elimina una carta de movimiento segun su id.
            
            Args:
                movement_card_id : Id de la carta a eliminar
            Returns:
                none.
        """
        session = Session()
        try:
            movement_card = session.query(MovementCards).filter(MovementCards.id == movement_card_id).first()
            session.delete(movement_card)
            session.commit()
        except NoResultFound:
            raise ValueError("No movement card with that id")
        finally:
            session.close()
    
    def delete_movement_card_from_user(self, user_id : int):
        """
            Elimina todas las cartas de movimiento de un usuario.
            
            Args:
                user_id : Id del usuario.
            Returns:
                none.
        """
        session = Session()
        try:
            movement_cards = session.query(MovementCards).filter(MovementCards.user_id == user_id).all()
            for movement_card in movement_cards:
                session.delete(movement_card)
            session.commit()
        except NoResultFound:
            raise ValueError("No movement cards for that user")
        finally:
            session.close()
            
    