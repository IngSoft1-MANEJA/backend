from sqlalchemy.exc import NoResultFound
from typing import List
from app.models.models import Tiles
from app.utils.utils import validate_color, validate_position

class TileService:
    """
    Servicio para realizar operaciones CRUD sobre la tabla de Tiles
    Metodos:
            - __init__
            - create_tile
            - get_all_tiles
            - get_tile_by_id
            - update_tile_color
            - delete_tile
    """
    def __init__(self, db):
        """ Constructor de la clase, guardamos en el atributo
            db: La session de la base de datos."""
        self.db = db

    def create_tile(self, board_id : int, color : str, position_x : int, position_y : int):
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
        new_tile = Tiles(board_id=board_id, color=color, positionX = position_x, positionY = position_y)
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
        return tiles

    def get_tile_by_id(self, tile_id : int) -> Tiles:
        """
        Obtiene una ficha de la base de datos por su id.
        Args:
            tile_id: Id de la ficha.
        Returns:
            tile: Ficha.
        """
        tile = self.db.query(Tiles).filter(Tiles.id == tile_id).one()
        return tile

    def update_tile_position(self, tile_id : int, positionX: int, positionY: int):
        """
        Actualiza el color de una ficha.
        Args:
            tile_id: Id de la ficha.
            color: Color de la ficha.
        """
        validate_position(positionX, positionY)
        tile = self.db.query(Tiles).filter(Tiles.id == tile_id).one()
        tile.positionX = positionX
        tile.positionY = positionY
        self.db.commit()

    def delete_tile(self, tile_id : int):
        """
        Elimina una ficha de la base de datos.
        Args:
            tile_id: Id de la ficha.
        """
        tile = self.db.query(Tiles).filter(Tiles.id == tile_id).one()
        self.db.delete(tile)
        self.db.commit()