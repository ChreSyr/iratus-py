

from mainpiece import RollingMainPiece, HasMoved


class Rook(RollingMainPiece, HasMoved):

    LETTER = "r"
    moves = ((1, 0), (0, 1), (-1, 0), (0, -1))

