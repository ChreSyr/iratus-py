

from mainpiece import MainPiece


class Stone(MainPiece):

    LETTER = "s"
    moves = ((-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1))

    def _roll(self, dx, dy):

        dx = 1 if dx > 0 else -1 if dx < 0 else 0
        dy = 1 if dy > 0 else -1 if dy < 0 else 0

        square = self.square
        x = square // 10
        y = square % 10
        d = dx * 10 + dy
        rolling_square = None

        rolling = True
        while rolling:
            rolling = False

            if self.board.has_square(x + dx, y + dy):
                if square + d not in self.board.existing_squares:
                    raise AssertionError
                piece_on_attainable_square = self.board[square + d]

                if piece_on_attainable_square == 0:
                    rolling_square = square + d
                    x += dx
                    y += dy
                    d += dx * 10 + dy
                    rolling = True
            else:
                rolling_square = None

        if rolling_square is not None:
            roll = "before_move", self.square, rolling_square
            uncapture = "anticapture", self
            return roll, uncapture

    def can_be_captured_by(self, piece, move):

        # A pawn can't pull a stone
        if piece.LETTER == 'p':
            return False

        # Cannot pull a stone if there is a piece behind
        # Only works if all the move is vertical, horizontal or diagonal (knights can't roll stones)
        dx, dy = move
        if abs(dx) != abs(dy) and 0 not in (dx, dy):
            return False

        normalized_dx = max(min(dx, 1), -1)
        normalized_dy = max(min(dy, 1), -1)
        x = self.square // 10
        y = self.square % 10
        if self.board.has_square(x + normalized_dx, y + normalized_dy):
            piece_behind_stone = self.board[self.square + normalized_dx * 10 + normalized_dy]
            if piece_behind_stone != 0:
                return False

        return True

    def capture(self, capturer):

        start_square = capturer.square

        if start_square == self.square:  # cage release
            return super().capture(capturer)

        roll = self._roll(self.square // 10 - start_square // 10, self.square % 10 - start_square % 10)
        if roll:  # The stone has not been ejected
            self.ignore_next_link = True
            return roll

        else:
            return super().capture(capturer)

    def go_to(self, square):

        prisoner = self.board[square]
        if prisoner == 0:
            return super().go_to(square)
        else:
            assert prisoner.malus.LETTER == "c"
            cancel_mainmove = "cancel_mainmove",
            autodestruction = "capture", self, self
            release = "set_malus", prisoner, prisoner.malus, None
            return cancel_mainmove, autodestruction, release

    def update_valid_moves(self):

        if self.is_captured:
            return

        self.valid_moves = ()

        for move in self.moves:

            dx, dy = move
            square = self.square
            x = square // 10
            y = square % 10
            d = dx * 10 + dy
            valid_move = None

            rolling = True
            while rolling:
                rolling = False

                if not self.board.has_square(x + dx, y + dy):
                    continue

                if square + d not in self.board.existing_squares:
                    raise AssertionError
                piece_on_attainable_square = self.board[square + d]

                if piece_on_attainable_square == 0:

                    # if there is an enemy trap on that square, we can't ride it
                    extrapiece = self.board.get_extrapiece_at(square + d)
                    if extrapiece != 0:
                        continue
                    if False and hasattr(self.board, "trap"):
                        if True in (trap.is_availible and trap.square is square
                                    for trap in self.board.trap[self.enemy_color]):
                            continue

                    valid_move = d
                    x += dx
                    y += dy
                    d += dx * 10 + dy
                    rolling = True

                elif piece_on_attainable_square.LETTER == self.LETTER and \
                        piece_on_attainable_square.color != self.color:
                    valid_move = d
                    rolling = False

                elif piece_on_attainable_square.malus and piece_on_attainable_square.malus.LETTER == "c":  # in a cage
                    if piece_on_attainable_square.color == self.color:
                        valid_move = d
                        rolling = False

            if valid_move is not None:
                self.valid_moves += (valid_move,)

        if self.bonus:
            self.bonus.update_ally_vm()
        if self.malus:
            self.malus.update_victim_vm()
