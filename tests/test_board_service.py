from itertools import cycle
from random import seed, shuffle
from unittest import mock


from app.cruds.board import BoardService
from app.models.enums import Colors
from app.models.models import Boards, Tiles


@mock.patch(
    "app.cruds.board.TileService.create_tile", return_value=None
)
def test_init_board(mock_create_tile: mock.Mock):

    db = mock.Mock()
    db.commit = mock.Mock()
    board_id = 5

    colors = [color.value for color in Colors] * 9

    seed(99) 
    shuffle(colors)

    color_iter = iter(colors)

    expected_calls = [
        (board_id, next(color_iter), i, j)
        for i in range(6)
        for j in range(6)
    ]

    board_service = BoardService(db)
    seed(99)
    board_service.init_board(board_id)

    assert mock_create_tile.call_count == len(expected_calls)

    for call in expected_calls:
        mock_create_tile.assert_any_call(*call)

    db.commit.assert_called_once()


def test_board_table_property(db):

    board = Boards(match_id=1)
    db.add(board)
    db.commit()

    colors = [color.value for color in Colors]

    colors_iter = iter(cycle(colors))

    for i in range(6):
        for j in range(6):
            tile = Tiles(
                board_id=board.id, color=next(colors_iter), position_x=i, position_y=j
            )
            db.add(tile)

    db.commit()

    expected_table = [[next(colors_iter) for _ in range(6)] for _ in range(6)]

    board_service = BoardService(db)
    board_table = board_service.get_board_table(board.id)
    
    assert board_table == expected_table
