

from piece import Piece


class Dog(Piece):

    LETTER = "d"
    moves = ((-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1))

    def __init__(self, board, color, square):

        Piece.__init__(self, board, color, square)

        self.leash = None
        self.captured_while_leashed = False
        self.is_enraged = False

        self.calm_moves = self.moves
        self.enraged_moves = ((1, 0), (0, 1), (-1, 0), (0, -1))
        self._still_has_to_move = False

        # TODO : check if the dog can reach the king by moving twice

    is_leashed = property(lambda self: (self.leash is not None) and (not self.leash.is_captured))

    def _set_still_has_to_move(self, value):

        assert bool(value) is value

        self._still_has_to_move = value
        if value is True:
            self.board.ed_secondmove = self
        elif self.board.ed_secondmove is self:
            self.board.ed_secondmove = None
    still_has_to_move = property(lambda self: self._still_has_to_move, _set_still_has_to_move)

    def capture(self):

        super().capture()
        if self.is_leashed:
            self.captured_while_leashed = True

    def enrage(self):

        self.is_enraged = True

        self.moves = self.enraged_moves

        if self.widget is not None:
            self.widget.set_surface(self.widget.enraged_image)

    def uncapture(self):

        super().uncapture()
        if self.leash is not None:
            if self.captured_while_leashed is True:
                self.captured_while_leashed = False

    def unenrage(self):

        self.is_enraged = False

        self.moves = self.calm_moves

        if self.widget is not None:
            self.widget.set_surface(self.widget.calm_image)

    def update_valid_moves(self):

        if self.is_captured:
            return

        self.valid_moves = ()
        self.antiking_squares = ()

        if self.is_leashed:

            x = self.leash.square // 10
            y = self.leash.square % 10
            from_dog_to_leash = self.leash.square - self.square

            for move in self.moves:

                dx, dy = move

                if self.board.has_square(x + dx, y + dy):
                    d = dx * 10 + dy
                    square = self.leash.square + d
                    if square not in self.board.existing_squares:
                        raise AssertionError
                    self.antiking_squares += (square,)

                    piece_on_attainable_square = self.board[square]

                    attainable = False

                    if piece_on_attainable_square is 0:

                        # if there is an enemy trap on that square, we can't ride it
                        if hasattr(self.board, "trap"):
                            if True in (trap.state is 0 and trap.square is square
                                        for trap in self.board.trap[self.enemy_color]):
                                continue

                        self.valid_moves += (from_dog_to_leash + d,)
                        attainable = True

                    elif piece_on_attainable_square.color != self.color:

                        # Cage
                        if piece_on_attainable_square.is_trapped:
                            continue

                        # Stone
                        if piece_on_attainable_square.LETTER == "s":
                            continue

                        self.valid_moves += (from_dog_to_leash + d,)
                        attainable = True   # TODO : is it useless ?

        else:

            x = self.square // 10
            y = self.square % 10

            for move in self.moves:

                dx, dy = move

                if self.board.has_square(x + dx, y + dy):
                    d = dx * 10 + dy
                    square = self.square + d
                    if square not in self.board.existing_squares:
                        raise AssertionError
                    self.antiking_squares += (square,)

                    piece_on_attainable_square = self.board[square]
                    attainable = False
                    if piece_on_attainable_square is 0:
                        self.valid_moves += (d,)
                        attainable = True
                    elif piece_on_attainable_square.color != self.color:

                        # Cage
                        if piece_on_attainable_square.is_trapped:
                            continue

                        if piece_on_attainable_square.LETTER == "s":
                            # Cannot pull a stone if there is a piece behind
                            # Only works if all the rolling pieces have 1 square moves
                            if self.board.has_square(x + 2 * dx, y + 2 * dy):
                                piece_behind_stone = self.board[square + dx * 10 + dy]
                                if piece_behind_stone is not 0:
                                    continue

                        self.valid_moves += (d,)
                        attainable = True

                    if self.is_enraged and attainable is True:

                        x2 = square // 10
                        y2 = square % 10

                        for second_move in self.moves:

                            dx2, dy2 = second_move

                            if self.board.has_square(x2 + dx2, y2 + dy2):
                                d2 = dx2 * 10 + dy2
                                square2 = square + d2
                                if square2 is self.square:
                                    continue
                                if square2 in self.antiking_squares:
                                    continue
                                self.antiking_squares += (square2,)
