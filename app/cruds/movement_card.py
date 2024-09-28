from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from typing import List
from app.models.models import MovementCards
from app.database import engine

class MovementCardService:
    """
    Servicio para realizar operaciones CRUD sobre la tabla de MovementCards
    Metodos: 
        - __init__
        - create_movement_card
        - get_movement_cards
        - get_movement_card_by_id
        - get_movement_card_by_user
        - delete_movement_card
        - delete_movement_card_from_user
    """
    def __init__(self, db: Session):
        """ Constructor de la clase, guardamos en el atributo
            db: La session de la base de datos."""
        self.db = db
        
        
    def create_movement_card(self, movement : str, color : str):
        """
            Crea una nueva instancia de carta de movimiento en la base de datos.
            
            Args:
                movement: movimiento de la carta.
                color: color de la carta.
            Returns:
                movement_card: el objeto movement_card creado.
        """
        movement_card = MovementCards(movement=movement, color=color)
        self.db.add(movement_card)
        self.db.commit()
        self.db.refresh(movement_card)
        return movement_card
    
    def get_movement_cards(self) -> List[MovementCards]:
        """
            Obtiene la lista de todas las cartas de movimiento.
            
            Args:
                none.
            Returns:
                MovementCards: Lista de movement_cards.
        """
        movement_cards = self.db.query(MovementCards).all()
        return movement_cards
    
    
    def get_movement_card_by_id(self, movement_card_id : int):
        """
            Obtiene una carta de movimiento segun su id.
            
            Args:
                movement_card_id : Id de la carta a buscar
        """
        try:
            movement_card = self.db.query(MovementCards).filter(MovementCards.id == movement_card_id).one()
            return movement_card
        except NoResultFound:
            raise NoResultFound(f"Movement card with id {movement_card_id} not found, can't get")
        
        
    def get_movement_card_by_user(self, user_id : int) -> List[MovementCards]:
        """
            Obtiene la lista de cartas de movimiento de un usuario.
            
            Args:
                user_id : Id del usuario.
            Returns:
                MovementCards: Lista de movement_cards.
        """
        movement_cards = self.db.query(MovementCards).filter(MovementCards.user_id == user_id).all()
        return movement_cards

            
    def delete_movement_card(self, movement_card_id : int):
        """
            Elimina una carta de movimiento segun su id.
            
            Args:
                movement_card_id : Id de la carta a eliminar
            Returns:
                none.
        """
        try:
            movement_card = self.db.query(MovementCards).filter(MovementCards.id == movement_card_id).first()
            self.db.delete(movement_card)
            self.db.commit()
        except NoResultFound:
            raise ValueError("No movement card with that id")
    
    
    def delete_movement_card_from_user(self, user_id : int):
        """
            Elimina todas las cartas de movimiento de un usuario.
            
            Args:
                user_id : Id del usuario.
            Returns:
                none.
        """
        try:
            movement_cards = self.db.query(MovementCards).filter(MovementCards.user_id == user_id).all()
            for movement_card in movement_cards:
                self.db.delete(movement_card)
            self.db.commit()
        except NoResultFound:
            raise ValueError("No movement cards for that user")
  
            
    