from .constants import Color


class Player:
    def __init__(self, color: Color):
        self.color = color

    def __repr__(self):
        return f"{self.color.name.capitalize()} Player"
