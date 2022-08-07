
import baopig as bp


file_dict = {0:"a", 1:"b", 2:"c", 3:"d", 4:"e", 5:"f", 6:"g", 7:"h"}


class Piece:

    WIDGET_CLASS = None

    LETTER = None
    moves = ()

    ATTR_TO_COPY = "LETTER",
    METH_TO_COPY = "copy", "go_to"

    def __init__(self, board, color, square):

        self.board = board
        self.color = color
        self.enemy_color = "w" if color == "b" else "b"
        self.square = square

        # just for calculation use
        self.is_captured = False

        # Block the next widget's link by mouse
        self.ignore_next_link = False

        # The display is done by a different object
        # Every piece doesn't have a widget (calculation pieces for example)
        self.widget = None

        self.board.add_piece(self)

    def __str__(self):

        return self.__class__.__name__ + "_captured" if self.is_captured \
            else self.__class__.__name__ + "_" + self.coordinates

    coordinates = property(lambda self: file_dict[self.file] + str(self.board.nbranks - self.rank))
    file = property(lambda self: self.square // 10)
    rank = property(lambda self: self.square % 10)

    def copy(self, original):

        self.is_captured = original.is_captured
        if self.is_captured:
            return

        self.board[original.square] = self

        # TODO : can be replaced by a transform somewhere ?
        # piece_class = original.__class__
        # for attr in piece_class.ATTR_TO_COPY:
        #     setattr(self, attr, getattr(piece_class, attr))
        # for method in piece_class.METH_TO_COPY:
        #     setattr(self, method, bp.PrefilledFunction(getattr(piece_class, method), self))

        if self.square != original.square:
            self.go_to(original.square)

    def go_to(self, square):
        """
        Should only be called by the board
        """

        if self.is_captured:
            self.square = square
            return

        # Memorizing the new position for the display
        if self.widget is not None:
            self.widget.update_from_piece_movement()

    def init_display(self):

        self.widget = self.WIDGET_CLASS(self)

    def transform(self, piece_class):

        for attr in piece_class.ATTR_TO_COPY:
            setattr(self, attr, getattr(piece_class, attr))
        for method in piece_class.METH_TO_COPY:
            setattr(self, method, bp.PrefilledFunction(getattr(piece_class, method), self))

        if self.widget is not None:
            image = self.board.display.application.images[self.color + self.LETTER]
            image = bp.transform.scale(image, self.widget.rect.size)
            self.widget.set_surface(image)

            self.board.calculator.pieces_correspondence[self].transform(piece_class)

        # TODO : add the transformed piece in board.queen, board.bishops...


class PieceWidget(bp.Widget):

    LAYER = None

    def __init__(self, piece):

        square_size = piece.board.display.square_size

        image = piece.board.display.application.images[piece.color+piece.LETTER]
        image = bp.transform.scale(image, (square_size, square_size))

        col = piece.square // 10
        row = piece.square % 10
        pos = col * square_size, row * square_size
        bp.Widget.__init__(self, piece.board.display, pos=pos, surface=image, layer=self.LAYER)

        self.piece = piece
        self.board_orientation_when_asleep = None

        # Animation
        self.motion_animator = bp.RepeatingTimer(.01, self.animate)
        self.motion_pos = self.motion_end = self.rect.topleft

    def __str__(self):

        return "Widget_" + str(self.piece)

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
