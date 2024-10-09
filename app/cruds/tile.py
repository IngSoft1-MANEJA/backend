from typing import List
from sqlalchemy.exc import NoResultFound

from app.models.models import Tiles
from app.utils.utils import validate_color, validate_position
from app.exceptions import TileNotFound, NoTilesFound


class TileService:
    """
    Servicio para realizar operaciones CRUD sobre la tabla de Tiles
    """

    def __init__(self, db):
        """ Constructor de la clase, guardamos en el atributo
            db: La session de la base de datos."""
        self.db = db

    def create_tile(self, board_id: int, color: str, position_x: int, position_y: int):
        """
        Crea una nueva ficha en la base de datos.
        Args:
            board_id: Id del tablero al cual pertenece la ficha.
            color: Color de la ficha.
        Returns:
            new_tile: Ficha creada.
        """
        validate_color(color)
        validate_position(position_x, position_y)
        new_tile = Tiles(board_id=board_id, color=color,
                         position_x=position_x, position_y=position_y)
        self.db.add(new_tile)
        self.db.commit()
        return new_tile

    def get_all_tiles(self) -> List[Tiles]:
        """
        Obtiene todas las fichas de la base de datos.
        Returns:
            tiles: Lista de fichas.
        """
        tiles = self.db.query(Tiles).all()
        if not tiles:
            raise NoTilesFound()
        return tiles

    def get_tile_by_id(self, tile_id: int) -> Tiles:
        """
        Obtiene una ficha de la base de datos por su id.
        Args:
            tile_id: Id de la ficha.
        Returns:
            tile: Ficha.
        """
        try:
            tile = self.db.query(Tiles).filter(Tiles.id == tile_id).one()
            return tile
        except NoResultFound:
            raise TileNotFound(tile_id)

    def update_tile_position(self, tile_id: int, position_x: int, position_y: int):
        """
        Actualiza el color de una ficha.
        Args:
            tile_id: Id de la ficha.
            color: Color de la ficha.
        """
        validate_position(position_x, position_y)
        tile = self.db.query(Tiles).filter(Tiles.id == tile_id).one()
        tile.position_x = position_y
        tile.position_y = position_x
        self.db.commit()
        self.db.refresh(tile)

    def delete_tile(self, tile_id: int):
        """
        Elimina una ficha de la base de datos.
        Args:
            tile_id: Id de la ficha.
        """
        tile = self.db.query(Tiles).filter(Tiles.id == tile_id).one()
        self.db.delete(tile)
        self.db.commit()
