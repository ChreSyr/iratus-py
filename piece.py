import time

import baopig as bp


file_dict = {0:"a", 1:"b", 2:"c", 3:"d", 4:"e", 5:"f", 6:"g", 7:"h"}


class Bonus:

    def __init__(self, board, square):

        self.widget = None
        self.board = board
        self.square = square

        self.board.add(self)

    def move(self):

        if piece.trap is not None and piece.trap.trap_widget.is_hidden:
            move.unequiped_trap = piece.trap
            piece.trap.trap_widget.show()
            piece.unequip()

        # Trap stuff
        if piece.bonus is None:
            # Trap equipement
            for bonus in self.bonus[piece.color]:
                if bonus.ally is None and bonus.square == move.end_square:
                    piece.equip(bonus)
                    move.trap_equipement = True
        else:
            piece.bonus.move(move.end_square)

    def undo(self):

        if move.trap_equipement is True:
            assert piece.trap is not None
            piece.unequip()

        if move.trap_capture is True:
            assert piece.cage is not None
            piece.cage.untrap()

        if move.broken_cage is not None:
            assert move.capture.LETTER == "s"
            move.capture, piece = piece, move.capture
            move.broken_cage.unrelease(move.capture)
            # self[move.start_square] = piece
            piece.uncapture()

        ...

        if piece.trap is not None:
            piece.trap.move(move.start_square)

        if move.destroyed_trap is not None:
            assert piece.LETTER == "l"
            move.destroyed_trap.undestroy()
            if move.capture != 0:
                move.capture.equip(move.destroyed_trap)

        if move.unequiped_trap is not None:
            assert move.unequiped_trap.square is piece.square
            piece.equip(move.unequiped_trap)


class Piece:

    LETTER = None
    moves = ()

    SubPieceAttributes = ("moves", "LETTER")
    SubPieceMethods = ("capture", "copy", "go_to", "uncapture", "undo", "update_valid_moves")

    def __init__(self, board, color, square):

        self.board = board
        self.color = color
        self.enemy_color = "w" if color == "b" else "b"
        self.square = square
        board[square] = self  # TODO

        # valid_moves is a tuple of INTEGERS
        # piece.square + valid_move = new piece.square
        self.valid_moves = ()
        self.antiking_squares = ()

        # just for calculation use
        self.is_captured = False

        # Block the next widget's link by mouse
        self.ignore_next_link = False

        # for trap attachement
        self.bonus = None
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

    def copy(self, original):
        self.is_captured = original.is_captured
        if not self.is_captured:
            self.board[original.square] = self
            if self.square != original.square:
                self.go_to(original.square)  # TODO : is it a problem when go_to is overriden ?
                # Piece.go_to(self, original.square)

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

    def init_display(self):

        self.widget = PieceWidget(self)

    def redo(self, square):

        self.go_to(square)

    def transform(self, piece_class):
        for attr in piece_class.SubPieceAttributes:
            setattr(self, attr, getattr(piece_class, attr))
        for method in piece_class.SubPieceMethods:
            setattr(self, method, bp.PrefilledFunction(getattr(piece_class, method), self))

        if self.widget is not None:
            image = self.board.display.application.images[self.color + self.LETTER]
            image = bp.transform.scale(image, (self.board.display.square_size, self.board.display.square_size))
            self.widget.set_surface(image)

            self.board.calculator.pieces_correspondence[self].transform(piece_class)

        # TODO : add the transformed piece in board.queen, board.bishops...

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


class RollingPiece(Piece):

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


class PieceMovingTwice(Piece):

    still_has_to_move = False
    SubPieceAttributes = Piece.SubPieceAttributes + ("still_has_to_move",)

    def copy(self, original):

        Piece.copy(self, original)

        if not self.is_captured:
            self.still_has_to_move = original.still_has_to_move

    def go_to(self, square):

        Piece.go_to(self, square)

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


# TODO : solve : when a PieceMovingTwice blocks a check with the first move, what next ?


class PieceWidget(bp.Focusable):

    def __init__(self, piece):

        square_size = piece.board.display.square_size

        image = piece.board.display.application.images[piece.color+piece.LETTER]
        image = bp.transform.scale(image, (square_size, square_size))

        col = piece.square // 10
        row = piece.square % 10
        pos = col * square_size, row * square_size
        bp.Focusable.__init__(self, piece.board.display, pos=pos, surface=image, layer="pieces_layer")

        self.piece = piece
        self.board_orientation_when_asleep = None

        # Allow a selected piece to be unselected when you click on it
        self._was_selected = False

        # Animation
        self.motion_animator = bp.RepeatingTimer(.01, self.animate)
        self.motion_pos = self.motion_end = self.rect.topleft

        self.piece.board.display.all_piecewidgets.append(self)

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

    def animate(self):

        if self.rect.topleft != self.motion_end:
            d = bp.Vector2(self.motion_end) - self.rect.topleft
            length = max(10., d.length() / 10)
            if d.length() > length:
                d.scale_to_length(length)
                self.motion_pos += d
                self.set_pos(topleft=self.motion_pos)
            else:
                self.set_pos(topleft=self.motion_end)
                self.motion_animator.cancel()

    def sleep(self):

        if self.rect.topleft != self.motion_end:
            self.set_pos(topleft=self.motion_end)
            self.motion_animator.cancel()
        super().sleep()
        self.board_orientation_when_asleep = self.piece.board.display.orientation

    def update_from_piece_movement(self, animate=True):

        square = self.piece.square
        if self.piece.board.display.orientation == "w":
            col, row = square // 10, square % 10
        else:
            col, row = 7 - square // 10, self.piece.board.nbranks - 1 - square % 10

        square_size = self.piece.board.display.square_size
        self.motion_animator.cancel()

        if animate:
            self.motion_end = col * square_size, row * square_size
            self.animate()
            self.motion_animator.start()
        else:
            self.set_pos(topleft=(col * square_size, row * square_size))
            self.motion_pos = self.motion_end = self.rect.topleft

    def wake(self):

        with bp.paint_lock:
            super().wake()
            if self.board_orientation_when_asleep != self.piece.board.display.orientation:

                if self.piece.board.display.orientation == "w":
                    col, row = self.piece.square // 10, self.piece.square % 10
                else:
                    col, row = 7 - self.piece.square // 10, self.piece.board.nbranks - 1 - self.piece.square % 10

                square_size = self.piece.board.display.square_size
                self.set_pos(topleft=(col * square_size, row * square_size))

                # avoid the animation if the board has been flipped since the capture
                self.motion_pos = self.motion_end = self.rect.topleft
