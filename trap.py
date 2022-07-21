

import baopig as bp


class Trap:

    LETTER = "t"

    def __init__(self, board, color, square):

        self.board = board
        self.color = color
        self.square = square
        self.trap_widget = None
        self.cage_widget = None
        self.ally = None
        self.inmate = None
        self.state = 0  # 0 : trap , 1 : cage , 2 : destroyed

    def destroy(self):
        # Only when a leash should be trapped, the trap is destroyed
        assert self.inmate is None

        self.state = 2
        if self.ally is not None:
            self.ally.unequip()
        if self.trap_widget is not None:
            self.trap_widget.hide()

    def init_display(self):

        self.trap_widget = TrapWidget(self)
        self.cage_widget = CageWidget(self)

    def move(self, square):

        self.square = square

        if self.trap_widget is not None:
            square_size = self.board.display.square_size
            if self.board.display.orientation == "w":
                for widget in (self.trap_widget, self.cage_widget):
                    widget.set_pos(topleft=((square // 10) * square_size, (square % 10) * square_size))
            else:
                for widget in (self.trap_widget, self.cage_widget):
                    widget.set_pos(topleft=((7 - square // 10) * square_size, (9 - square % 10) * square_size))

    def release(self, inmate):

        assert inmate is self.inmate
        assert inmate.is_trapped and inmate.is_captured

        inmate.cage = None
        inmate.is_trapped = False
        inmate.is_captured = False

        self.state = 2

        if self.cage_widget is not None:
            self.cage_widget.hide()

    def trap(self, piece):

        assert piece.color != self.color

        self.inmate = piece
        piece.cage = self
        piece.is_trapped = True
        piece.is_captured = True
        piece.valid_moves = piece.antiking_squares = ()

        if piece.LETTER == "d":
            if piece.is_leashed:
                piece.captured_while_leashed = True
                piece.leash.capture()

        self.state = 1

        if self.trap_widget is not None:
            self.trap_widget.hide()
            self.cage_widget.show()

    def undestroy(self):

        self.state = 0

        if self.trap_widget is not None:
            self.trap_widget.show()

    def unrelease(self, piece):

        assert self.inmate is piece
        assert piece.cage is None

        self.state = 1
        self.inmate = piece
        piece.cage = self
        piece.is_trapped = True
        piece.is_captured = True
        piece.valid_moves = piece.antiking_squares = ()

        if self.trap_widget is not None:
            assert self.trap_widget.is_hidden and self.cage_widget.is_hidden
            self.cage_widget.show()

    def untrap(self):
        # When a piece was just trapped but undo is clicked

        assert self.inmate is not None

        self.inmate.cage = None
        self.inmate.is_trapped = False
        self.inmate.uncapture()
        self.inmate = None
        self.state = 0

        if self.trap_widget:
            self.cage_widget.hide()
            self.trap_widget.show()


class TrapWidget(bp.Widget):

    def __init__(self, trap):

        square_size = trap.board.display.square_size

        image = trap.board.display.application.images[trap.color+"t"]
        image = bp.transform.scale(image, (square_size, square_size))

        pos = ((trap.square // 10) * square_size, (trap.square % 10) * square_size)
        bp.Widget.__init__(self, trap.board.display, pos=pos, surface=image)

        self.trap = trap


class CageWidget(bp.Widget):

    def __init__(self, trap):

        square_size = trap.board.display.square_size

        image = trap.board.display.application.images[trap.color+"c"]
        image = bp.transform.scale(image, (square_size, square_size))

        pos = ((trap.square // 10) * square_size, (trap.square % 10) * square_size)
        bp.Widget.__init__(self, trap.board.display, pos=pos, surface=image)

        self.trap = trap
        self.hide()
