class SwitcherException(Exception):
    pass


class GameConnectionDoesNotExist(SwitcherException):
    def __init__(self, id: int):
        message: str = f"Game {id} doesn't have an open connection"
        super().__init__(message)


class PlayerAlreadyConnected(SwitcherException):
    def __init__(self, game_id: int, player_id: int):
        message: str = f"player {player_id} already connected to game {game_id}"
        super().__init__(message)


class PlayerNotConnected(SwitcherException):
    def __init__(self, game_id: int, player_id: int):
        message: str = f"Player {player_id} from game {game_id} not connected to the game"
        super().__init__(message)