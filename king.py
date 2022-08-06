

from piece import Piece


# TODO : King cannot ride a trap ? Or yes ?


class King(Piece):

    LETTER = "k"
    moves = ((-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1))

    def __init__(self, *args, **kwargs):

        Piece.__init__(self, *args, **kwargs)

        # [long castle right, short castle right, turn_number_of_first_move]
        self.castle_rights = [False, False, None]

    in_check = property(lambda self: self.square_is_under_check(self.square))

    def copy(self, original):

        super().copy(original)
        self.castle_rights = original.castle_rights.copy()

    def go_to(self, square):

        Piece.go_to(self, square)

        if self.castle_rights[2] is None:
            self.castle_rights[2] = self.board.current_move.turn_number

            file = square // 10
            if file == 6 and self.castle_rights[1]:
                rook_castle = "after_move", square + 10, square - 10
                notation = "notation", "0-0"
                return rook_castle, notation
            elif file == 2 and self.castle_rights[0]:
                rook_castle = "after_move", square - 20, square + 10
                notation = "notation", "0-0-0"
                return rook_castle, notation

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

                if self.can_capture(self.board[square], move):
                    self.valid_moves += (d,)

        if self.castle_rights[2] is None and not self.in_check:

            # TODO : remember if the rooks have moved

            # castling at right

            can_short_castle = False
            piece_at_right_corner = self.board[self.square + 30]
            if isinstance(piece_at_right_corner, Piece) and piece_at_right_corner.LETTER == "r" and piece_at_right_corner.color:
                can_short_castle = True
                for move in (10, 20):
                    square = self.square + move
                    if self.board[square] != 0 or self.square_is_under_check(square):
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
                    if self.board[square] != 0 or self.square_is_under_check(square):
                        can_long_castle = False
                        break
                if self.board[self.square - 30] != 0:
                    can_long_castle = False
            if can_long_castle:
                self.valid_moves += (-20,)
            self.castle_rights[0] = can_long_castle

    def undo(self, move):

        super().undo(move)
        if move.turn_number == self.castle_rights[2]:
            assert self.castle_rights[2] is not None
            self.castle_rights[2] = None

        # start_file = move.start_square // 10
        # end_file = move.end_square // 10
        # if abs(start_file - end_file) == 2:
