

from piece import Piece


class Stone(Piece):

    LETTER = "s"
    moves = ((-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1))

    def __init__(self, *args, **kwargs):

        Piece.__init__(self, *args, **kwargs)

    def roll(self, dx, dy):

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

            # print(rolling_square, x, y, d)

            if self.board.has_square(x + dx, y + dy):
                if square + d not in self.board.existing_squares:
                    raise AssertionError
                piece_on_attainable_square = self.board[square + d]

                if piece_on_attainable_square is 0:
                    rolling_square = square + d
                    x += dx
                    y += dy
                    d += dx * 10 + dy
                    rolling = True
            else:
                rolling_square = None

        if rolling_square is not None:
            return self.board.move(self, rolling_square)

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

                if self.board.has_square(x + dx, y + dy):
                    if square + d not in self.board.existing_squares:
                        raise AssertionError
                    piece_on_attainable_square = self.board[square + d]

                    if piece_on_attainable_square is 0:

                        # if there is an enemy trap on that square, we can't ride it
                        if hasattr(self.board, "trap"):
                            if True in (trap.state is 0 and trap.square is square
                                        for trap in self.board.trap[self.enemy_color]):
                                continue

                        valid_move = d
                        x += dx
                        y += dy
                        d += dx * 10 + dy
                        rolling = True

                    elif piece_on_attainable_square.is_trapped and piece_on_attainable_square.color == self.color:
                        valid_move = d
                        rolling = False

            if valid_move is not None:
                self.valid_moves += (valid_move,)
