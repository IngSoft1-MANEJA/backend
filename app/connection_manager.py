from fastapi import WebSocket, WebSocketDisconnect, WebSocketException
from typing import Any, Dict 

from app.exceptions import *

class ConnectionManager:
    def __init__(self) -> None:
        self._games: Dict[int, Dict[int, WebSocket]] = {}
    
    def create_game_connection(self, game_id):
        """Creates a new game entry for future connections.

        Args:
            game_id: game's id to create.
        """
        self._games[game_id] = {}

    @staticmethod
    async def keep_alive(websocket: WebSocket):
        """Keeps websocket connections alive

        Args:
            websocket: connection to keep alive.
        """

        while True:
            await websocket.receive_text()

    def connect_player_to_game(self, game_id: int, player_id: int, websocket: WebSocket):
        """Connects players to game and saves the connections.

        Args:
            game_id: id of the game to join.
            player_id: id of the player who wants to join.
            websocket: websocket connection to save.
        """
        if game_id not in self._games:
            raise GameConnectionDoesNotExist(game_id)

        if player_id in self._games[game_id]:
            raise PlayerAlreadyConnected(game_id, player_id)

        self._games[game_id][player_id] = websocket

    def disconnect_player_from_game(self, game_id: int, player_id: int):
        """Removes a player connection from game and the game's entry if no player left.

        Args:
            game_id: id of the game to disconnect from.
            player_id: id of the player who wants to disconnect.
            websocket: websocket connection to remove.
        """
        if game_id not in self._games:
            raise GameConnectionDoesNotExist(game_id)

        if player_id not in self._games[game_id]:
            raise PlayerNotConnected(game_id, player_id)

        del self._games[game_id][player_id]

        if len(self._games[game_id].keys()) == 0:
            del self._games[game_id]

    async def broadcast_to_game(self, game_id: int, msg: Any):
        """Sends message to all players in a game.

        Args:
            game_id: id of the game.
            msg: message to send.
        """

        if game_id not in self._games:
            raise GameConnectionDoesNotExist(game_id)

        for conn in self._games[game_id].values():
            await conn.send_json(msg)

    async def send_to_player(self, game_id: int, player_id: int, msg: Any):
        """Sends message to a specific player in a game.

        Args:
            game_id: id of the game.
            msg: message to send.
        """

        if game_id not in self._games:
            raise GameConnectionDoesNotExist(game_id)

        if player_id not in self._games[game_id]:
            raise PlayerNotConnected(game_id, player_id)

        conn: WebSocket = self._games[game_id][player_id]
        await conn.send_json(msg)
        

manager = ConnectionManager()
