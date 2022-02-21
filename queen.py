

from piece import RollingPiece


class Queen(RollingPiece):

    LETTER = "q"
    moves = ((-1, -1), (-1, 1), (1, 1), (1, -1), (1, 0), (0, 1), (-1, 0), (0, -1))

