from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app.models.models import ShapeCards
from app.utils.utils import validate_shape, validate_add_shape_card_to_hand


class ShapeCardService():
    """
    Servicio para realizar operaciones CRUD sobre la tabla de ShapeCards
    """

    def __init__(self, db: Session):
        """ Constructor de la clase, guardamos en el atributo
            db: La session de la base de datos."""
        self.db = db

    def create_shape_card(self, shape: str, is_hard: bool, is_visible: bool,
                          player_owner: int) -> ShapeCards:
        """
            Crea una nueva instancia de carta de figura en la base de datos.

            Args:
                shape: figura de la carta.
                color: color de la carta.
                is_hard: si la carta es dificil.
                is_visible: si la carta es visible.
                player_owner: id del jugador propietario de la carta.

            Returns:
                shape_card: el objeto shape_card creado.
        """
        validate_shape(shape)
        shape_card = ShapeCards(shape_type=shape, is_hard=is_hard, is_visible=is_visible,
                                is_blocked=False, player_owner=player_owner)
        self.db.add(shape_card)
        self.db.commit()
        self.db.refresh(shape_card)
        return shape_card

    def get_shape_cards(self) -> List[ShapeCards]:
        """
            Obtiene la lista de todas las cartas de figura.

            Args:
                none.
            Returns:
                ShapeCards: Lista de shape_cards.
        """

        shape_cards = self.db.query(ShapeCards).all()
        return shape_cards

    def get_shape_card_id(self, shape_card: ShapeCards) -> int:
        """
            Obtiene el id de una carta de figura.

            Args:
                shape_card: Objeto de carta de figura.
            Returns:
                int: Id de la carta de figura.
        """
        return shape_card.id

    def get_shape_card_by_id(self, shape_card_id: int):
        """
            Obtiene una carta de figura segun su id.

            Args:
                shape_card_id : Id de la carta de forma a buscar
        """
        try:
            shape_card = self.db.query(ShapeCards).filter(
                ShapeCards.id == shape_card_id).one()
            return shape_card
        except NoResultFound:
            raise NoResultFound(
                f"ShapeCard with id {shape_card_id} not found, can't get")

    def get_shape_card_by_player(self, player_id: int) -> List[ShapeCards]:
        """
            Obtiene las cartas de figura de un jugador.

            Args:
                user_id : Id del usuario del que se quieren obtener las cartas.
        """
        try:
            shapes_cards = self.db.query(ShapeCards).filter(
                ShapeCards.player_owner == player_id).all()
            return shapes_cards
        except NoResultFound:
            raise NoResultFound(
                f"The user with id {player_id} has no shape cards")

    def delete_shape_card(self, shape_card_id: int):
        """
            Elimina una carta de figura segun su id.

            Args:
                shape_card_id : Id de la carta de figura a eliminar
        """
        try:
            shape_card = self.db.query(ShapeCards).filter(
                ShapeCards.id == shape_card_id).one()
            self.db.delete(shape_card)
            self.db.commit()
        except NoResultFound:
            raise NoResultFound(
                f"ShapeCard with id {shape_card_id} not found, can't delete")

    def add_shape_card_to_player(self, player_id: int, shape_card_id: int):
        """
            Agrega una carta de figura a un usuario.

            Args:
                user_id : Id del usuario al que se le quiere agregar la carta.
                shape_card_id : Id de la carta de forma a agregar.
        """
        try:
            count_cards = self.db.query(ShapeCards).filter(
                ShapeCards.player_owner == player_id).count()
            validate_add_shape_card_to_hand(player_id, count_cards)
            shape_card = self.db.query(ShapeCards).filter(
                ShapeCards.id == shape_card_id).one()
            shape_card.player_owner = player_id
            self.db.commit()
        except NoResultFound:
            raise NoResultFound(
                f"ShapeCard with id {shape_card_id} not found, can't add")

    def update_shape_card(self, shape_card_id: int, is_visible: bool, is_blocked: bool):
        """
            Actualiza los atributos de una carta de figura.

            Args:
                shape_card_id : Id de la carta de figura a actualizar.
                is_visible : Visibilidad de la carta.
                is_blocked : Bloqueo de la carta.
        """
        try:
            shape_card = self.db.query(ShapeCards).filter(
                ShapeCards.id == shape_card_id).one()
            shape_card.is_visible = is_visible
            shape_card.is_blocked = is_blocked
            self.db.commit()
        except NoResultFound:
            raise NoResultFound(
                f"ShapeCard with id {shape_card_id} not found, can't update")

    def get_visible_cards(self, player_id: int) -> List[ShapeCards]:
        try:
            cards = self.db.query(ShapeCards).filter(ShapeCards.player_owner == player_id)
            return cards
        
        # REVISAR CUANDO SEA 0
        except NoResultFound:
            raise NoResultFound(f"Player with id {player_id} has not visible cards")