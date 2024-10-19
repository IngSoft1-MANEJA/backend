import pytest

from app.utils.board_shapes_algorithm import *


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
    print([Figure((Coordinate(1, 0), Coordinate(1, 1), Coordinate(1, 2), Coordinate(1, 3)))])
    assert (
        board_figures ==
        [[Coordinate(1, 0), Coordinate(1, 1),
          Coordinate(1, 2), Coordinate(1, 3)]]
    )
