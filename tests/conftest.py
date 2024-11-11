import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from unittest.mock import patch

from app.connection_manager import ConnectionManager
from app.cruds.board import BoardService
from app.cruds.match import MatchService
from app.cruds.movement_card import MovementCardService
from app.cruds.player import PlayerService
from app.cruds.shape_card import ShapeCardService
from app.cruds.tile import TileService
from app.models.enums import *

import os

from app.models.models import Base
from app.database import Base, get_db
from app.models.models import *
from app.routers import matches, players


@pytest.fixture
def db_session():
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URL = "sqlite:///tests/test_db.sqlite"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine, checkfirst=True)
    init_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = init_session()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)
    os.remove(basedir + "/test_db.sqlite")


@pytest.fixture
def app(db_session):
    os.environ["TURN_TIMER"] = "1"

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app = FastAPI()

    origins = ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(matches.router)
    app.include_router(players.router)
    app.dependency_overrides[get_db] = override_get_db

    yield app

    app.dependency_overrides.clear()


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def match_service(db_session):
    return MatchService(db_session)


@pytest.fixture
def player_service(db_session):
    return PlayerService(db_session)


@pytest.fixture
def shape_service(db_session):
    return ShapeCardService(db_session)


@pytest.fixture
def movement_card_service(db_session):
    return MovementCardService(db_session)


@pytest.fixture
def board_service(db_session):
    return BoardService(db_session)


@pytest.fixture
def tile_service(db_session):
    return TileService(db_session)

@pytest.fixture
def player():
    return Players(id=1, player_name="Player 1", match_id=1, turn_order=1, is_owner=True)

@pytest.fixture
def match():
    return Matches(id=1, state="STARTED", current_players=2, current_player_turn=1)

@pytest.fixture()
def load_matches(db_session):
    list_matches = [
        Matches(match_name="Match 1", max_players=2, is_public=True, state="WAITING", current_players=2, players=[
                Players(player_name="Player 1", is_owner=True, match_id=1, session_token=""), Players(player_name="Player 2", is_owner=False, match_id=1, session_token="")
            ]),
        Matches(match_name="Match 2", max_players=2, is_public=True, state="STARTED", current_players=2),
        Matches(match_name="Match 3", max_players=4, is_public=True, state="WAITING", current_players=1, players=[
                Players(player_name="Player 3", is_owner=True, match_id=3, session_token="")
            ])
    ]
    
    db_session.add_all(list_matches)
    db_session.commit()


@pytest.fixture()
def load_data_for_test(db_session):
    list_matches = [
        {'name': 'Match 1', 'max_players': 4, 'public': True},
        {'name': 'Match 2', 'max_players': 3, 'public': False},
        {'name': 'Match 3', 'max_players': 2, 'public': True}
    ]
    list_players = [
        {'name': 'Player 1', 'match_to_link': 1,
            'owner': True, 'token': 'token1', 'turn_order': 2},
        {'name': 'Player 2', 'match_to_link': 1,
            'owner': False, 'token': 'token2', 'turn_order': 1},
        {'name': 'Player 3', 'match_to_link': 2, 'owner': True,
            'token': 'token3', 'turn_order': 1},
        {'name': 'Player 4', 'match_to_link': 2, 'owner': False,
            'token': 'token4', 'turn_order': 2},
        {'name': 'Player 5', 'match_to_link': 3, 'owner': False,
            'token': 'token5', 'turn_order': 3},
        {'name': 'Player 6', 'match_to_link': 3, 'owner': True,
            'token': 'token6', 'turn_order': 1}]
    list_boards = [
        {'match_id': 1, 'ban_color': 'red',
            'curren_player_turn': 1, 'next_player_turn': 2},
        {'match_id': 2, 'ban_color': 'green',
            'curren_player_turn': 3, 'next_player_turn': 4},
        {'match_id': 3, 'ban_color': 'yellow',
            'curren_player_turn': 3, 'next_player_turn': 4},
    ]
    list_tiles = [
        {'board_id': 1, 'color': 'red', 'positionX': 1, 'positionY': 1},
        {'board_id': 1, 'color': 'green', 'positionX': 2, 'positionY': 1},
        {'board_id': 2, 'color': 'blue', 'positionX': 1, 'positionY': 1},
        {'board_id': 3, 'color': 'yellow', 'positionX': 1, 'positionY': 1},
    ]
    list_shape_cards = [
        {'player_owner': 1, 'shape_type': 1, 'is_hard': True,
            'is_visible': False, 'is_blocked': "NOT_BLOCKED"},
        {'player_owner': 1, 'shape_type': 2, 'is_hard': True,
            'is_visible': False, 'is_blocked': "NOT_BLOCKED"},
        {'player_owner': 2, 'shape_type': 3, 'is_hard': True,
            'is_visible': False, 'is_blocked': "NOT_BLOCKED"},
        {'player_owner': 2, 'shape_type': 2, 'is_hard': True,
            'is_visible': False, 'is_blocked': "NOT_BLOCKED"},
        {'player_owner': 3, 'shape_type': 2, 'is_hard': True,
            'is_visible': False, 'is_blocked': "NOT_BLOCKED"},
        {'player_owner': 4, 'shape_type': 6, 'is_hard': True,
            'is_visible': False, 'is_blocked': "NOT_BLOCKED"},
        {'player_owner': 5, 'shape_type': 6, 'is_hard': True,
            'is_visible': False, 'is_blocked': "NOT_BLOCKED"},
        {'player_owner': 6, 'shape_type': 4, 'is_hard': True,
            'is_visible': False, 'is_blocked': "NOT_BLOCKED"},
    ]
    list_movement_cards = [
        {'matchId': 1, 'player_owner': 1, 'movement': 'Inverse L'},
        {'matchId': 1, 'player_owner': 1, 'movement': 'Line Between'},
        {'matchId': 1, 'player_owner': 2, 'movement': 'Line Border'},
        {'matchId': 2, 'player_owner': 3, 'movement': 'L'},
        {'matchId': 2, 'player_owner': 4, 'movement': 'Diagonal'},
        {'matchId': 3, 'player_owner': 5, 'movement': 'Inverse Diagonal'},
        {'matchId': 3, 'player_owner': 5, 'movement': 'L'},
        {'matchId': 3, 'player_owner': 6, 'movement': 'Line'},
    ]

    session = db_session
    try:
        for match in list_matches:
            new_match = Matches(match_name=match['name'], max_players=match['max_players'],
                                is_public=match['public'], state="WAITING", current_players=2)
            session.add(new_match)
            session.commit()
        for player in list_players:
            new_player = Players(player_name=player['name'], match_id=player['match_to_link'],
                                 is_owner=player['owner'], session_token=player['token'], turn_order=player['turn_order'])
            session.add(new_player)
            session.commit()
        for board in list_boards:
            new_board = Boards(match_id=board['match_id'], ban_color=board['ban_color'])
            session.add(new_board)
            session.commit()
        for tile in list_tiles:
            new_tile = Tiles(board_id=tile['board_id'], color=tile['color'],
                             position_x=tile['positionX'], position_y=tile['positionY'])
            session.add(new_tile)
            session.commit()
        for shape_card in list_shape_cards:
            new_shape_card = ShapeCards(player_owner=shape_card['player_owner'], shape_type=shape_card['shape_type'],
                                        is_hard=shape_card['is_hard'], is_visible=shape_card['is_visible'],
                                        is_blocked=shape_card['is_blocked'])
            session.add(new_shape_card)
            session.commit()
        for movement_card in list_movement_cards:
            new_movement_card = MovementCards(
                player_owner=movement_card['player_owner'], mov_type=movement_card['movement'], match_id=movement_card['matchId'])
            session.add(new_movement_card)
            session.commit()
    finally:
        session.close()
