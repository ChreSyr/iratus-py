

from piece import Piece


class Knight(Piece):

    LETTER = "n"
    moves = ((-2, -1), (-1, -2), (-1, 2), (1, 2), (2, 1), (2, -1), (-2, 1), (1, -2))


