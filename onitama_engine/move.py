class Move:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def invert(self):
        return Move(-self.x, -self.y)
