

import baopig
from piece import Piece
from dog import Dog


class Pawn(Piece):

    LETTER = "p"

    def __init__(self, *args, **kwargs):

        Piece.__init__(self, *args, **kwargs)

        if self.color == "b":
            self.moves = ((0, 1), (0, 2))
            self.attacking_moves = ((1, 1), (-1, 1))
        else:
            self.moves = ((0, -1), (0, -2))
            self.attacking_moves = ((-1, -1), (1, -1))

        self._has_moved = False
        self.start_rank = self.square % 10
        self.promotion_rank = 0 if self.color == "w" else 7

    def go_to(self, square):

        super().go_to(square)

        self._has_moved = square % 10 is not self.start_rank

        if self.rank is self.promotion_rank:

            if self.widget is not None:
                self.board.display.pawn_to_promote = self
                self.board.display.promotion_dialog.open()

        # en passant
        stepback = 1 if self.color == "w" else -1
        piece_behind = self.board[self.square + stepback]
        if piece_behind != 0 and piece_behind.color != self.color and piece_behind.LETTER == "p":
            last_move = self.board.game.history[-1]
            if self.board[last_move.end_square] is piece_behind and \
                    abs(last_move.start_square - last_move.end_square) == 2:
                en_passant = "capture", piece_behind
                return en_passant,

    def update_valid_moves(self):

        if self.is_captured:
            return

        self.valid_moves = ()
        self.antiking_squares = ()
        x = self.square // 10
        y = self.square % 10

        for move in self.moves:
            dx, dy = move
            if self.board.has_square(x + dx, y + dy):
                d = dx * 10 + dy
                square = self.square + d
                if square not in self.board.existing_squares:
                    raise AssertionError
                # piece_on_attainable_square = self.board[square]
                if self.board[square] == 0:
                    self.valid_moves += (d,)
                else:
                    break  # not reaching the second step if a piece is on the front square
            if self._has_moved:
                break

        for move in self.attacking_moves:
            dx, dy = move
            if self.board.has_square(x + dx, y + dy):
                d = dx * 10 + dy
                square = self.square + d
                if square not in self.board.existing_squares:
                    raise AssertionError
                self.antiking_squares += (square,)

                piece_on_attainable_square = self.board[square]
                if piece_on_attainable_square != 0 and piece_on_attainable_square.color != self.color:
                    self.valid_moves += (d,)

                # en passant
                elif piece_on_attainable_square == 0:
                    piece_aside = self.board[self.square + dx * 10]
                    if piece_aside != 0 and piece_aside.LETTER == "p" and piece_aside.color != self.color:
                        last_move = self.board.game.history[-1]
                        if self.board[last_move.end_square] is piece_aside and \
                                abs(last_move.start_square - last_move.end_square) == 2:
                            self.valid_moves += (d,)


class IPawn(Pawn):  # Pawns for iratus

    def __init__(self, *args, **kwargs):

        Pawn.__init__(self, *args, **kwargs)

        self.promotion_rank = 0 if self.color == "w" else 9

    def update_valid_moves(self):
        """
        Just like Pawn.update_valid_moves, but always can go 2 squares forward
        """

        if self.is_captured:
            return

        self.valid_moves = ()
        self.antiking_squares = ()
        x = self.square // 10
        y = self.square % 10

        for move in self.moves:
            dx, dy = move
            if self.board.has_square(x + dx, y + dy):
                d = dx * 10 + dy
                square = self.square + d
                if square not in self.board.existing_squares:
                    raise AssertionError
                # piece_on_attainable_square = self.board[square]
                if self.board[square] == 0:

                    # if there is an enemy trap on that square, we can't ride it
                    if hasattr(self.board, "trap"):
                        if True in (trap.state == 0 and trap.square is square
                                    for trap in self.board.trap[self.enemy_color]):
                            continue

                    self.valid_moves += (d,)
                else:
                    break  # not reaching the second step if a piece is on the front square

        for move in self.attacking_moves:
            dx, dy = move
            if self.board.has_square(x + dx, y + dy):
                d = dx * 10 + dy
                square = self.square + d
                if square not in self.board.existing_squares:
                    raise AssertionError
                self.antiking_squares += (square,)

                piece_on_attainable_square = self.board[square]

                # en passant
                if piece_on_attainable_square == 0:
                    piece_aside = self.board[self.square + dx * 10]
                    if piece_aside != 0 and piece_aside.LETTER == "p" and piece_aside.color != self.color:
                        last_move = self.board.game.history[-1]
                        if self.board[last_move.end_square] is piece_aside and \
                                abs(last_move.start_square - last_move.end_square) == 2:
                            self.valid_moves += (d,)

                elif piece_on_attainable_square.color != self.color:

                    # Cage
                    if piece_on_attainable_square.is_trapped:
                        continue

                    # Stone
                    if piece_on_attainable_square.LETTER == "s":
                        continue

                    self.valid_moves += (d,)
