import random
import sys
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from onitama_engine import Color, Onitama

app = FastAPI()


class GameWrapper:
    def __init__(self, onitama_game: Onitama):
        self.game = onitama_game
        self.num_players = 0
        self.player_colors = {}
        self.available_colors = list(Color)

    def add_player(self, player_id: str, color: Color):
        self.player_colors[player_id] = color
        self.available_colors.remove(color)

    def get_player_color(self, player_id: str) -> Color:
        return self.player_colors.get(player_id)

    def assign_random_color(self) -> Color:
        return random.choice(self.available_colors)


class GameManager:
    def __init__(self):
        self.games: Dict[str, GameWrapper] = {}

    def create_game(self) -> str:
        game_id = str(uuid4())
        game = Onitama()
        game_wrapper = GameWrapper(game)
        self.games[game_id] = game_wrapper
        return game_id

    def join_game(self, game_id: str) -> Color:
        game_wrapper = self.games.get(game_id)
        if not game_wrapper:
            raise HTTPException(status_code=404, detail="Game not found")

        if game_wrapper.num_players >= 2:
            raise HTTPException(status_code=400, detail="Game is already full")

        game_wrapper.num_players += 1
        player_color = game_wrapper.assign_random_color()
        game_wrapper.add_player(game_id, player_color)

        return player_color

    def get_game(self, game_id: str) -> Onitama:
        game_wrapper = self.games.get(game_id)
        if not game_wrapper:
            raise HTTPException(status_code=404, detail="Game not found")

        return game_wrapper.game

    def remove_game(self, game_id: str):
        if game_id in self.games:
            del self.games[game_id]


game_manager = GameManager()


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: str):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, game_id: str):
        self.active_connections[game_id].remove(websocket)

    async def broadcast_game_state(self, game_id: str, game_state: dict):
        if game_id in self.active_connections:
            for websocket in self.active_connections[game_id]:
                await websocket.send_json(game_state)


websocket_manager = WebSocketManager()


@app.post("/create_game")
def create_game():
    game_id = game_manager.create_game()
    player_color = game_manager.join_game(game_id)

    return {"game_id": game_id, "color": player_color.name}


@app.post("/join_game/{game_id}")
def join_game(game_id: str):
    player_color = game_manager.join_game(game_id)

    return {"game_id": game_id, "color": player_color.name}


@app.get("/game_state/{game_id}")
def game_state(game_id: str):
    game = game_manager.get_game(game_id)

    return game.get_game_state()


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    game = game_manager.get_game(game_id).game
    if not game:
        return

    await websocket_manager.connect(websocket, game_id)

    try:
        while True:
            move_input = await websocket.receive_json()
            valid_move, msg = game.validate_input(
                move_input["card_name"],
                move_input["x"],
                move_input["y"],
                move_input["nx"],
                move_input["ny"],
            )

            if not valid_move:
                await websocket.send_json({"status": "error", "message": msg})
            else:
                winner = game.make_move(
                    move_input["card_name"],
                    move_input["x"],
                    move_input["y"],
                    move_input["nx"],
                    move_input["ny"],
                )

                updated_game_state = game.get_game_state()
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
