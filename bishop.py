

from mainpiece import RollingMainPiece


class Bishop(RollingMainPiece):

    LETTER = "b"
    moves = ((-1, -1), (-1, 1), (1, 1), (1, -1))


