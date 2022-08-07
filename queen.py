

from mainpiece import RollingMainPiece


class Queen(RollingMainPiece):

    LETTER = "q"
    moves = ((-1, -1), (-1, 1), (1, 1), (1, -1), (1, 0), (0, 1), (-1, 0), (0, -1))

