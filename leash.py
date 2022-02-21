

from piece import Piece
from king import King


class Leash(Piece):

    LETTER = "l"
    moves = ((-1, -1), (1, -1), (1, 1), (-1, 1))  # , (-2, -2), (2, -2), (2, 2), (-2, 2))

    def __init__(self, board, color, square, dog):

        Piece.__init__(self, board, color, square)

        assert dog.leash is None

        self.dog = dog
        dog.leash = self
