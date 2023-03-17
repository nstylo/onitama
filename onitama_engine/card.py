from typing import List, Tuple

from move import Move


class Card:
    def __init__(self, name: str, moves: List[Move]):
        self.name = name
        self.moves = moves

    @classmethod
    def from_tuple(cls, card_tuple: Tuple[str, List[Tuple[int, int]]]):
        return cls(card_tuple[0], [Move(x, y) for x, y in card_tuple[1]])
