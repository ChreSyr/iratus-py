

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
        self.promotion = None  # The new class if this pawn promotes
        self.start_rank = self.square % 10
        self.promotion_rank = 0 if self.color == "w" else 7

    def go_to(self, square, promotion=None):

        if self.promotion is not None:
            self.promotion.go_to(self, square)
            return

        super().go_to(square)

        self._has_moved = square % 10 is not self.start_rank

        if self.rank is self.promotion_rank:
            if promotion is not None:
                self.promote(promotion)

            elif self.widget is not None:
                self.board.display.pawn_to_promote = self
                self.board.display.promotion_dialog.open()

    def undo(self, move):

        if move.promotion is not None:
            assert move.promotion is self.promotion
            self.unpromote()

        super().undo(move)

    def promote(self, piece_class):
        """
        :param piece_class: one of Queen, Rook, Bishop, Knight
        """

        # New attributes
        self.promotion = piece_class
        self.LETTER = piece_class.LETTER
        self.moves = piece_class.moves

        # board.queen most of time
        self.board.__getattribute__(piece_class.__name__.lower())[self.color] += (self,)

        # Display
        if self.widget is not None:
            self.widget.kill()
            self.init_display()

            self.board.calculator.get_simulated_piece(self).promote(piece_class)

            # Game historic
            # Needed because the dialog window is closed after the end of the history saving
            self.board.game.history[-1].promotion = piece_class
            self.board.update_pieces_vm()

        # valid moves
        self.update_valid_moves()

    def unpromote(self):
        """
        Happens when "undo" is done
        """

        # board.queen most of time
        l = list(self.board.__getattribute__(self.promotion.__name__.lower())[self.color])
        l.remove(self)
        self.board.__getattribute__(self.promotion.__name__.lower())[self.color] = tuple(l)

        # Back to old attributes
        self.promotion = None
        self.LETTER = Pawn.LETTER
        self.moves = ((0, 1), (0, 2)) if self.color == "b" else ((0, -1), (0, -2))

        # Display
        if self.widget is not None:
            self.widget.kill()
            self.init_display()

        # Calcul
        if self.board.calculator is not None:
            self.board.calculator.get_simulated_piece(self).unpromote()

    def update_valid_moves(self):

        if self.is_captured:
            return

        if self.promotion is not None:
            self.promotion.update_valid_moves(self)
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
                if self.board[square] is 0:
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
                if piece_on_attainable_square is not 0 and piece_on_attainable_square.color != self.color:
                    self.valid_moves += (d,)

                # en passant
                elif piece_on_attainable_square is 0:
                    piece_aside = self.board[self.square + dx * 10]
                    if piece_aside is not 0 and piece_aside.LETTER == "p" and piece_aside.color != self.color:
                        last_move = self.board.game.history[-1]
                        if last_move.piece is piece_aside and \
                                        abs(last_move.start_square - last_move.end_square) is 2:
                            self.valid_moves += (d,)


class IPawn(Pawn):  # Pawns for iratus

    def __init__(self, *args, **kwargs):

        Pawn.__init__(self, *args, **kwargs)

        self.promotion_rank = 0 if self.color == "w" else 9

        # ENRAGED DOG attributes
        self.leash = None
        self.is_leashed = False
        self.is_enraged = True
        self._still_has_to_move = False
        self.calm_moves = self.moves
        self.enraged_moves = ((1, 0), (0, 1), (-1, 0), (0, -1))

    def _set_still_has_to_move(self, value):

        assert bool(value) is value

        self._still_has_to_move = value
        if value is True:
            self.board.ed_secondmove = self
        elif self.board.ed_secondmove is self:
            self.board.ed_secondmove = None
    still_has_to_move = property(lambda self: self._still_has_to_move, _set_still_has_to_move)

    def promote(self, piece_class):

        super().promote(piece_class)
        if piece_class is Dog:
            Dog.enrage(self)

    def unpromote_TOREMOVE(self):

        super().unpromote()

    def update_valid_moves(self):
        """
        Just like Pawn.update_valid_moves, but always can go 2 squares forward
        """

        if self.is_captured:
            return

        if self.promotion is not None:
            self.promotion.update_valid_moves(self)
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
                if self.board[square] is 0:

                    # if there is an enemy trap on that square, we can't ride it
                    if hasattr(self.board, "trap"):
                        if True in (trap.state is 0 and trap.square is square
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
                if piece_on_attainable_square is 0:
                    piece_aside = self.board[self.square + dx * 10]
                    if piece_aside is not 0 and piece_aside.LETTER == "p" and piece_aside.color != self.color:
                        last_move = self.board.game.history[-1]
                        if last_move.piece is piece_aside and \
                                        abs(last_move.start_square - last_move.end_square) is 2:
                            self.valid_moves += (d,)

                elif piece_on_attainable_square.color != self.color:

                    # Cage
                    if piece_on_attainable_square.is_trapped:
                        continue

                    # Stone
                    if piece_on_attainable_square.LETTER == "s":
                        continue

                    self.valid_moves += (d,)
