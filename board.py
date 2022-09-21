
import baopig as bp
from piece import file_dict
from mainpiece import MainPiece, MainPieceWidget
from extrapiece import ExtraPiece
from queen import Queen
from rook import Rook
from bishop import Bishop
from knight import Knight


class Board:

    def __init__(self, game, nbranks):

        # Game is the turn, time, history and winning manager
        self.game = game

        # _squares is the board storage
        # If a square is empty, then _squares[square.id] returns 0
        # If a square is filled with a piece, it returns the piece
        self._squares = [0] * 80

        # All the pieces, captured or not
        self.pieces = ()
        self.set = {"w": (), "b": ()}
        self.extrapieces = ()  # traps, cages, dynamites...
        self.extrapieces_set = {"w": (), "b": ()}

        # List of all the square
        # TODO : remove ? is it only used by assertions ?
        self.nbranks = nbranks
        self.existing_squares = ()
        for col in range(0, 71, 10):
            self.existing_squares += tuple(range(col+0, col+self.nbranks))

        self.current_move = None

        self._create_pieces()

        # The display is done by a different object
        # Every board doesn't have a display (calculation boards for example)
        self.display = None

        # Used by displayed boards for calculations
        self.calculator = None

    def __getitem__(self, item):

        return self._squares[item]

    def __setitem__(self, key, value):
        """ Move the piece 'value' to the square 'key' """

        if value != 0:

            assert isinstance(value, MainPiece), value

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

    def add_piece(self, piece):

        if isinstance(piece, MainPiece):
            # self[piece.square] = piece  # TODO
            self._squares[piece.square] = piece  # only time we directly use self._squares
            self.pieces += piece,
            self.set[piece.color] += piece,

        elif isinstance(piece, ExtraPiece):
            self.extrapieces += piece,
            self.extrapieces_set[piece.color] += piece,

        else:
            raise ValueError

    def get_extrapiece_at(self, square):

        for extrapiece in self.extrapieces:
            if not extrapiece.is_captured and extrapiece.state == 0 and extrapiece.square == square:
                return extrapiece
        return 0

    def get_position(self):
        """ Return a GamePosition object for the fat_history """
        raise NotImplemented

    def has_square(self, x, y):

        return 0 <= x < 8 and 0 <= y < self.nbranks

    def init_display(self, scene):
        """ Initialize a display dedicated to this board """
        raise NotImplemented

    def move(self, start_square, end_square):
        """ Should only be called by the game """

        move = Move(self, start_square, end_square)
        self.current_move = move

        move.execute_command("main_move")

        return move

    def redo(self, move):

        self.current_move = move
        piece = self[move.start_square]

        """for capture in move.captures:
            capture.capture(piece)

        for before_move in move.before_moves:
            self.redo(before_move)

        piece.redo(move.end_square)
        # piece.go_to(move.end_square)

        for after_move in move.after_moves:
            self.redo(after_move)"""

        move.redo_commands()

    def undo(self, move):
        """ Undo the last move """

        move.undo_commands()

        """for after_move in move.after_moves:
            self.undo(after_move)

        # piece = self[move.end_square]
        if move.piece.is_captured:
            assert move.piece in move.captures
            move.piece.uncapture()
        move.piece.undo(move)

        for before_move in move.before_moves:
            self.undo(before_move)

        for capture in move.captures:
            if not capture.is_captured:
                assert capture is move.piece
                continue
            capture.uncapture()"""

    def update_pieces_vm(self):
        """ Update the valid moves of all the remaining pieces """
        raise NotImplemented


class BoardPosition:
    """ Store a chess position in a final object """
    _EQ_ATTRIBUTES = ("squares", "castle_rights", "turn")

    def __init__(self, board, turn):

        self.squares = [0] * 80

        for piece in board.pieces:
            if not piece.is_captured:
                self.squares[piece.square] = piece.LETTER
        self.castle_rights = {"w": board.king["w"].castle_rights.copy(),
                              "b": board.king["b"].castle_rights.copy()}
        self.turn = turn

    def __eq__(self, other):

        # NOTE : according to FIDE rules, I should check if en passant abilities are the same

        for attr in self._EQ_ATTRIBUTES:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True


class BoardDisplay(bp.Zone):

    STYLE = bp.Zone.STYLE.substyle()
    STYLE.create(
        promotion_choices={
            "Queen": Queen,
            "Rook": Rook,
            "Bishop": Bishop,
            "Knight": Knight,
        },
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

        # This layer contains the pieces on the board
        self.pieces_layer = bp.Layer(self, MainPieceWidget, name="pieces_layer", weight=4)

        # This layer is just in front of the pieces
        self.front_layer = bp.Layer(self, name="front_layer", weight=5)

        # This rectangle highlights the selected piece
        self.selection_square = bp.Rectangle(self, width=self.square_size, height=self.square_size,
                                             color=(50, 250, 50))
        self.selection_square.hide()

        # Memory for the selected piece
        self.selected_piece = None

        # Dict referencing the square watermarks made for displaying a piece valid moves
        self.vm_watermarks = dict((i, VM_Watermark(self, i)) for i in self.board.existing_squares)

        # In-game displayed watermarks
        self.visible_vm_watermarks = []

        self.pawn_to_promote = None
        self.promotion_dialog = bp.Dialog(self.application, title="Promotion time !",
                                          choices=self.style["promotion_choices"].keys())

        def promote(ans):
            promotion = "transform", self.pawn_to_promote, self.style["promotion_choices"][ans]
            last_move = self.board.game.history[-1]
            last_move.execute_commands(commands=(promotion,))
            last_move.notation += "=" + promotion[2].LETTER.upper()
            self.board.update_pieces_vm()
            self.board.game.check_for_end()
        self.promotion_dialog.signal.ANSWERED.connect(promote, owner=None)

        self.orientation = "w"

    def flip(self, animate=True):

        self.orientation = "b" if self.orientation == "w" else "w"

        assert self.selected_piece is None

        with bp.paint_lock:  # freezes the display during the operation

            for pack in self.board.pieces, self.board.extrapieces:
                for thing in pack:
                    widget = thing.widget
                    if widget.is_awake:
                        widget.update_from_piece_movement(animate=animate)

    def select(self, widget):

        if widget.is_asleep:
            return  # occurs when a piece is captured : the selection signal is emitted right after it falls asleep

        # When the stone is rolled by an enemy
        # if widget.piece.LETTER == "s":
        #     if not widget.collidemouse():
        #         self.selected_piece = widget
        #         widget.defocus()
        #         return

        self.selection_square.set_pos(topleft=widget.rect.topleft)
        self.selection_square.show()
        self.selected_piece = widget

        if widget.piece.color != self.board.game.turn:
            return

        if self.board.game.history:
            last_move = self.board.game.history[-1]
            piece = self.board[last_move.end_square]
            if hasattr(piece, "still_has_to_move") and piece.still_has_to_move:
                if widget.piece != piece:
                    return

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
        self.selection_square.hide()

        for vm_watermark in self.visible_vm_watermarks:
            if vm_watermark.collidemouse():
                if self.orientation == "w":
                    self.board.game.move(widget.piece.square, vm_watermark.square)
                else:
                    self.board.game.move(widget.piece.square, 69 + self.board.nbranks - vm_watermark.square)
            vm_watermark.hide()
        self.visible_vm_watermarks.clear()


class Move:

    def __init__(self, board, start_square, end_square):

        self.board = board
        self.start_square = start_square
        self.end_square = end_square

        self.piece = board[start_square]
        self.commands = ()
        self.trap_equipement = None
        self.trap_capture = None
        self.unequiped_trap = None
        self.destroyed_trap = None
        self.broken_cage = None

        self.before_moves = []
        self.after_moves = []
        self.captures = []
        self.notation = None
        self.turn = self.piece.color
        self.next_turn = self.piece.enemy_color
        self.turn_number = 1
        self.counter50rule = 0

        if self.board.game.history:
            last_move = self.board.game.history[-1]
            self.turn_number = last_move.turn_number
            if last_move.turn != self.turn:
                self.turn_number += .5
                self.counter50rule = last_move.counter50rule + .5

        captured = board[end_square]
        if captured != 0:
            self.execute_command("capture", captured, self.piece)

        # Draw by 50-moves rule
        if self.piece.LETTER == "p":  # 0 when the capturer experienced a backfire
            self.counter50rule = 0

    # piece = property(lambda self: self.board[self.start_square])
    # capture = property(lambda self: self.board[self.end_square])

    def execute_commands(self, commands):
        """
        Commands & syntax :

            "anticapture", MainPiece
            "after_move", int, int
            "before_move", int, int
            "capture", MainPiece:captured, MainPiece:capturer
            "main_move"
            "notation", str
            "set_bonus", MainPiece, OldBonus, NewBonus
            "set_malus", MainPiece, OldMalus, NewMalus
            "set_next_turn", str
            "transform", MainPiece, class

        """

        if commands is None:
            return

        for command, *args in commands:
            self.execute_command(command, *args)

    def execute_command(self, command, *args):

        if command in ("after_move", "before_move"):
            self.commands += (command, self.board.move(args[0], args[1])),
        elif command == "anticapture":
            self.captures.remove(args[0])
            """elif command == "after_move":
                self.after_moves.append(self.board.move(args[0], args[1]))
                self.commands += ("move", args[0], args[1]),
            elif command == "before_move":
                self.before_moves.append(self.board.move(args[0], args[1]))
                self.commands += ("move", args[0], args[1]),"""
        elif command == "capture":
            self.commands += ("capture", *args),
            captured = args[0]
            capturer = args[1]
            self.captures.append(captured)
            self.execute_commands(captured.capture(capturer))
            self.counter50rule = 0
        elif command == "main_move":
            self.commands += ("main_move",),
            self.execute_commands(self.piece.go_to(self.end_square))
            self.init_notation()
        elif command == "notation":
            self.notation = args[0]
        elif command == "set_bonus":
            self.commands += (command, *args),
            args[0].set_bonus(args[2])  # mainpiece = args[0], new_bonus = args[2]
        elif command == "set_malus":
            self.commands += (command, *args),
            args[0].set_malus(args[2])  # mainpiece = args[0], new_malus = args[2]
        elif command == "set_next_turn":
            self.next_turn = args[0]
        elif command == "transform":
            piece = args[0]
            old_class = piece.__class__
            new_class = args[1]
            self.commands += (command, piece, old_class, new_class),
            piece.transform(new_class)
        else:
            raise ValueError(command)

    def init_notation(self):
        """ Called after the move is applied """

        if self.notation is not None:
            return

        n = ""
        piece = self.piece

        # the name of the piece, not for pawns
        if piece.LETTER != "p":
            n += piece.LETTER.capitalize()

        # When two allied knights, rooks or queens could have jump on this square
        for thing in (("n", self.board.knight), ("r", self.board.rook), ("q", self.board.queen)):
            if piece.LETTER == thing[0]:
                allies = []  # allies of same type who also could have make the move
                for piece2 in thing[1][piece.color]:
                    if piece2 is not piece:
                        for move in piece2.valid_moves:
                            if self.end_square is piece2.square + move:
                                allies.append(piece2)
                if len(allies) == 1:
                    if self.start_square // 10 is allies[0].square // 10:
                        # They are on the same file, so we indiquate the rank
                        n += str(10 - self.start_square % 10)
                    else:
                        # They are not on the same file
                        n += file_dict[self.start_square // 10]
                elif len(allies) > 1:
                    same_file = same_rank = False
                    for ally in allies:
                        if ally.file is self.start_square // 10:
                            same_file = True
                        if ally.rank is self.start_square % 10:
                            same_rank = True
                    if same_file is False:
                        # They are not on the same file
                        n += file_dict[self.start_square // 10]
                    elif same_rank is False:
                        # They are on the same file, but not on the same rank
                        n += str(10 - self.start_square % 10)
                    else:
                        # There is at least one on the same rank and one on the same file
                        # NOTE : handles when 3 queens can go on the same square
                        n += file_dict[self.start_square // 10] + str(10 - self.start_square % 10)

        # When two allied dogs could have jumped on this square
        # TODO

        if len(self.captures) != 0:

            # When a pawn captures something, we write its origin file
            if piece.LETTER == "p":
                n += file_dict[self.start_square // 10]
            n += "x"

        n += piece.coordinates

        self.notation = n

    def redo_commands(self):

        for command, *args in self.commands:
            if command in ("after_move", "before_move"):
                self.board.move(args[0], args[1])
            elif command == "capture":
                args[0].capture(args[1])  # captured = args[0], capturer = args[1]
            elif command == "main_move":
                self.piece.redo(self.end_square)
            elif command == "set_bonus":
                args[0].set_bonus(args[2])  # mainpiece = args[0], new_bonus = args[2]
            elif command == "set_malus":
                args[0].set_malus(args[2])  # mainpiece = args[0], new_malus = args[2]
            elif command == "transform":
                args[0].transform(args[2])  # piece = args[0], new_class = args[2]
            else:
                raise ValueError(command)

    def undo_commands(self):

        for command, *args in reversed(self.commands):
            if command in ("after_move", "before_move"):
                self.board.undo(args[0])
            elif command == "capture":
                captured = args[0]
                # if not captured.is_captured:
                #     assert captured is self.piece
                #     continue  # TODO : works even when removed ?
                captured.uncapture()
            elif command == "main_move":
                # piece = self[move.end_square]
                # if self.piece.is_captured:
                #     assert self.piece in self.captures
                #     move.piece.uncapture()
                self.piece.undo(self)
            elif command == "set_bonus":
                args[0].set_bonus(args[1])  # mainpiece = args[0], old_bonus = args[1]
            elif command == "set_malus":
                args[0].set_malus(args[1])  # mainpiece = args[0], old_malus = args[1]
            elif command == "transform":
                args[0].transform(args[1])  # piece = args[0], old_class = args[1]
                # TODO : fix : sometimes, self[transformation[0]] return 0 (dynamite ?)
            else:
                raise ValueError(command)


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
