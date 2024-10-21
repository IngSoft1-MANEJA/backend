import pytest

from app.utils.board_shapes_algorithm import *
from app.utils.utils import FIGURE_COORDINATES

def test_rotate_90_degrees():
    board_dimensions = (6,6)

    figure = FIGURE_COORDINATES["MINI_LINE"]
    rotated_figure = rotate_90_degrees(figure, board_dimensions)
    assert(rotated_figure == Figure((Coordinate(2,0), Coordinate(3,0), Coordinate(4,0), Coordinate(5,0))))

    figure = FIGURE_COORDINATES["T_90"]
    rotated_figure = rotate_90_degrees(figure, board_dimensions)
    assert(rotated_figure == Figure((Coordinate(3,0), Coordinate(3,1), Coordinate(3,2), Coordinate(4,1), Coordinate(5,1))))


def test_rotate_180_degrees():
    board_dimensions = (6,6)

    figure = Figure(tuple(FIGURE_COORDINATES["T_90"]))
    rotated_figure = rotate_180_degrees(figure, board_dimensions)
    assert(rotated_figure == Figure((Coordinate(3,2), Coordinate(4,0), Coordinate(4,1), Coordinate(4,2), Coordinate(5,2))))

def test_rotate_270_degrees():
    board_dimensions = (6,6)

    figure = Figure(tuple(FIGURE_COORDINATES["T_90"]))
    rotated_shape = rotate_270_degrees(figure, board_dimensions)
    assert(rotated_shape == Figure((Coordinate(3,1), Coordinate(4,1), Coordinate(5,0), Coordinate(5,1), Coordinate(5,2))))

def test_rotate_90_degrees():
    board_dimensions = (6,6)

    figure = FIGURE_COORDINATES["MINI_LINE"]
    rotated_figure = rotate_90_degrees(figure, board_dimensions)
    assert(rotated_figure == Figure((Coordinate(2,0), Coordinate(3,0), Coordinate(4,0), Coordinate(5,0))))

    figure = FIGURE_COORDINATES["T_90"]
    rotated_figure = rotate_90_degrees(figure, board_dimensions)
    assert(rotated_figure == Figure((Coordinate(3,0), Coordinate(3,1), Coordinate(3,2), Coordinate(4,1), Coordinate(5,1))))


def test_rotate_180_degrees():
    board_dimensions = (6,6)

    figure = Figure(tuple(FIGURE_COORDINATES["T_90"]))
    rotated_figure = rotate_180_degrees(figure, board_dimensions)
    assert(rotated_figure == Figure((Coordinate(3,2), Coordinate(4,0), Coordinate(4,1), Coordinate(4,2), Coordinate(5,2))))

def test_rotate_270_degrees():
    board_dimensions = (6,6)

    figure = Figure(tuple(FIGURE_COORDINATES["T_90"]))
    rotated_shape = rotate_270_degrees(figure, board_dimensions)
    assert(rotated_shape == Figure((Coordinate(3,1), Coordinate(4,1), Coordinate(5,0), Coordinate(5,1), Coordinate(5,2))))


def test_is_within_bounds():
    dimensions = (5, 5)
    x = 0
    y = 4
    assert (is_within_bounds(x, y, dimensions))

    dimensions = (5, 5)
    x = 5
    y = 7
    assert (not is_within_bounds(x, y, dimensions))

    dimensions = (5, 5)
    x = -3
    y = -1
    assert (not is_within_bounds(x, y, dimensions))


def test_find_board_figures():
    board = Board([
        [Colors.RED, Colors.YELLOW, Colors.RED, Colors.RED],
        [Colors.BLUE, Colors.BLUE, Colors.BLUE, Colors.BLUE],
        [Colors.RED, Colors.GREEN, Colors.RED, Colors.RED],
        [Colors.GREEN, Colors.YELLOW, Colors.RED, Colors.RED]
    ])
    figures_to_find = frozenset([
        Figure((Coordinate(3, 0), Coordinate(3, 1),
               Coordinate(3, 2), Coordinate(3, 3)))
    ])

    board_figures = find_board_figures(board, figures_to_find)
    print(board_figures)
    assert (
        board_figures ==
        [[Coordinate(1, 0), Coordinate(1, 1),
          Coordinate(1, 2), Coordinate(1, 3)]]
    )
