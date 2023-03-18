from enum import Enum, auto

from .constants import Color
from .move import Move


class Rank(Enum):
    MASTER = auto()
    STUDENT = auto()


class Piece:
    def __init__(self, color: Color, rank: Rank, x: int, y: int):
        self.color = color
        self.rank = rank
        self.x = x
        self.y = y

    def apply_move(self, move: Move):
        self.x += move.x
        self.y += move.y

    def to_dict(self):
        return {
            "color": self.color.value,
            "rank": self.rank.value,
            "x": self.x,
            "y": self.y,
        }

    def __repr__(self):
        color_initial = "r" if self.color == Color.RED else "b"
        rank_initial = "m" if self.rank == Rank.MASTER else "s"
        return f"{color_initial}{rank_initial}"
