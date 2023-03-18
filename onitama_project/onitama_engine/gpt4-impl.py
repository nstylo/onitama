import random


class Onitama:
    def __init__(self):
        self.board = [[None] * 5 for _ in range(5)]
        self.cards = self.generate_cards()
        self.current_cards = random.sample(self.cards, 5)
        self.red_cards = self.current_cards[:2]
        self.blue_cards = self.current_cards[2:4]
        self.neutral_card = self.current_cards[4]
        self.current_player = "red" if random.random() < 0.5 else "blue"
        self.setup_board()

    def generate_cards(self):
        cards = [
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
        return cards

    def setup_board(self):
        for i in range(5):
            if i == 2:
                self.board[0][i] = ("red", "master")
                self.board[4][i] = ("blue", "master")
            else:
                self.board[0][i] = ("red", "student")
                self.board[4][i] = ("blue", "student")

    def display_board(self):
        print("  0  1  2  3  4")
        for y, row in enumerate(self.board):
            row_str = []
            for cell in row:
                if cell is not None:
                    color, piece = cell
                    abbreviation = f"{color[0]}{piece[0]}"
                    row_str.append(abbreviation)
                else:
                    row_str.append("  ")
            print(f"{y} {' '.join(row_str)} {y}")
        print("  0  1  2  3  4")

    def get_valid_moves(self, x, y):
        if self.board[y][x] is None:
            return []

        color, piece = self.board[y][x]
        if color != self.current_player:
            return []

        card_list = self.red_cards if color == "red" else self.blue_cards
        moves = []
        for card in card_list:
            for dx, dy in card[1]:
                # Invert the moves for the blue player
                if color == "red":
                    dy = -dy
                    dx = -dx

                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < 5
                    and 0 <= ny < 5
                    and (self.board[ny][nx] is None or self.board[ny][nx][0] != color)
                ):
                    moves.append((card[0], nx, ny))
        return moves

    def move_piece(self, x, y, nx, ny):
        self.board[ny][nx] = self.board[y][x]
        self.board[y][x] = None

    def make_move(self, card_name, x, y, nx, ny):
        color = self.current_player
        if color == "red":
            card_index = [card[0] for card in self.red_cards].index(card_name)
            self.neutral_card, self.red_cards[card_index] = (
                self.red_cards[card_index],
                self.neutral_card,
            )
        else:
            card_index = [card[0] for card in self.blue_cards].index(card_name)
            self.neutral_card, self.blue_cards[card_index] = (
                self.blue_cards[card_index],
                self.neutral_card,
            )

        self.move_piece(x, y, nx, ny)
        self.current_player = "blue" if self.current_player == "red" else "red"
        return self.check_victory()

    def check_victory(self):
        red_master = None
        blue_master = None

        for y in range(5):
            for x in range(5):
                piece = self.board[y][x]
                if piece == ("red", "master"):
                    red_master = (x, y)
                elif piece == ("blue", "master"):
                    blue_master = (x, y)

        if red_master is None:
            return "blue"
        if blue_master is None:
            return "red"

        if red_master[1] == 4:
            return "red"
        if blue_master[1] == 0:
            return "blue"

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
                move[0] == card_name and move[1] == nx and move[2] == ny
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
        print(f"Current player: {game.current_player}")
        print(f"Red cards: {[card[0] for card in game.red_cards]}")
        print(f"Blue cards: {[card[0] for card in game.blue_cards]}")
        print(f"Neutral card: {game.neutral_card[0]}")

        card_name, x, y, nx, ny = game.prompt_move()
        winner = game.make_move(card_name, x, y, nx, ny)
        if winner is not None:
            print(f"{winner} wins!")
            break
