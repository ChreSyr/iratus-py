

from mainpiece import RollingMainPiece


class Rook(RollingMainPiece):

    LETTER = "r"
    moves = ((1, 0), (0, 1), (-1, 0), (0, -1))

