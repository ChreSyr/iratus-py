
import baopig as bp
from piece import Piece, PieceWidget


class MainPieceWidget(PieceWidget, bp.Focusable):

    LAYER = "pieces_layer"

    def __init__(self, piece):

        PieceWidget.__init__(self, piece)
        bp.Focusable.__init__(self, self.parent)

        # Allow a selected piece to be unselected when you click on it
        self._was_selected = False

    def __str__(self):

        return "Widget_" + str(self.piece)

    def handle_focus(self):

        if self.is_asleep:
            self.defocus()  # when a piece grabs another one, the grabbed one is focused just before it disappears

    def handle_defocus(self):

        if self.is_asleep:
            return

        self._was_selected = False
        if self.parent.selected_piece is self:
            self.parent.unselect(self)

    def handle_link(self):

        if self.is_asleep:
            return  # just captured

        if self.piece.ignore_next_link:
            self.piece.ignore_next_link = False
            self.defocus()
            self.unlink()
            return

        self._was_selected = self.parent.selected_piece is self
        self.parent.select(self)

        self.motion_animator.cancel()
        self.layer.overlay(len(self.layer), self)

    def handle_link_motion(self, rel):

        if self.is_asleep:
            return  # just captured
        self.move(*rel)

    def handle_unlink(self):

        if self.is_asleep:
            return  # just captured

        for vm_watermark in self.parent.visible_vm_watermarks:
            if vm_watermark.collidemouse():
                assert self.parent.selected_piece is self
                self.motion_pos = self.rect.pos
                self.defocus()
                return

        self.motion_pos = self.rect.pos
        if self.parent.selection_square.collidemouse():
            if self._was_selected:
                self.defocus()
        else:
            self.defocus()
        self.update_from_piece_movement()


class MainPiece(Piece):

    WIDGET_CLASS = MainPieceWidget
    ATTR_TO_COPY = Piece.ATTR_TO_COPY + ("moves",)
    METH_TO_COPY = Piece.METH_TO_COPY + ("capture", "redo", "uncapture", "undo", "update_valid_moves")

    def __init__(self, board, color, square):

        Piece.__init__(self, board, color, square)

        # valid_moves is a tuple of INTEGERS
        # piece.square + valid_move = new piece.square
        self.valid_moves = ()
        self.antiking_squares = ()

        # for bonus equipement
        self.bonus = None
        self.malus = None

    def can_capture(self, piece, move):

        if piece == 0:
            return True

        if piece.color == self.color:
            return False

        return piece.can_be_captured_by(self, move)

    def can_be_captured_by(self, piece, move):
        """ Only called by piece.can_capture() """

        return True

    def capture(self, capturer):
        # The board call this function when this piece is captured

        # Memorizing the new position for the game
        assert self.board[self.square] is self
        self.board[self.square] = 0  # TODO

        self.is_captured = True
        self.valid_moves = self.antiking_squares = ()

        if self.widget is not None:
            self.widget.sleep()

    def go_to(self, square):
        """
        Should only be called by the board
        """

        if self.is_captured:
            self.square = square
            return

        # Memorizing the new position for the game
        # assert self.board[self.square] is self
        self.board[self.square] = 0  # TODO
        self.board[square] = self  # self.square = square  # TODO

        # Memorizing the new position for the display
        if self.widget is not None:
            self.widget.update_from_piece_movement()

    def redo(self, square):

        self.go_to(square)

    def set_bonus(self, trap):  # TODO

        assert trap.color == self.color
        assert self.trap is None
        assert trap.ally is None

        self.trap = trap
        trap.ally = self

    def uncapture(self):
        # The board call this function when this piece was captured but "undo" is done

        # Memorizing the new position for the game
        assert self.board[self.square] == 0
        self.board[self.square] = self  # TODO

        self.is_captured = False

        if self.widget is not None:
            self.widget.set_lock(pos=False)
            self.widget.wake()

    def undo(self, move):

        assert self.board[move.end_square] is self
        self.go_to(move.start_square)

    def unequip(self):

        # TODO : find a graphic way to unequip the trap during a move

        assert self.trap is not None

        self.trap.ally = None
        self.trap = None

    def update_valid_moves(self):

        if self.is_captured:
            return

        self.valid_moves = ()
        self.antiking_squares = ()
        x = self.square // 10
        y = self.square % 10

        for move in self.moves:

            dx, dy = move

            if not self.board.has_square(x + dx, y + dy):
                continue

            d = dx * 10 + dy
            square = self.square + d
            if square not in self.board.existing_squares:
                raise AssertionError
            self.antiking_squares += (square,)

            if self.can_capture(self.board[square], move):
                self.valid_moves += (d,)
            continue

            piece_on_attainable_square = self.board[square]
            # if no piece is on the square
            if piece_on_attainable_square == 0:

                # if there is an enemy trap on that square, we can't ride it
                # TODO
                if hasattr(self.board, "trap"):
                    if True in (trap.state == 0 and trap.square is square
                                for trap in self.board.trap[self.enemy_color]):
                        continue

                self.valid_moves += (d,)

            elif piece_on_attainable_square.color != self.color and False:

                # Cage
                # TODO
                if piece_on_attainable_square.is_trapped:
                    continue

                # If it is a stone, pawns, knights and leashed dogs cannot move it
                # pawns and leashed dog magange this themselves, only have to care about knight
                if piece_on_attainable_square.LETTER == "s":
                    if self.LETTER == "n":
                        continue
                    # Cannot pull a stone if there is a piece behind
                    # Only works if all the rolling pieces have 1 square moves
                    if self.board.has_square(x + 2 * dx, y + 2 * dy):
                        piece_behind_stone = self.board[square + dx * 10 + dy]
                        if piece_behind_stone != 0:
                            continue

            elif self.can_capture(piece_on_attainable_square, move):
                self.valid_moves += (d,)


class RollingMainPiece(MainPiece):

    def update_valid_moves(self):

        if self.is_captured:
            return

        self.valid_moves = ()
        self.antiking_squares = ()
        start_square = self.square

        for move in self.moves:

            dx, dy = move
            x = start_square // 10
            y = start_square % 10
            d = dx * 10 + dy
            square = start_square + d

            rolling = True
            while rolling:
                rolling = False

                if not self.board.has_square(x + dx, y + dy):
                    continue

                self.antiking_squares += (square,)

                piece_on_attainable_square = self.board[square]

                if self.can_capture(piece_on_attainable_square, move):
                    self.valid_moves += (d,)

                if piece_on_attainable_square == 0:
                    # we can roll one step further
                    x += dx
                    y += dy
                    d += dx * 10 + dy
                    square = start_square + d
                    rolling = True


class MainPieceMovingTwice(MainPiece):

    still_has_to_move = False
    ATTR_TO_COPY = MainPiece.ATTR_TO_COPY + ("still_has_to_move",)

    def copy(self, original):

        MainPiece.copy(self, original)

        if not self.is_captured:
            self.still_has_to_move = original.still_has_to_move

    def go_to(self, square):

        MainPiece.go_to(self, square)

        self.still_has_to_move = not self.still_has_to_move
        if self.still_has_to_move:
            return ("set_next_turn", self.color),

    def update_valid_moves(self):

        if self.is_captured:
            return

        self.valid_moves = ()
        self.antiking_squares = ()
        x = self.square // 10
        y = self.square % 10

        for move in self.moves:

            dx, dy = move

            if not self.board.has_square(x + dx, y + dy):
                continue

            d = dx * 10 + dy
            square = self.square + d
            if square not in self.board.existing_squares:
                raise AssertionError
            self.antiking_squares += (square,)

            if self.can_capture(self.board[square], move):
                self.valid_moves += (d,)

                x2 = square // 10
                y2 = square % 10

                for second_move in self.moves:

                    dx2, dy2 = second_move

                    if self.board.has_square(x2 + dx2, y2 + dy2):
                        d2 = dx2 * 10 + dy2
                        square2 = square + d2
                        if square2 == self.square:
                            continue
                        if square2 in self.antiking_squares:
                            continue
                        self.antiking_squares += (square2,)
