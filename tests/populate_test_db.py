from sqlalchemy.orm import sessionmaker
from app.database import engine, init_db
from app.models.models import Matches, Players, Boards, Tiles, ShapeCards, MovementCards


# Configuración de la sesión
Session = sessionmaker(bind=engine)

def load_data_for_test():
    #============================= List of matches =============================
    list_matches = [
        {'name': 'Match 1', 'max_players': 4, 'public': True},
        {'name': 'Match 2', 'max_players': 3, 'public': False},
        {'name': 'Match 3', 'max_players': 2, 'public': True}
    ]
    # ============================= List of players =============================
    list_players = [
        {'name': 'Player 1', 'match_to_link': 1,
            'owner': True, 'token': 'token1', 'turn_order': 2},
        {'name': 'Player 2', 'match_to_link': 1,
            'owner': False, 'token':'token2', 'turn_order': 1},
        {'name': 'Player 3', 'match_to_link': 2, 'owner': True,
            'token': 'token3', 'turn_order': 1},
        {'name': 'Player 4', 'match_to_link': 2, 'owner': False,
            'token': 'token4', 'turn_order': 2},
        {'name': 'Player 5', 'match_to_link': 3, 'owner': False,
            'token': 'token5', 'turn_order': 3},
        {'name': 'Player 6', 'match_to_link': 3, 'owner': True,
            'token': 'token6', 'turn_order': 1}]
    # ============================= List of boards =============================
    list_boards = [
        {'match_id': 1, 'ban_color': 'red', 'curren_player_turn': 1, 'next_player_turn': 2},
        {'match_id': 2, 'ban_color': 'green', 'curren_player_turn': 3, 'next_player_turn': 4},
        {'match_id': 3, 'ban_color': 'yellow', 'curren_player_turn': 3, 'next_player_turn': 4},
    ]
    # ============================= List of tiles =============================
    list_tiles = [
        {'board_id': 1, 'color': 'red', 'positionX': 1, 'positionY': 1},
        {'board_id': 1, 'color': 'green', 'positionX': 2, 'positionY': 1},
        {'board_id': 2, 'color': 'blue', 'positionX': 1, 'positionY': 1},
        {'board_id': 3, 'color': 'yellow', 'positionX': 1, 'positionY': 1},  
    ]
    
    # ============================= List of shape cards =============================
    list_shape_cards = [
        {'player_owner': 1, 'shape_type': 1, 'is_hard': True, 'is_visible': False, 'is_blocked': False},
        {'player_owner': 1, 'shape_type': 2, 'is_hard': True, 'is_visible': False, 'is_blocked': False},
        {'player_owner': 2, 'shape_type': 3, 'is_hard': True, 'is_visible': False, 'is_blocked': False},
        {'player_owner': 2, 'shape_type': 2, 'is_hard': True, 'is_visible': False, 'is_blocked': False},
        {'player_owner': 3, 'shape_type': 2, 'is_hard': True, 'is_visible': False, 'is_blocked': False},
        {'player_owner': 4, 'shape_type': 6, 'is_hard': True, 'is_visible': False, 'is_blocked': False},
        {'player_owner': 5, 'shape_type': 6, 'is_hard': True, 'is_visible': False, 'is_blocked': False},
        {'player_owner': 6, 'shape_type': 4, 'is_hard': True, 'is_visible': False, 'is_blocked': False},
    ]
    # ============================= List of movement cards =============================
    list_movement_cards = [
        {'player_owner': 1, 'movement': 'Inverse L'},
        {'player_owner': 1, 'movement': 'Line Between'},
        {'player_owner': 2, 'movement': 'Line Border'},
        {'player_owner': 3, 'movement': 'L'},
        {'player_owner': 4, 'movement': 'Diagonal'},
        {'player_owner': 5, 'movement': 'Inverse Diagonal'},
        {'player_owner': 5, 'movement': 'L'},
        {'player_owner': 6, 'movement': 'Line'},
    ]
    # ============================= Load data in the database =============================
    session = Session()
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
            new_board = Boards(match_id=board['match_id'], ban_color=board['ban_color'],
                                current_player_turn=board['curren_player_turn'], next_player_turn=board['next_player_turn'])
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
            new_movement_card = MovementCards(player_owner=movement_card['player_owner'], mov_type=movement_card['movement'])
            session.add(new_movement_card)
            session.commit()
    finally:
        session.close()
        
if __name__ == '__main__':
    load_data_for_test()