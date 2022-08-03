
import baopig as bp
from piece import Piece


class Board:

    def __init__(self, game, nbranks):

        # Game is the turn, time, history and winning manager
        self.game = game

        # _squares is the board storage
        # If a square is empty, then _squares[square.id] returns 0
        # If a square is filled with a piece, it returns the piece
        self._squares = [0] * 80

        # All the pieces, captured and on the board ones
        self.pieces = ()
        self.set = {"w": (), "b": ()}

        # List of all the square
        # TODO : remove ? is it only used by assertions ?
        self.nbranks = nbranks
        self.existing_squares = ()
        for col in range(0, 71, 10):
            self.existing_squares += tuple(range(col+0, col+self.nbranks))

        self._create_pieces()

        # The display is done by a different object
        # Every board doesn't have a display (calculation boards for example)
        self.display = None

        # Used by displayed boards for calculations
        self.calculator = None

        # TODO
        self.ed_secondmove = None

    def __getitem__(self, item):

        return self._squares[item]

    def __setitem__(self, key, value):
        """ Move the piece 'value' to the square 'key' """

        if value != 0:

            assert isinstance(value, Piece), value

            if self._squares[value.square] is not value:
                try:
                    index = self._squares.index(value)
                    self._squares[index] = 0
                except ValueError:
                    pass

            value.square = key

        self._squares[key] = value

    def _create_pieces(self):
        """ Called once at construction """

    def add(self, piece):

        assert isinstance(piece, Piece)
        self._squares[piece.square] = piece  # only time we directly use self._squares
        self.pieces += (piece,)
        self.set[piece.color] += (piece,)

    def get_position(self):
        """ Return a GamePosition object for the fat_history """
        raise NotImplemented

    def has_square(self, x, y):

        return 0 <= x < 8 and 0 <= y < self.nbranks

    def init_display(self, scene):
        """ Initialize a display dedicated to this board """
        raise NotImplemented

    def move(self, piece, square, redo=None):
        """
        Moves a piece on a square, removes captured pieces
        Should only be called by the game
        """
        raise NotImplemented

    def undo(self, move):
        """ Undo the last move TODO : remove the parameter """
        raise NotImplemented

    def update_pieces_vm(self):
        """ Update the valid moves of all the remaining pieces """
        raise NotImplemented


class VM_Watermark:

    def __init__(self, board, square):

        class W_VM_Watermark(bp.Rectangle):

            def __init__(self):

                bp.Rectangle.__init__(self, board, col=square//10, row=square%10, color=(50, 250, 50, 50),
                                      width=80, height=80, layer=board.vm_watermarks_layer)
                self.hide()

        self.board = board
        self.square = square
        self.widget = W_VM_Watermark()

        self.col = self.widget.col
        self.row = self.widget.row

        self.show = self.widget.show
        self.hide = self.widget.hide
        self.collidemouse = self.widget.collidemouse
