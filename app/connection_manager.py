from fastapi import WebSocket, WebSocketDisconnect, WebSocketException
from typing import Any, Callable, Dict, List, Union

from app.exceptions import *
from app.schemas import MatchOut

import asyncio
from app.logger import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self) -> None:
        self._games: Dict[int, Dict[int, WebSocket]] = {}
        self._connections: List[Dict[str, Union[str, int, WebSocket]]] = []

    def add_anonymous_connection(self, websocket: WebSocket):
        """Add anonymous websocket to connections
        
        Args:
            websocket: connection to add.
        """
        self._connections.append({"match_name": None, "max_players": None, "websocket": websocket})
        return len(self._connections) - 1
    
    def remove_anonymous_connection(self, websocket: WebSocket):
        """Remove anonymous websocket from connections'
        
        Args:
            websocket: connection to remove.
        """
        try:
            conn_to_delete = None
            for i, conn in enumerate(self._connections):
                if conn["websocket"] == websocket:
                    conn_to_delete = i
                    break
            if conn_to_delete == None:
                raise ValueError("Connection not found")
            
            del self._connections[conn_to_delete]
        except ValueError:
            pass


    def create_game_connection(self, game_id):
        """Creates a new game entry for future connections.

        Args:
            game_id: game's id to create.
        """
        self._games[game_id] = {}


    async def broadcast(self, msg):
        for websocket in self._connections:
            await websocket.send_json(msg)


    @staticmethod
    async def keep_alive(websocket: WebSocket):
        """Keeps websocket connections alive

        Args:
            websocket: connection to keep alive.
        """

        while True:
            await websocket.receive_text()
    
    async def receive_and_broadcast_message(self, websocket: WebSocket, game_id: int):
        """Keeps websocket connections alive.
        When receive a message, broadcast it to the match

        Args:
            websocket: connection to keep alive.
            game_id: id of the game
        """
        msg = await websocket.receive_json()
        await self.broadcast_to_game(game_id, msg)


    async def keep_alive_matches(self, index, on_filter_matches):
        """
        Mantiene viva la conexión del websocket y filtra las partidas.
        Args:
            index: índice de la conexión a mantener viva.
            on_filter_matches: función para filtrar las partidas.
        """
        while True:
            try:
                response = await self._connections[index]["websocket"].receive_json()
            except IndexError:
                # La conexión ya no existe, salir del bucle
                break

            if response["key"] == "FILTER_MATCHES":
                if "match_name" in response["payload"]:
                    self._connections[index]["match_name"] = response["payload"]["match_name"]
                if "max_players" in response["payload"]:
                    self._connections[index]["max_players"] = response["payload"]["max_players"]

                filtered_matches = on_filter_matches(self._connections[index]["match_name"], 
                                                    self._connections[index]["max_players"])
                matches = [MatchOut.model_validate(match).model_dump() 
                        for match in filtered_matches]
                msg = {"key": "MATCHES_LIST", "payload": {"matches": matches}}
                await self._connections[index]["websocket"].send_json(msg)


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