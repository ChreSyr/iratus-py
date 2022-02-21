

from piece import RollingPiece


class Rook(RollingPiece):

    LETTER = "r"
    moves = ((1, 0), (0, 1), (-1, 0), (0, -1))

