
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

    # TODO : move to classes overriding it
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

    def can_be_captured_by(self, piece, move):
        """ Only called by piece.can_go_to() """

        if self.malus is not None:
            assert self.malus.LETTER == "c"
            return False
        return True

    def can_equip(self, extrapiece):

        if extrapiece.color == self.color:
            return self.bonus is None
        else:
            return False

    def can_go_to(self, square, move):

        piece = self.board[square]

        if piece == 0:
            extrapiece = self.board.get_extrapiece_at(square)
            if extrapiece != 0:
                return self.can_equip(extrapiece) and extrapiece.can_equip(self)
            return True

        if piece.color == self.color:
            return False

        return piece.can_be_captured_by(self, move)

    def capture(self, capturer):
        # The board call this function when this piece is captured

        # Memorizing the new position for the game
        assert self.board[self.square] is self
        self.board[self.square] = 0  # TODO

        self.is_captured = True
        self.valid_moves = self.antiking_squares = ()

        if self.widget is not None:
            self.widget.sleep()

        if self.malus is not None:
            if self.malus.LETTER != "c":
                raise NotImplemented("if such a malus exists, we should merge malus and bonus reactions")
            return self.malus.handle_victimcapture(capturer)

        if self.bonus is not None:
            return self.bonus.handle_allycapture(capturer)

    def copy(self, original):

        super().copy(original)
        if (self.bonus is None) != (original.bonus is None):
            if original.bonus:
                self.set_bonus(self.board.get_simulated_piece(original.bonus))
            else:
                self.set_bonus(None)
        if (self.malus is None) != (original.malus is None):
            if original.malus:
                self.set_malus(self.board.get_simulated_piece(original.malus))
            else:
                self.set_malus(None)

    def go_to(self, square):
        """
        Should only be called by the board
        """

        if self.is_captured:
            self.square = square
            return ()

        # Memorizing the new position for the game
        # assert self.board[self.square] is self
        self.board[self.square] = 0  # TODO
        self.board[square] = self  # self.square = square  # TODO

        # Memorizing the new position for the display
        if self.widget is not None:
            self.widget.update_from_piece_movement()

        if self.bonus is not None:
            self.bonus.square = square

        extrapiece = self.board.get_extrapiece_at(square)
        if extrapiece != 0:
            return extrapiece.handle_collision(self)

        return ()

    def redo(self, square):

        self.go_to(square)

    def set_bonus(self, bonus):

        if self.widget:
            print(f"SET BONUS {bonus} TO {self}")

        if bonus is not None:
            assert bonus.color == self.color
            assert bonus.ally is None
            bonus.set_ally(self)

        if self.bonus is None:
            assert bonus is not None
        else:
            assert bonus is None
            self.bonus.set_ally(None)

        self.bonus = bonus

    def set_malus(self, malus):

        if malus is not None:
            assert malus.color != self.color
            assert malus.victim is None
            assert self.malus is None
            malus.set_victim(self)

        else:
            self.malus.set_victim(None)

        self.malus = malus

        if self.widget:
            print(f"SET MALUS {malus} TO {self}")

    def uncapture(self):
        # The board call this function when this piece was captured but "undo" is done

        # Memorizing the new position for the game
        assert self.board[self.square] == 0
        self.board[self.square] = self  # TODO

        self.is_captured = False

        if self.widget is not None:
            self.widget.wake()

        if self.bonus is not None:
            self.bonus.handle_allyuncapture()

    def undo(self, move):

        assert self.board[move.end_square] is self
        self.go_to(move.start_square)

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

            if self.can_go_to(square, move):
                self.valid_moves += (d,)

        if self.bonus:
            self.bonus.update_ally_vm()
        if self.malus:
            self.malus.update_victim_vm()


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

                if not self.board.has_square(x + dx, y + dy):
                    break

                self.antiking_squares += (square,)

                piece_on_attainable_square = self.board[square]

                if self.can_go_to(square, move):
                    self.valid_moves += (d,)
                else:
                    rolling = False

                if piece_on_attainable_square == 0:
                    # we can roll one step further
                    x += dx
                    y += dy
                    d += dx * 10 + dy
                    square = start_square + d
                else:
                    rolling = False

        if self.bonus:
            self.bonus.update_ally_vm()
        if self.malus:
            self.malus.update_victim_vm()


class MainPieceMovingTwice(MainPiece):

    still_has_to_move = False
    ATTR_TO_COPY = MainPiece.ATTR_TO_COPY + ("still_has_to_move",)

    def copy(self, original):

        MainPiece.copy(self, original)

        if not self.is_captured:
            self.still_has_to_move = original.still_has_to_move

    def go_to(self, square):

        commands = MainPiece.go_to(self, square)

        # if just trapped, ignore second move
        if commands:
            for command, *args in commands:
                if command == "set_malus" and args[2] is not None and args[2].LETTER == "c":
                    return commands

        self.still_has_to_move = not self.still_has_to_move
        if self.still_has_to_move:
            return commands + (("set_next_turn", self.color),)

        return commands

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

            if self.can_go_to(square, move):
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

        if self.bonus:
            self.bonus.update_ally_vm()
        if self.malus:
            self.malus.update_victim_vm()
