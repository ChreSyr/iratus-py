

from piece import Piece


# TODO : King cannot ride a trap ? Or yes ?


class King(Piece):

    LETTER = "k"
    moves = ((-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1))

    def __init__(self, *args, **kwargs):

        Piece.__init__(self, *args, **kwargs)

        self.castle_rights = [False, False, False]  # [long castle right, short castle right, has_moved]

    in_check = property(lambda self: self.square_is_under_check(self.square))

    def go_to(self, square):

        Piece.go_to(self, square)

        self.castle_rights[2] = True

    def square_is_under_check(self, square):
        # if the square is under check, returns True

        for piece in self.board.set[self.enemy_color]:
            if not piece.is_captured:
                if square in piece.antiking_squares:
                    return True
        return False

    def update_valid_moves(self):

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
                self.antiking_squares += (square,)

                piece_on_attainable_square = self.board[square]
                if piece_on_attainable_square is 0:

                    # if there is an enemy trap on that square, we can't ride it
                    if hasattr(self.board, "trap"):
                        if True in (trap.state is 0 and trap.square is square
                                    for trap in self.board.trap[self.enemy_color]):
                            continue

                    self.valid_moves += (d,)

                elif piece_on_attainable_square.color != self.color:
                    # if piece_on_attainable_square.LETTER == "l":
                    #     continue
                    if not piece_on_attainable_square.is_trapped:
                        if piece_on_attainable_square.trap is None:
                            self.valid_moves += (d,)

        if self.castle_rights[2] is False and not self.in_check:

            # castling at right

            can_short_castle = False
            piece_at_right_corner = self.board[self.square + 30]
            if isinstance(piece_at_right_corner, Piece) and piece_at_right_corner.LETTER == "r" and piece_at_right_corner.color:
                can_short_castle = True
                for move in (10, 20):
                    square = self.square + move
                    if self.board[square] is not 0 or self.square_is_under_check(square):
                        can_short_castle = False
                        break
            if can_short_castle:
                self.valid_moves += (20,)
            self.castle_rights[1] = can_short_castle

            # castling at left

            can_long_castle = False
            piece_at_left_corner = self.board[self.square - 40]
            if isinstance(piece_at_left_corner, Piece) and piece_at_left_corner.LETTER == "r":
                can_long_castle = True
                for move in (-10, -20):
                    square = self.square + move
                    if self.board[square] is not 0 or self.square_is_under_check(square):
                        can_long_castle = False
                        break
                if self.board[self.square - 30] is not 0:
                    can_long_castle = False
            if can_long_castle:
                self.valid_moves += (-20,)
            self.castle_rights[0] = can_long_castle

