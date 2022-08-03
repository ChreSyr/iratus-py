
import baopig as bp
from piece import Bonus, Piece, PieceWidget


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
        self.bonus = ()  # traps, cages, dynamites...
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

        if isinstance(piece, Piece):
            self._squares[piece.square] = piece  # only time we directly use self._squares
            self.pieces += (piece,)
            self.set[piece.color] += (piece,)
        else:
            assert isinstance(piece, Bonus)
            self.bonus += (piece,)

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


class BoardPosition:
    """ Store a chess position in a final object """

    def __init__(self, board, turn):

        self.squares = [0] * 80

        for piece in board.pieces:
            if not piece.is_captured:
                self.squares[piece.square] = piece.LETTER
        self.castle_rights = {"w": board.king["w"].castle_rights.copy(),
                              "b": board.king["b"].castle_rights.copy()}
        self.turn = turn
        self._eq_attributes = ("squares", "castle_rights", "turn")

    def __eq__(self, other):

        # TODO : according to FIDE rules, I should check if en passant abilities are the same

        for attr in self._eq_attributes:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True


class BoardDisplay(bp.Zone):

    STYLE = bp.Zone.STYLE.substyle()
    STYLE.create(
        promotion_choices=("Queen", "Rook", "Bishop", "Knight"),
    )
    STYLE.modify(
        background_image=bp.image.load("Images/chessboard.png")
    )

    def __init__(self, board, scene, square_size):

        bp.Zone.__init__(self, scene, size=(square_size * 8, square_size * board.nbranks), sticky="center")

        self.board = board
        self.square_size = square_size

        # This grid layer contains the matermarks made for displaying the selected piece valid moves (vm_watermark)
        self.vm_watermarks_layer = bp.GridLayer(self, bp.Rectangle, weight=1, name="vm_watermarks_layer",
                                                row_height=self.square_size, col_width=self.square_size,
                                                nbcols=8, nbrows=board.nbranks)
        # This layer contains the informative squares, as the selection square
        # TODO : remove ?
        self.informative_squares_layer = bp.Layer(self, bp.Rectangle, weight=2, name="informative_squares_layer")

        # This layer is right behind the pieces
        self.back_layer = bp.Layer(self, name="back_layer", weight=3)

        # This grid layer contains the pieces, captured and on the board ones
        self.pieces_layer = bp.GridLayer(self, PieceWidget, name="pieces_layer", weight=4,
                                         row_height=self.square_size, col_width=self.square_size,
                                         nbcols=8, nbrows=board.nbranks)

        # This layer is just in front of the pieces
        self.front_layer = bp.Layer(self, name="front_layer", weight=5)

        # This rectangle highlights the selected piece
        self._selection_square = bp.Rectangle(self, width=self.square_size, height=self.square_size,
                                              color=(50, 250, 50))
        self._selection_square.hide()

        # Memory for the selected piece
        self.selected_piece = None

        # Dict referencing the square watermarks made for displaying a piece valid moves
        self.vm_watermarks = dict((i, VM_Watermark(self, i)) for i in self.board.existing_squares)

        # In-game displayed watermarks
        self.visible_vm_watermarks = []

        self.pawn_to_promote = None
        self.promotion_dialog = bp.Dialog(self.application, title="Promotion time !",
                                          choices=self.style["promotion_choices"])

        def promote(ans):
            self.pawn_to_promote.promote(eval(ans))
        self.promotion_dialog.signal.ANSWERED.connect(promote, owner=None)

        self.orientation = "w"

        self.all_piecewidgets = []

    def flip(self):

        self.orientation = "b" if self.orientation == "w" else "w"

        assert self.selected_piece is None

        with bp.paint_lock:  # freezes the display durong the operation

            pws = tuple(self.all_piecewidgets)
            swapped = []
            for pw in pws:
                assert isinstance(pw, PieceWidget)
                if isinstance(pw, PieceWidget):
                    if pw in swapped:
                        continue
                    try:
                        pw.piece.go_to(pw.piece.square)
                    except PermissionError:
                        pw2 = self.board[69 + self.board.nbranks - pw.piece.square].widget
                        self.pieces_layer.swap(pw, pw2)
                        swapped.append(pw2)

            for bonus in self.board.bonus:
                nsquare = 69 + self.board.nbranks - bonus.square if self.orientation == "b" else bonus.square
                x, y = nsquare // 10, nsquare % 10
                bonus.trap_widget.set_pos(topleft=(x * self.square_size, y * self.square_size))
                bonus.cage_widget.set_pos(topleft=(x * self.square_size, y * self.square_size))

                # TODO : bonus.widget.set_pos(topleft=(x * self.square_size, y * self.square_size))

    def select(self, widget):

        if widget.is_asleep:
            return  # occurs when a piece is captured : the selection signal is emitted right after it falls asleep

        # When the stone is rolled by an enemy
        if widget.piece.LETTER == "s":
            if not widget.collidemouse():
                self.selected_piece = widget
                widget.defocus()
                return

        self._selection_square.set_pos(topleft=widget.rect.topleft)
        self._selection_square.show()
        self.selected_piece = widget

        if widget.piece.color != self.board.game.turn:
            return

        try:
            if self.board.ed_secondmove is not None:
                if widget.piece != self.board.ed_secondmove:
                    return
        except AttributeError:
            pass

        start_square = widget.piece.square
        for move in widget.piece.valid_moves:
            if self.orientation == "w":
                vm_watermark = self.vm_watermarks[start_square + move]
            else:
                vm_watermark = self.vm_watermarks[69 + self.board.nbranks - start_square - move]
            vm_watermark.show()
            self.visible_vm_watermarks.append(vm_watermark)

    def unselect(self, widget):

        assert widget is self.selected_piece
        self.selected_piece = None
        self._selection_square.hide()

        for vm_watermark in self.visible_vm_watermarks:
            if vm_watermark.collidemouse():
                if self.orientation == "w":
                    self.board.game.move(widget.piece, vm_watermark.square)
                else:
                    self.board.game.move(widget.piece, 69 + self.board.nbranks - vm_watermark.square)
            vm_watermark.hide()
        self.visible_vm_watermarks.clear()


class VM_Watermark:

    def __init__(self, board, square):

        class W_VM_Watermark(bp.Rectangle):

            def __init__(self):

                bp.Rectangle.__init__(self, board, col=square // 10, row=square % 10, color=(50, 250, 50, 50),
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
