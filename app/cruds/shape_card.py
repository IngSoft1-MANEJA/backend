from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from typing import List
from models.models import ShapeCards
from database import engine

class ShapeCardService:
    """
    Servicio para realizar operaciones CRUD sobre la tabla de ShapeCards
    Metodos: 
        - __init__
        - create_shape_card
        - get_shape_cards
        - get_shape_card_by_id
        - get_shape_card_by_user
        - delete_shape_card
        - delete_shape_card_from_user
        - update_shape_card
        
    """
    def create_shape_card(self, db:Session, shape : str, color : str):
        """
            Crea una nueva instancia de carta de figura en la base de datos.
            
            Args:
                shape: figura de la carta.
                color: color de la carta.
            Returns:
                shape_card: el objeto shape_card creado.
        """
   
        shape_card = ShapeCards(shape=shape, color=color)
        db.add(shape_card)
        db.commit()
        db.refresh(shape_card)
        return shape_card

        
    def get_shape_cards(self, db:Session) -> List[ShapeCards]:
        """
            Obtiene la lista de todas las cartas de figura.
            
            Args:
                none.
            Returns:
                ShapeCards: Lista de shape_cards.
        """
 
        shape_cards = db.query(ShapeCards).all()
        return shape_cards

    
    def get_shape_card_by_id(self, db:Session, shape_card_id : int):
        """
            Obtiene una carta de figura segun su id.
            
            Args:
                shape_card_id : Id de la carta de forma a buscar
        """
        try:
            shape_card = db.query(ShapeCards).filter(ShapeCards.id == shape_card_id).one()
            return shape_card
        except NoResultFound:
            raise NoResultFound(f"ShapeCard with id {shape_card_id} not found, can't get")

            
    def get_shape_card_by_user(self, db:Session, user_id : int):
        """
            Obtiene las cartas de figura de un usuario.
            
            Args:
                user_id : Id del usuario del que se quieren obtener las cartas.
        """
        try: 
            shapes_cards = db.query(ShapeCards).filter(ShapeCards.player_owner == user_id).all()
            return shapes_cards
        except NoResultFound:
            raise NoResultFound(f"The user with id {user_id} has no shape cards")
            
    def delete_shape_card(self, db:Session, shape_card_id : int):
        """
            Elimina una carta de figura segun su id.
            
            Args:
                shape_card_id : Id de la carta de figura a eliminar
        """
        try:
            shape_card = db.query(ShapeCards).filter(ShapeCards.id == shape_card_id).one()
            db.delete(shape_card)
            db.commit()
        except NoResultFound:
            raise NoResultFound(f"ShapeCard with id {shape_card_id} not found, can't delete")
            
    def delete_shape_card_from_user(self, db:Session, user_id : int, shape_card_id: int):
        """
            Elimina una carta de figura de un usuario.
            
            Args:
                user_id : Id del usuario del que se quiere eliminar la carta.
                shape_card_id : Id de la carta de forma a eliminar.
        """
        try:
            shape_card = db.query(ShapeCards).filter(ShapeCards.player_owner == user_id and ShapeCards.id == shape_card_id).one()
            db.delete(shape_card)
            db.commit()
        except NoResultFound:
            raise NoResultFound(f"ShapeCard with id {shape_card_id} not found, can't delete")
        except ValueError:
            raise ValueError(f"The user with id {user_id} has no shape cards")
            
    def update_shape_card(self, db:Session, shape_card_id : int, is_visible : bool, is_blocked: bool):
        """
            Actualiza los atributos de una carta de figura.
            
            Args:
                shape_card_id : Id de la carta de figura a actualizar.
                is_visible : Visibilidad de la carta.
                is_blocked : Bloqueo de la carta.
        """
        try:
            shape_card = db.query(ShapeCards).filter(ShapeCards.id == shape_card_id).one()
            shape_card.is_visible = is_visible
            shape_card.is_blocked = is_blocked
            db.commit()
        except NoResultFound:
            raise NoResultFound(f"ShapeCard with id {shape_card_id} not found, can't update")


        