from app.database import Base
from typing import List
from .enums import Colors, Shapes, Movements
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey

# ================================================ MATCHES MODELS =================================#


class Matches(Base):
    __tablename__ = 'matches'
    # --------------------------------- ATTRIBUTES -------------------------#
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    match_name: Mapped[str] = mapped_column(String(50))
    started: Mapped[bool]
    is_public: Mapped[bool]
    max_players: Mapped[int]
    current_player_turn = Column(
        Integer, ForeignKey('players.id'), nullable=True)

    # --------------------------------- RELATIONSHIPS -----------------------#
    players: Mapped[List["Players"]] = relationship("Players", back_populates="match",
                                                    cascade="all, delete-orphan",
                                                    foreign_keys="[Players.match_id]",
                                                    post_update=True)
    board: Mapped["Boards"] = relationship("Boards", back_populates="match",
                                           cascade="all, delete-orphan",
                                           uselist=False,
                                           post_update=True)

    # --------------------------------- REPR -------------------------#
    def __repr__(self):
        return (f"Match(id={self.id!r}, match_name={self.match_name!r}, "
                f"started={self.started!r}, is_public={self.is_public!r}, "
                f"max_players={self.max_players!r})")

# ================================================ PLAYERS MODELS =================================#


class Players(Base):
    __tablename__ = 'players'
    # --------------------------------- ATTRIBUTES -------------------------#
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    player_name: Mapped[str] = mapped_column(String(50))
    is_owner: Mapped[bool]
    session_token: Mapped[str]
    turn_order: Mapped[int]
    match_id: Mapped[int] = mapped_column(ForeignKey('matches.id'))

    # --------------------------------- REPR -------------------------------#
    match: Mapped["Matches"] = relationship(
        "Matches", back_populates="players", foreign_keys=[match_id], post_update=True)
    shape_cards: Mapped[List["ShapeCards"]] = relationship(
        "ShapeCards", back_populates="owner", post_update=True)
    movement_cards: Mapped[List["MovementCards"]] = relationship(
        "MovementCards", back_populates="owner", post_update=True)

    # --------------------------------- VALIDATORS -------------------------#
    @validates('turn_order')
    def validate_turn_order(self, key, turn_order):
        if turn_order < 1 or turn_order > 4:
            raise ValueError(
                f"Turn order {turn_order} is not valid: must be between 1 and 4")
        return turn_order

    # --------------------------------- REPR -------------------------------#
    def __repr__(self):
        return (f"Player(id={self.id!r}, player_name={self.player_name!r}, "
                f"is_owner={self.is_owner!r}, match_id={self.match_id!r})")

# ================================================ BOARDS MODELS ==================================#


class Boards(Base):
    __tablename__ = 'boards'
    # --------------------------------- ATTRIBUTES -------------------------#
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ban_color: Mapped[str] = mapped_column(String(50), nullable=False)  #
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey('matches.id'))

    # --------------------------------- RELATIONSHIPS -----------------------#
    match: Mapped["Matches"] = relationship(
        "Matches", back_populates="board", lazy='joined', post_update=True)
    tiles: Mapped[List["Tiles"]] = relationship(
        "Tiles", back_populates="board", post_update=True)

    # --------------------------------- VALIDATORS -------------------------#
    @validates('ban_color')
    def validate_ban_color(self, key, color):
        if color not in Colors.__members__:
            raise ValueError(f"Color {color} is not a valid color to ban, must be one of {
                             Colors.__members__}")
        return color

    # --------------------------------- REPR -------------------------------#
    def __repr__(self):
        return (f"Board(id={self.id!r}, match_id={self.match_id!r})")

# ================================================ TILES MODELS ===================================#


class Tiles(Base):
    __tablename__ = 'tiles'
    # --------------------------------- ATTRIBUTES -------------------------#
    id: Mapped[int] = mapped_column(primary_key=True)
    color: Mapped[Colors]
    positionX: Mapped[int] = mapped_column(Integer)
    positionY: Mapped[int] = mapped_column(Integer)
    board_id: Mapped[int] = mapped_column(Integer, ForeignKey('boards.id'))
    board: Mapped["Boards"] = relationship("Boards", back_populates="tiles")

    # --------------------------------- VALIDATORS -------------------------#
    @validates('PositionX', 'PositionY')
    def validate_position(self, key, position):
        if position < 0 or position > 5:
            raise ValueError(f"Position {position} is out of bounds")
        return position

    # --------------------------------- REPR -------------------------------#
    def __repr__(self):
        return (f"Tile(id={self.id!r}, color={self.color!r}, "
                f"positionX={self.positionX!r}, positionY={self.positionY!r}, "
                f"board_id={self.board_id!r})")

# ================================================ SHAPECARDS MODELS ==============================#


class ShapeCards(Base):
    __tablename__ = 'shapeCards'
    # --------------------------------- ATTRIBUTES -------------------------#
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shape_type: Mapped[str]
    is_hard: Mapped[bool]
    is_visible: Mapped[bool]
    is_blocked: Mapped[bool]
    player_owner: Mapped[int] = mapped_column(
        Integer, ForeignKey('players.id'))

    # --------------------------------- RELATIONSHIPS -----------------------#
    owner: Mapped["Players"] = relationship(
        "Players", back_populates="shape_cards", post_update=True)

    # --------------------------------- VALIDATORS -------------------------#
    @validates('shape_type')
    def validate_shape(self, key, shape):
        if shape not in Shapes.__members__:
            raise ValueError(f"Shape {shape} is not valid shape type")
        return shape

    # -------------------------------- REPR -------------------------------#
    def __repr__(self):
        return (f"ShapeCard(id={self.id!r}, name={self.name!r}, "
                f"shape_type={self.shape_type!r}, is_hard={self.is_hard!r}, "
                f"is_visible={self.is_visible!r}, is_blocked={
                    self.is_blocked!r}, "
                f"player_owner={self.player_owner!r})")

# ================================================ MOVEMENTCARDS MODELS ===========================#


class MovementCards(Base):
    __tablename__ = 'movementCards'  # Cambiado a minúsculas
    # --------------------------------- ATTRIBUTES -------------------------#
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    mov_type: Mapped[str]
    player_owner: Mapped[int] = mapped_column(ForeignKey('players.id'))

    # --------------------------------- RELATIONSHIPS -----------------------#
    owner: Mapped["Players"] = relationship(
        "Players", back_populates="movement_cards", post_update=True)

    # --------------------------------- VALIDATORS -------------------------#
    @validates('mov_type')
    def validate_movement(self, key, movement):
        if movement not in Movements.__members__:
            raise ValueError(f"Movement {movement} is not valid mov type")
        return movement

    # --------------------------------- REPR -------------------------------#
    def __repr__(self):
        return (f"MovementCard(id={self.id!r}, name={self.name!r}, "
                f"mov_type={self.mov_type!r}, player_owner={self.player_owner!r})")

# =================================================================================================#
