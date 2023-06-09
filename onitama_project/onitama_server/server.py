import random
import sys
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from onitama_engine import Color, Onitama

app = FastAPI()


GameID = UUID
PlayerID = UUID
WebSocketID = UUID


class Player(BaseModel):
    id: UUID
    color: Color


class GameWrapper:
    def __init__(self, onitama_game: Onitama):
        self.game: Onitama = onitama_game
        self.players: Dict[PlayerID, Player] = {}
        self.host: Optional[PlayerID] = None
        self.available_colors: List[Color] = list(Color)
        self.current_player: Optional[PlayerID] = None
        self.started: bool = False

    def add_player(self, player: Player):
        self.players[player.id] = player
        self.available_colors.remove(player.color)

        if self.num_players == 1:
            self.host = player.id

    def assign_random_color(self) -> Color:
        return random.choice(self.available_colors)

    def start(self):
        self.current_player = random.choice(list(self.players.keys()))
        self.started = True

    @property
    def is_full(self):
        return self.num_players >= 2

    @property
    def num_players(self):
        return len(self.players)


class GameManager:
    def __init__(self):
        self.games: Dict[GameID, GameWrapper] = {}

    def create_game(self) -> GameID:
        game_id = uuid4()
        game = Onitama()
        game_wrapper = GameWrapper(game)
        self.games[game_id] = game_wrapper
        return game_id

    def join_game(self, game_id: GameID) -> Player:
        game_wrapper = self.games.get(game_id)
        if not game_wrapper:
            raise HTTPException(status_code=404, detail="Game not found")

        if game_wrapper.is_full:
            raise HTTPException(status_code=400, detail="Game is already full")

        player = Player(id=uuid4(), color=game_wrapper.assign_random_color())
        game_wrapper.add_player(player)

        return player

    def get_game(self, game_id: GameID) -> Onitama:
        game_wrapper = self.games.get(game_id)
        if not game_wrapper:
            raise HTTPException(status_code=404, detail="Game not found")

        return game_wrapper.game

    def remove_game(self, game_id: GameID):
        if game_id in self.games:
            del self.games[game_id]


game_manager = GameManager()


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[WebSocketID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: WebSocketID):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, game_id: WebSocketID):
        self.active_connections[game_id].remove(websocket)

    async def broadcast_game_state(self, game_id: WebSocketID, game_state: dict):
        if game_id in self.active_connections:
            for websocket in self.active_connections[game_id]:
                await websocket.send_json(game_state)


websocket_manager = WebSocketManager()


@app.post("/create_game")
def create_game():
    game_id = game_manager.create_game()
    player = game_manager.join_game(game_id)

    return {"game_id": game_id, "player": player}


@app.post("/join_game/{game_id}")
def join_game(game_id: GameID):
    player = game_manager.join_game(game_id)

    return {"game_id": game_id, "player": player}


@app.get("/game_state/{game_id}")
def game_state(game_id: GameID):
    game = game_manager.get_game(game_id)

    return game.get_game_state()


@app.post("/start_game/{game_id}")
async def start_game(game_id: GameID, player_id: PlayerID):
    game_wrapper = game_manager.games.get(game_id)
    if not game_wrapper:
        raise HTTPException(status_code=404, detail="Game not found")

    if not game_wrapper.is_full:
        raise HTTPException(
            status_code=400, detail="Two players are required to start the game"
        )

    if player_id != game_wrapper.host:
        raise HTTPException(
            status_code=403, detail="You are not allowed to start the game."
        )

    game_wrapper.start()

    start_message = {
        "type": "game_started",
        "status": "game_started",
        "message": "The game has started",
        "current_player": game_wrapper.current_player,
    }

    await websocket_manager.broadcast_game_state(game_id, start_message)

    return {"status": "success", "message": "The game has been started"}


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: GameID):
    game_wrapper = game_manager.get_game(game_id)
    game = game_wrapper.game
    if not game:
        return

    await websocket_manager.connect(websocket, game_id)

    try:
        while True:
            ws_msg = await websocket.receive_json()
            move_input = ws_msg["move_input"]
            player_id = UUID(ws_msg["player_id"])

            if player_id != game_wrapper.current_player:
                await websocket.send_json(
                    {
                        "type": "error",
                        "status": "error",
                        "message": "It's not your turn.",
                    }
                )
                continue

            valid_move, msg = game.validate_input(
                move_input["card_name"],
                move_input["x"],
                move_input["y"],
                move_input["nx"],
                move_input["ny"],
            )

            if not valid_move:
                await websocket.send_json(
                    {"type": "error", "status": "error", "message": msg}
                )
            else:
                winner = game.make_move(
                    move_input["card_name"],
                    move_input["x"],
                    move_input["y"],
                    move_input["nx"],
                    move_input["ny"],
                )

                updated_game_state = game.get_game_state()
                updated_game_state["type"] = "game_state_updated"
                updated_game_state["status"] = "success"
                updated_game_state["winner"] = winner

                await websocket_manager.broadcast_game_state(
                    game_id, updated_game_state
                )

                if winner is not None:
                    break

    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket, game_id)
    finally:
        # Clean up the game state and active connections when the game finishes
        game_manager.remove_game(game_id)
        if game_id in websocket_manager.active_connections:
            del websocket_manager.active_connections[game_id]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
