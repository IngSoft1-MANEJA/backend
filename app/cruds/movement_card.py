from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app.models.enums import Movements
from app.models.models import Matches, MovementCards
from app.utils.utils import validate_movement
from app.exceptions import MovementCardNotFound, NoMovementCardsFound


class MovementCardService:
    """
    Servicio para realizar operaciones CRUD sobre la tabla de MovementCards
    """

    def __init__(self, db: Session):
        """ Constructor de la clase, guardamos en el atributo
            db: La session de la base de datos."""
        self.db = db

    def create_movement_card(self, mov_type: str, match_id: int, player_owner: id = None):
        """
            Crea una nueva instancia de carta de movimiento en la base de datos.

            Args:
                mov_type: tipo de movimiento de la carta.
                match_id: id del match al que pertenece la carta.
                player_owner: id del jugador propietario de la carta, si no se especifica se asigna None.
            Returns:
                movement_card: el objeto movement_card creado.
        """
        validate_movement(mov_type)
        if player_owner is None:
            movement_card = MovementCards(mov_type=mov_type, match_id=match_id)
        else:
            movement_card = MovementCards(
                mov_type=mov_type, player_owner=player_owner, match_id=match_id)
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
        if not movement_cards:
            raise MovementCardNotFound("No movement cards found")
        return movement_cards

    def get_movement_card_by_id(self, movement_card_id: int):
        """
            Obtiene una carta de movimiento segun su id.

            Args:
                movement_card_id : Id de la carta a buscar
        """
        try:
            movement_card = self.db.query(MovementCards).filter(
                MovementCards.id == movement_card_id).one()
            return movement_card
        except NoResultFound:
            raise MovementCardNotFound(movement_card_id)

    def get_movement_card_by_user(self, player_owner: int) -> List[MovementCards]:
        """
        Obtiene la lista de cartas de movimiento de un usuario.

        Args:
            player_owner : Id del propietario de las cartas.
        Returns:
            MovementCards: Lista de movement_cards.
        """
        movement_cards = self.db.query(MovementCards).filter(
            MovementCards.player_owner == player_owner).all()
        if not movement_cards:
            return []
        return movement_cards

    def delete_movement_card(self, movement_card_id: int):
        """
            Elimina una carta de movimiento.

            Args:
                movement_card_id : Id de la carta a eliminar.
            Returns:
                none.
        """
        try:
            movement_card = self.db.query(MovementCards).filter(
                MovementCards.id == movement_card_id).one()
            self.db.delete(movement_card)
            self.db.commit()
        except NoResultFound:
            raise MovementCardNotFound(movement_card_id)

    def delete_movement_card_from_user(self, player_owner: int):
        """
        Elimina todas las cartas de movimiento de un usuario.

        Args:
            player_owner : Id del propietario de las cartas.
        Returns:
            none.
        """
        movement_cards = self.db.query(MovementCards).filter(
            MovementCards.player_owner == player_owner).all()
        if not movement_cards:
            raise MovementCardNotFound(
                f"No movement cards found for player owner {player_owner}")
        for movement_card in movement_cards:
            self.db.delete(movement_card)
        self.db.commit()

    def get_movement_card_by_match(self, match_id: int) -> List[MovementCards]:
        """
        Obtiene la lista de cartas de movimiento de un match.

        Args:
            match_id: Id del match.
        Returns:
            MovementCards: Lista de movement_cards.
        """
        movement_cards = self.db.query(MovementCards).filter(
            MovementCards.match_id == match_id).all()
        if not movement_cards:
            raise NoMovementCardsFound(match_id)
        return movement_cards

    def add_movement_card_to_player(self, player_id: int, movement_card_id: int) -> MovementCards:
        """
        Agrega una carta de movimiento a un jugador.

        Args:
            player_id : Id del jugador.
            movement_card_id : Id de la carta de movimiento.
        Returns:
            none.
        """
        movement_card = self.get_movement_card_by_id(movement_card_id)
        movement_card.player_owner = player_id
        self.db.commit()
        self.db.refresh(movement_card)
        return movement_card

    def get_movement_cards_without_owner(self, match_id: int) -> List[MovementCards]:
        """
        Obtiene la lista de cartas de movimiento sin jugadores asignados.
        Args:
            match_id : Id del match.

        Returns:
            MovementCards: Lista de movement_cards.
        """
        movement_cards = self.db.query(MovementCards).filter(
            MovementCards.match_id == match_id,
            MovementCards.player_owner == None).all()
        return movement_cards

    def update_card_owner_to_none(self, movement_card_id: int) -> MovementCards:
        """
        Actualiza el propietario de una carta de movimiento.

        Args:
            movement_card_id : Id de la carta de movimiento.
            player_id : Id del nuevo propietario.
        Returns:
            none.
        """
        movement_card = self.get_movement_card_by_id(movement_card_id)
        movement_card.player_owner = None
        self.db.commit()
        self.db.refresh(movement_card)
        return movement_card

    def create_movement_deck(self, match_id: int):
        match = self.db.get(Matches, match_id)
        if match is None:
            raise NoResultFound("Match not found")

        deck = []
        for mov in Movements:
            for _ in range(7):
                movement_card = MovementCards(mov_type=mov.value, match_id=match_id)
                deck.append(movement_card)
        self.db.add_all(deck)
        self.db.commit()