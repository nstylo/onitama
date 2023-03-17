import random
from typing import List, Optional, Tuple

from card import Card
from constants import Color
from piece import Piece, Rank
from player import Player


class Onitama:
    def __init__(self):
        self.board = [[None] * 5 for _ in range(5)]
        self.cards = self.generate_cards()
        self.current_cards = random.sample(self.cards, 5)
        self.red_cards = self.current_cards[:2]
        self.blue_cards = self.current_cards[2:4]
        self.neutral_card = self.current_cards[4]

        self.red_player = Player(Color.RED)
        self.blue_player = Player(Color.BLUE)

        starting_player_color = Color.RED if random.random() < 0.5 else Color.BLUE
        self.current_player = (
            self.red_player if starting_player_color == Color.RED else self.blue_player
        )

        self.setup_board()

    def generate_cards(self) -> List[Card]:
        card_tuples = [
            ("Tiger", [(0, -2), (0, 1)]),
            ("Dragon", [(-2, -1), (-1, 1), (2, -1), (1, 1)]),
            ("Frog", [(-2, 0), (-1, -1), (1, 1)]),
            ("Rabbit", [(1, -1), (2, 0), (-1, 1)]),
            ("Crab", [(0, -1), (-2, 0), (2, 0)]),
            ("Elephant", [(1, 0), (-1, -1), (1, -1), (-1, 0)]),
            ("Goose", [(-1, 0), (-1, -1), (1, 0), (1, 1)]),
            ("Rooster", [(1, 0), (1, -1), (-1, 0), (-1, 1)]),
            ("Monkey", [(-1, -1), (1, -1), (-1, 1), (1, 1)]),
            ("Mantis", [(-1, -1), (1, -1), (0, 1)]),
            ("Horse", [(0, -1), (-1, 0), (0, 1)]),
            ("Ox", [(0, -1), (1, 0), (0, 1)]),
            ("Crane", [(0, -1), (1, 1), (-1, 1)]),
            ("Boar", [(0, -1), (1, 0), (-1, 0)]),
            ("Eel", [(1, 0), (-1, -1), (-1, 1)]),
            ("Cobra", [(-1, 0), (1, -1), (1, 1)]),
        ]
        return [Card.from_tuple(card_tuple) for card_tuple in card_tuples]

    def setup_board(self):
        for i in range(5):
            if i == 2:
                self.board[0][i] = Piece(Color.RED, Rank.MASTER, i, 0)
                self.board[4][i] = Piece(Color.BLUE, Rank.MASTER, i, 4)
            else:
                self.board[0][i] = Piece(Color.RED, Rank.STUDENT, i, 0)
                self.board[4][i] = Piece(Color.BLUE, Rank.STUDENT, i, 4)

    def display_board(self):
        print("  0  1  2  3  4")
        for y, row in enumerate(self.board):
            row_str = []
            for cell in row:
                if cell is not None:
                    abbreviation = repr(
                        cell
                    )  # Use the __repr__ function of the Piece class
                    row_str.append(abbreviation)
                else:
                    row_str.append("  ")
            print(f"{y} {' '.join(row_str)} {y}")
        print("  0  1  2  3  4")

    def get_valid_moves(self, x: int, y: int) -> List[Tuple[Card, int, int]]:
        piece = self.board[y][x]
        if piece is None:
            return []

        if piece.color != self.current_player.color:
            return []

        card_list = (
            self.red_cards
            if self.current_player.color == Color.RED
            else self.blue_cards
        )
        moves = []
        for card in card_list:
            for move in card.moves:
                # Invert the moves for the red player
                if piece.color == Color.RED:
                    move = move.invert()

                nx, ny = x + move.x, y + move.y
                if (
                    0 <= nx < 5
                    and 0 <= ny < 5
                    and (
                        self.board[ny][nx] is None
                        or self.board[ny][nx].color != piece.color
                    )
                ):
                    moves.append((card, nx, ny))
        return moves

    def move_piece(self, x: int, y: int, nx: int, ny: int) -> None:
        moving_piece = self.board[y][x]
        moving_piece.x = nx
        moving_piece.y = ny
        self.board[ny][nx] = moving_piece
        self.board[y][x] = None

    def make_move(
        self, card_name: str, x: int, y: int, nx: int, ny: int
    ) -> Optional[Player]:
        color = self.current_player.color
        if color == Color.RED:
            card_index = [card.name for card in self.red_cards].index(card_name)
            self.neutral_card, self.red_cards[card_index] = (
                self.red_cards[card_index],
                self.neutral_card,
            )
        else:
            card_index = [card.name for card in self.blue_cards].index(card_name)
            self.neutral_card, self.blue_cards[card_index] = (
                self.blue_cards[card_index],
                self.neutral_card,
            )

        self.move_piece(x, y, nx, ny)
        self.current_player = (
            self.blue_player
            if self.current_player == self.red_player
            else self.red_player
        )
        return self.check_victory()

    def check_victory(self):
        red_master = None
        blue_master = None

        for y in range(5):
            for x in range(5):
                piece = self.board[y][x]
                if piece and piece.color == Color.RED and piece.rank == Rank.MASTER:
                    red_master = piece
                elif piece and piece.color == Color.BLUE and piece.rank == Rank.MASTER:
                    blue_master = piece

        if red_master is None:
            return self.blue_player
        if blue_master is None:
            return self.red_player

        if red_master.y == 4:
            return self.red_player
        if blue_master.y == 0:
            return self.blue_player

        return None

    def prompt_move(self):
        while True:
            move_input = input(
                "Enter the card name, piece coordinates (x, y), and target coordinates (x, y): "
            )
            card_name, x, y, nx, ny = move_input.split()
            x, y, nx, ny = int(x), int(y), int(nx), int(ny)

            moves = self.get_valid_moves(x, y)
            valid_move = any(
                move[0].name == card_name and move[1] == nx and move[2] == ny
                for move in moves
            )

            if valid_move:
                return card_name, x, y, nx, ny
            else:
                print("Invalid move. Please try again.")


if __name__ == "__main__":
    game = Onitama()
    while True:
        game.display_board()
        print(f"Current player: {repr(game.current_player)}")
        print(f"Red cards: {[card.name for card in game.red_cards]}")
        print(f"Blue cards: {[card.name for card in game.blue_cards]}")
        print(f"Neutral card: '{game.neutral_card.name}'")

        card_name, x, y, nx, ny = game.prompt_move()
        winner = game.make_move(card_name, x, y, nx, ny)
        if winner is not None:
            print(f"{repr(winner)} wins!")
            break
