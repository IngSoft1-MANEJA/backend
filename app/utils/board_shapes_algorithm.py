"""
This module provides an algorithm to find figures in a matrix of shapes.
"""

import collections
import copy
import enum
import typing
from app.models.enums import Colors

T = typing.TypeVar("T")
Matrix: typing.TypeAlias = list[list[T]]


class Board:

    def __init__(self, board_matrix: Matrix[Colors]) -> None:

        self._matrix: Matrix[Colors] = copy.deepcopy(board_matrix)
        self.shape: tuple[int, int] = (len(board_matrix), len(board_matrix[0]))

    def __getitem__(self, i: int):
        return self._matrix[i]


Coordinate = collections.namedtuple("Coordinate", ["x", "y"])


class Figure:
    def __init__(self, coordinates: tuple[Coordinate, ...]) -> None:
        self.coordinates = tuple(sorted(coordinates))

    def __hash__(self) -> int:
        return hash(self.coordinates)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Figure):
            return self.coordinates == other.coordinates
        elif isinstance(other, tuple):
            return self.coordinates == other
        else: raise NotImplementedError

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Figure):
            return self.coordinates < other.coordinates
        elif isinstance(other, tuple):
            return self.coordinates < other
        else: raise NotImplementedError

    def __iter__(self):
        return iter(self.coordinates)

    def __str__(self):
        return str(self.coordinates)

    def __repr__(self):
        return str(self)


Shape: typing.TypeAlias = tuple[Coordinate, ...]


DIRECTIONS = [
    (0, 1),
    (0, -1),
    (1, 0),
    (-1, 0),
]
        

def is_within_bounds(x: int, y: int, dimensions: tuple[int, int]) -> bool:
    """Checks if coordinates are within bounds of the board.

    Args:
        x: coordinate row.
        y: coordinate column.
        dimensions: board dimensions.

    Returns:
        returns if the coordinate is within the bounds.
    """
    return x >= 0 and y >= 0 and x < dimensions[0] and y < dimensions[1]


def get_shape(
    board: Board, i: int, j: int, Colors: Colors, visited: Matrix[bool]
) -> Shape:
    """Runs BFS over coordinate in board and returns the shape found.

    Args:
        board: Board to apply bfs.
        i: coordinate row.
        j: coordinate column.
        Colors: Colors that the figure should have.
        visited: matrix to know if cell has already been visited and marked if not.

    Returns:
        Shape found as a list of coordinates or None if nothing is found.
    """
    queue = [Coordinate(i, j)]
    found_coordinates = []

    while len(queue) != 0:
        coordinate = queue.pop()
        for dx, dy in DIRECTIONS:
            nx, ny = coordinate.x + dx, coordinate.y + dy

            if not is_within_bounds(nx, ny, board.shape):
                continue

            n_Colors = board[nx][ny]
            if visited[nx][ny] or n_Colors != Colors:
                continue

            visited[nx][ny] = True
            new_coordinate = Coordinate(nx, ny)
            queue.append(new_coordinate)
            found_coordinates.append(new_coordinate)

    return found_coordinates


def get_all_board_shapes(board: Board) -> typing.Iterator[Shape]:
    """Yields each shape (adjacent tiles of the same Colors) as it finds them.

    Args:
        board: the board to walk through.

    Yields:
        shape formed from adjacent tiles of the same Colors.
    """
    visited = [[False for _ in range(board.shape[1])]
               for _ in range(board.shape[0])]
    for i in range(board.shape[0]):
        for j in range(board.shape[1]):
            Colors = board[i][j]
            shape = get_shape(board, i, j, Colors, visited)

            if shape:
                yield shape


def translate_shape_to_bottom_left(
    shape: Shape, board_dimensions: tuple[int, int]
) -> Shape:
    """Aligns the shape coordinates to the bottom left of a board

    Args:
        shape: shape to translate.
        board_dimensions: dimensions of the board.
    Returns:
        translated shape.
    """
    min_left = min(coordinate.y for coordinate in shape)
    max_bottom = max(coordinate.x for coordinate in shape)
    move_bottom = board_dimensions[1] - max_bottom

    new_shape = [
        Coordinate(coordinate.x + move_bottom - 1, coordinate.y - min_left)
        for coordinate in shape
    ]

    return new_shape


def rotate_90_degrees(figure: Figure, board_dimensions: tuple[int,int]) -> Figure:
    """Rotates the figure 90 degrees clockwise.
    
    Args:
        figure: Figure to rotate
        board_dimensions: dimensions of the board.

    Return:
        Rotated figure
    """
    new_figure = Figure(map(lambda coordinates: Coordinate(coordinates.y, board_dimensions[0] - 1 - coordinates.x), figure))
    
    return Figure(tuple(translate_shape_to_bottom_left(new_figure, board_dimensions)))

def rotate_180_degrees(figure: Figure, board_dimensions: tuple[int,int]) -> Figure:
    """Rotates the figure 180 degrees.
    
    Args:
        figure: Figure to rotate
        board_dimensions: dimensions of the board.

    Return:
        Rotated figure
    """
    new_figure = Figure(map(lambda coordinates: Coordinate(board_dimensions[0] - 1 - coordinates.x, board_dimensions[1] - 1 - coordinates.y), figure))
    
    return Figure(tuple(translate_shape_to_bottom_left(new_figure, board_dimensions)))

    #return rotate_90_degrees(rotate_90_degrees(figure, board_dimensions), board_dimensions)

def rotate_270_degrees(figure: Figure, board_dimensions: tuple[int,int]) -> Figure:
    """Rotates the figure 270 degrees clockwise (i.e. 90 degrees counter-clockwise).
    
    Args:
        figure: Figure to rotate
        board_dimensions: dimensions of the board.

    Return:
        Rotated figure
    """
    new_figure = Figure(map(lambda coordinates: Coordinate(board_dimensions[0] - 1 - coordinates.y, coordinates.x), figure))
    
    return Figure(tuple(translate_shape_to_bottom_left(new_figure, board_dimensions)))

    #return rotate_90_degrees(rotate_90_degrees(rotate_90_degrees(figure, board_dimensions), board_dimensions), board_dimensions)

def find_board_figures(
    board: Board, figures_to_find: frozenset[Figure]
) -> list[Figure]:
    """Finds all figure boards.

    Args:
        board: Board where to look for figures.
        figures_to_find: All the figures we should look for in the board. These figures
            should be positioned at the bottom left of the dimensions of the board.

    Return:
        List of figures found.
    """
    figures_found = []
    for shape in get_all_board_shapes(board):
        translated_shape = translate_shape_to_bottom_left(shape, board.shape)
        shape_figure = Figure(tuple(translated_shape))

        if shape_figure in figures_to_find:
            figures_found.append(sorted(shape))

    return figures_found
