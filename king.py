

from mainpiece import MainPiece


# TODO : King cannot ride a trap ? Or yes ?


class King(MainPiece):

    LETTER = "k"
    moves = ((-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1))

    def __init__(self, *args, **kwargs):

        MainPiece.__init__(self, *args, **kwargs)

        # [long castle right, short castle right, turn_number_of_first_move]
        self.castle_rights = [False, False, None]

    in_check = property(lambda self: self.square_is_under_check(self.square))

    def can_equip(self, bonus):

        return False

    def can_go_to(self, square, move):

        for piece in self.board.set[self.enemy_color]:
            if square in piece.antiking_squares:
                return False
        return super().can_go_to(square, move)

    def copy(self, original):

        super().copy(original)
        self.castle_rights = original.castle_rights.copy()

    def go_to(self, square):

        commands = MainPiece.go_to(self, square)

        if self.castle_rights[2] is None:
            self.castle_rights[2] = self.board.current_move.turn_number

            file = square // 10
            if file == 6 and self.castle_rights[1]:
                rook_castle = "after_move", square + 10, square - 10
                notation = "notation", "0-0"
                return commands + (rook_castle, notation)
            elif file == 2 and self.castle_rights[0]:
                rook_castle = "after_move", square - 20, square + 10
                notation = "notation", "0-0-0"
                return commands + (rook_castle, notation)

        return commands

    def square_is_under_check(self, square):
        # if the square is under check, returns True

        for piece in self.board.set[self.enemy_color]:
            if not piece.is_captured:
                if square in piece.antiking_squares:
                    return True
        return False

    def update_valid_moves(self):

        super().update_valid_moves()

        if self.castle_rights[2] is None and not self.in_check:

            # TODO : remember if the rooks have moved

            # castling at right

            can_short_castle = False
            piece_at_right_corner = self.board[self.square + 30]
            if isinstance(piece_at_right_corner, MainPiece) and piece_at_right_corner.LETTER == "r" and piece_at_right_corner.color:
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
            if isinstance(piece_at_left_corner, MainPiece) and piece_at_left_corner.LETTER == "r":
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
