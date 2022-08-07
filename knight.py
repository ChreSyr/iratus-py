

from mainpiece import MainPiece


class Knight(MainPiece):

    LETTER = "n"
    moves = ((-2, -1), (-1, -2), (-1, 2), (1, 2), (2, 1), (2, -1), (-2, 1), (1, -2))
