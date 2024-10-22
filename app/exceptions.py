# Description: Exceptions for the Switcher API
# Invalid characters, invalid values, etc:


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


class GameNotCreated(SwitcherException):
    def __init__(self, game_id: int):
        message: str = f"Game {game_id} not created, error creating game"
        super().__init__(message)

# ================== Cruds MatchService Exceptions ==============================


class MatchNameInvalid(SwitcherException):
    def __init__(self, name: str):
        message: str = f"Match name {name} is invalid"
        super().__init__(message)


class MatchMaxPlayersInvalid(SwitcherException):
    def __init__(self, max_players: int):
        message: str = f"Match max players {max_players} is invalid. Must be a number between 2 and 4"
        super().__init__(message)


class MatchNotCreated(SwitcherException):
    def __init__(self, name: str):
        message: str = f"Match {name} not created, error creating match"
        super().__init__(message)


class MatchNotFound(SwitcherException):
    def __init__(self, match_id: int):
        message: str = f"Match with id {match_id} not found, can't get"
        super().__init__(message)


class NoMatchesFound(SwitcherException):
    def __init__(self):
        message: str = "No matches found"
        super().__init__(message)


class MatchCannotBeUpdated(SwitcherException):
    def __init__(self, match_id: int):
        message: str = f"Match with id {match_id} cannot be updated"
        super().__init__(message)


class MatchAlreadyStarted(SwitcherException):
    def __init__(self, match_id: int):
        message: str = f"Match with id {match_id} already started"
        super().__init__(message)

# ====================== Cruds PlayerService Exceptions ==========================


class PlayerNameInvalid(SwitcherException):
    def __init__(self, name: str):
        message: str = f"Player name {name} is invalid"
        super().__init__(message)


class PlayerNotInMatch(SwitcherException):
    def __init__(self, player_id: int, match_id: int):
        message: str = f"Player {player_id} not in match with id: {match_id}"
        super().__init__(message)


class PlayerNotCreated(SwitcherException):
    def __init__(self, name: str):
        message: str = f"Player {name} not created, error creating player"
        super().__init__(message)


class PlayerNotFound(SwitcherException):
    def __init__(self, player_id: int):
        message: str = f"Player with id {player_id} not found, can't get"
        super().__init__(message)


class NoPlayersFound(SwitcherException):
    def __init__(self):
        message: str = "No players found"
        super().__init__(message)


class PlayerCannotBeUpdated(SwitcherException):
    def __init__(self, player_id: int):
        message: str = f"Player with id {player_id} cannot be updated"
        super().__init__(message)


class PlayerAlreadyInMatch(SwitcherException):
    def __init__(self, player_id: int, match_id: int):
        message: str = f"Player {player_id} already in match with id: {match_id}"
        super().__init__(message)


class PlayerNotHaveCards(SwitcherException):
    def __init__(self, player_id: int):
        message: str = f"Player {player_id} does not have cards"
        super().__init__(message)


class PlayerAreAlreadyBlocked(SwitcherException):
    def __init__(self, player_id: int):
        message: str = f"Player {player_id} are already blocked"
        super().__init__(message)

# ====================== Cruds CardService Exceptions ==========================


class CardNotCreated(SwitcherException):
    def __init__(self, name: str):
        message: str = f"Card {name} not created, error creating card"
        super().__init__(message)


class CardNotFound(SwitcherException):
    def __init__(self, card_id: int):
        message: str = f"Card with id {card_id} not found, can't get"
        super().__init__(message)


class NoCardsFound(SwitcherException):
    def __init__(self):
        message: str = "No cards found"
        super().__init__(message)


class CardCannotBeUpdated(SwitcherException):
    def __init__(self, card_id: int):
        message: str = f"Card with id {card_id} cannot be updated"
        super().__init__(message)


class CardAlreadyInPlayer(SwitcherException):
    def __init__(self, card_id: int, player_id: int):
        message: str = f"Card {card_id} already in player with id: {player_id}"
        super().__init__(message)


class CardNotInPlayer(SwitcherException):
    def __init__(self, card_id: int, player_id: int):
        message: str = f"Card {card_id} not in player with id: {player_id}"
        super().__init__(message)


class CardNotInMatch(SwitcherException):
    def __init__(self, card_id: int, match_id: int):
        message: str = f"Card {card_id} not in match with id: {match_id}"
        super().__init__(message)


class ShapeNotValid(SwitcherException):
    def __init__(self, shape: str):
        message: str = f"Shape {shape} is not valid"
        super().__init__(message)


class ColorNotValid(SwitcherException):
    def __init__(self, color: str):
        message: str = f"Color {color} is not valid"
        super().__init__(message)


class ShapeCardAreAlreadyBlocked(SwitcherException):
    def __init__(self, shape: str, card_id: int):
        message: str = f"The Shape Card {shape} whit ID: {card_id} are already blocked"
        super().__init__(message)

# ================== Cruds BoardService Exceptions ==============================


class BoardNotCreated(SwitcherException):
    def init(self, name: str):
        message: str = f"Board {name} not created, error creating board"
        super().init(message)


class BoardNotFound(SwitcherException):
    def init(self, board_id: int):
        message: str = f"Board with id {board_id} not found, can't get"
        super().init(message)


class TurnsAreEqual(SwitcherException):
    def init(self, board_id: int):
        message: str = f"Board with id {board_id} cannot be updated, current player and next player turn are equal"
        super().init(message)

# ========================= Cruds TileService Exceptions ========================


class TileNotFound(SwitcherException):
    def __init__(self, tile_id: int):
        message: str = f"Tile with id {tile_id} not found, can't get"
        super().__init__(message)


class NoTilesFound(SwitcherException):
    def __init__(self):
        message: str = "No tiles found"
        super().__init__(message)


class TileCannotBeUpdated(SwitcherException):
    def __init__(self, tile_id: int):
        message: str = f"Tile with id {tile_id} cannot be updated"
        super().__init__(message)


class TilePositionIsInvalid(SwitcherException):
    def __init__(self, positionX: int, positionY: int):
        message: str = f"Tile position ({positionX}, {positionY}) is invalid"
        super().__init__(message)


class ShapeCardHandIsFull(SwitcherException):
    def __init__(self, player_id: int):
        message: str = f"Player with id: {player_id} hand is full, can't add more shape cards"
        super().__init__(message)

# ========================= Cruds MovementCardService Exceptions ========================


class MoveNotValid(SwitcherException):
    def __init__(self, movement: str):
        message: str = f"Movement {movement} is not valid"
        super().__init__(message)


class MovementCardNotFound(SwitcherException):
    def __init__(self, movement_card_id: int):
        message: str = f"Movement card with id {movement_card_id} not found, can't get"
        super().__init__(message)


class NoMovementCardsFound(SwitcherException):
    def __init__(self, player_owner: int):
        message: str = f"No movement cards found with player id {player_owner}"
        super().__init__(message)
