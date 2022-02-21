

from piece import RollingPiece


class Bishop(RollingPiece):

    LETTER = "b"
    moves = ((-1, -1), (-1, 1), (1, 1), (1, -1))


