
import baopig as bp


file_dict = {0:"a", 1:"b", 2:"c", 3:"d", 4:"e", 5:"f", 6:"g", 7:"h"}


class Piece:

    LETTER = None
    moves = ()

    def __init__(self, board, color, square):

        self.board = board
        self.color = color
        self.enemy_color = "w" if color == "b" else "b"
        self.square = square
        # board.squares[square] = self  # TODO

        # valid_moves is a tuple of INTEGERS
        # piece.square + valid_move = new piece.square
        self.valid_moves = ()
        self.antiking_squares = ()

        # just for calculation use
        self.is_captured = False

        # for trap attachement
        self.trap = None  # ally
        self.cage = None  # enemy
        self.is_trapped = False  # should only be modified by Trap objects
        # self.trapped_while_having_trap = False

        # The display is done by a different object
        # Every piece doesn't have a widget (calculation pieces for example)
        self.widget = None

        self.board.add(self)

    def __str__(self):

        return self.__class__.__name__ + "_captured" if self.is_captured \
            else self.__class__.__name__ + "_" + self.coordinates

    coordinates = property(lambda self: file_dict[self.file] + str(self.board.nbranks - self.rank))
    file = property(lambda self: self.square // 10)
    rank = property(lambda self: self.square % 10)

    def capture(self):
        # The board call this function when this piece is captured

        self.is_captured = True
        self.valid_moves = self.antiking_squares = ()

        if self.widget is not None:
            self.widget.sleep()

    def equip(self, trap):

        assert trap.color == self.color
        assert self.trap is None
        assert trap.ally is None

        self.trap = trap
        trap.ally = self

    def go_to(self, square):
        """
        Should only be called by the board
        """

        # Memorizing the new position for the game
        # self.square = square  # TODO

        # Memorizing the new position for the display
        if self.widget is not None:

            if self.board.display.orientation == "w":
                col, row = square // 10, square % 10
            else:
                col, row = 7 - square // 10, self.board.nbranks - 1 - square % 10

            if self.widget.is_awake:
                self.widget.layer.move(self.widget, col, row)
            else:
                self.widget._row = row
                self.widget._col = col

    def init_display(self):

        self.widget = PieceWidget(self)

    def uncapture(self):
        # The board call this function when this piece was captured but "undo" is done

        self.is_captured = False

        if self.widget is not None:
            self.widget.set_lock(pos=False)
            self.widget.wake()

    def undo(self, move):

        assert move.piece is self
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

            if self.board.has_square(x + dx, y + dy):
                d = dx * 10 + dy
                square = self.square + d
                if square not in self.board.existing_squares:
                    raise AssertionError
                self.antiking_squares += (square,)

                piece_on_attainable_square = self.board[square]

                # if no piece is on the square
                if piece_on_attainable_square == 0:

                    # if there is an enemy trap on that square, we can't ride it
                    if hasattr(self.board, "trap"):
                        if True in (trap.state == 0 and trap.square is square
                                    for trap in self.board.trap[self.enemy_color]):
                            continue

                    self.valid_moves += (d,)

                elif piece_on_attainable_square.color != self.color:

                    # Cage
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

                    self.valid_moves += (d,)


class RollingPiece(Piece):

    def update_valid_moves(self):

        if self.is_captured:
            return

        self.valid_moves = ()
        self.antiking_squares = ()
        square = self.square

        for move in self.moves:

            dx, dy = move
            x = square // 10
            y = square % 10
            d = dx * 10 + dy

            rolling = True
            while rolling:
                rolling = False

                if self.board.has_square(x + dx, y + dy):

                    self.antiking_squares += (square + d,)

                    piece_on_attainable_square = self.board[square + d]

                    if piece_on_attainable_square == 0:

                        rolling = True

                        # if there is an enemy trap on that square, we can't ride it
                        if hasattr(self.board, "trap"):
                            if True in (trap.state == 0 and trap.square is square + d
                                        for trap in self.board.trap[self.enemy_color]):
                                rolling = False

                        # we can roll one step further
                        if rolling is True:

                            # if there is an ally trap on that square, we can't go further
                            if hasattr(self.board, "trap"):
                                if True in (trap.state == 0 and trap.square is square + d
                                            for trap in self.board.trap[self.color]):
                                    rolling = False

                            self.valid_moves += (d,)
                            x += dx
                            y += dy
                            d += dx * 10 + dy

                    elif piece_on_attainable_square.color != self.color:

                        # Cage
                        if piece_on_attainable_square.is_trapped:
                            continue

                        # Cannot pull a stone if there is a piece behind
                        # Only works if all the rolling pieces have 1 square moves
                        if piece_on_attainable_square.LETTER == "s":
                            if self.board.has_square(x + 2 * dx, y + 2 * dy):
                                piece_behind_stone = self.board[square + d + dx * 10 + dy]
                                if piece_behind_stone != 0:
                                    continue

                        self.valid_moves += (d,)


class PieceWidget(bp.Focusable):

    def __init__(self, piece):

        image = piece.board.display.application.images[piece.color+piece.LETTER]
        image = bp.transform.scale(image, (piece.board.display.square_size, piece.board.display.square_size))

        bp.Focusable.__init__(self, piece.board.display, col=piece.square // 10, row=piece.square % 10,
                              surface=image)

        self.piece = piece

        # Allow a selected piece to be unselected when you click on it
        self._was_selected = False

        if piece.LETTER == "d":
            self.calm_image = image
            self.enraged_image = bp.transform.scale(
                piece.board.display.application.images[piece.color+"ed"],
                (piece.board.display.square_size, piece.board.display.square_size)
            )
        
        self.piece.board.display.all_piecewidgets.append(self)

    def __str__(self):

        return "Widget_" + str(self.piece)

    def handle_focus(self):

        if self.is_asleep:
            self.defocus()  # when a piece grabs another one, the grabbed one is focused just before it disappears
        else:
            self.parent.select(self)

    def handle_defocus(self):

        if self.is_asleep:
            return

        self._was_selected = False
        self.parent.unselect(self)

    def handle_link(self):

        if self.is_asleep:
            return

        if self._was_selected:

            # Trap unequipement
            if self.piece.board.game.turn == self.piece.color and self.piece.trap is not None:
                if self.piece.trap.trap_widget.is_visible:
                    self.piece.trap.trap_widget.hide()
                else:
                    # was on a trap unequipement but clicked again on the piece
                    self.piece.trap.trap_widget.show()
                    self._was_selected = False
                    self.defocus()

            else:
                self._was_selected = False
                self.defocus()
        else:
            self._was_selected = True

    def handle_unlink(self):

        if self.is_asleep:
            return
        
        for vm_watermark in self.parent.visible_vm_watermarks:
            if vm_watermark.collidemouse():
                assert self.parent.selected_piece is self
                self.defocus()
                return

