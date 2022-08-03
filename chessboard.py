

import baopig as bp
from board import Board, BoardPosition, VM_Watermark
from piece import Piece, PieceWidget, file_dict
from pawn import Pawn
from knight import Knight
from bishop import Bishop
from rook import Rook
from queen import Queen
from king import King


class ChessBoard(Board):

    def __init__(self, game):

        Board.__init__(self, game, nbranks=8)

    def _create_pieces(self):

        # Creating pieces
        self.king = {}
        for square in range(1, 72, 10):
            Pawn(self, "b", square)
        for square in range(6, 77, 10):
            Pawn(self, "w", square)
        self.knight = {"b": (Knight(self, "b", 10), Knight(self, "b", 60)),
                       "w": (Knight(self, "w", 17), Knight(self, "w", 67))}
        self.bishop = {"b": (Bishop(self, "b", 20), Bishop(self, "b", 50)),
                       "w": (Bishop(self, "w", 27), Bishop(self, "w", 57))}
        self.rook = {"b": (Rook(self, "b", 0), Rook(self, "b", 70)),
                     "w": (Rook(self, "w", 7), Rook(self, "w", 77))}
        self.queen = {"b": (Queen(self, "b", 30),), "w": (Queen(self, "w", 37),)}
        self.king = {"b": King(self, "b", 40), "w": King(self, "w", 47)}

    def get_position(self):

        return BoardPosition(self, self.game.turn)

    def init_display(self, scene):

        if self.display is not None:
            raise PermissionError

        self.display = ChessBoardDisplay(self, scene)
        for piece in self.pieces:
            piece.init_display()

        self.calculator = ChessBoardCalculator(self)

    def move(self, piece, square, redo=None):
        """
        Moves a piece on a square, removes captured pieces
        Should only be called by the game
        :param piece: a Piece
        :param square: an integer
        :param redo: the move who is copied
        """

        assert piece.board is self

        old_square = piece.square
        captured_piece = self[square]
        rook_castle = None
        en_passant = None

        # En passant
        if captured_piece == 0 and piece.LETTER == "p":
            stepback = 1 if piece.color == "w" else -1
            piece_behind = self[square + stepback]
            if piece_behind != 0 and piece_behind.color != piece.color and piece_behind.LETTER == "p":
                last_move = self.game.history[-1]
                if last_move.piece is piece_behind and abs(last_move.start_square - last_move.end_square) == 2:
                    self[piece_behind.square] = 0
                    captured_piece = piece_behind
                    en_passant = piece_behind.square

        # If it was a piece
        # if captured_piece is not 0:
        if isinstance(captured_piece, Piece):
            assert captured_piece.board is self
            try:
                assert captured_piece.color != piece.color  # Chess pieces can't capture each other
            except AssertionError:
                print(2)
            captured_piece.capture()

        # Castling
        if piece.LETTER == "k":
            if piece.castle_rights[2] is False:
                file = square // 10
                if file in (2, 6):
                    if file == 6:
                        rook_castle = self.move(self[square + 10], square - 10)
                    else:
                        rook_castle = self.move(self[square - 20], square + 10)

        # Memorizing the new position for the game
        self[old_square] = 0
        self[square] = piece

        if redo is not None and redo.promotion is not None:
            piece.go_to(square, redo.promotion)
        else:
            piece.go_to(square)

        # Return informations for the game history
        return MoveForHistoric(self.game, piece, old_square, square, captured_piece, rook_castle, en_passant)

    def undo(self, move):

        assert move.piece.board is self

        if move.rook_castle is not None:
            assert move.piece.LETTER == "k"
            self.undo(move.rook_castle)

        self[move.start_square] = move.piece
        self[move.end_square] = move.capture
        move.piece.undo(move)

        if move.en_passant is not None:
            assert move.capture.LETTER == "p"
            self[move.en_passant] = move.capture
        else:
            self[move.end_square] = move.capture

        if move.capture != 0:
            assert move.capture.board is self
            move.capture.uncapture()

    def update_pieces_vm(self):

        for piece in self.pieces:
            piece.update_valid_moves()

        self.calculator.clone()
        for piece in self.set[self.game.turn]:
            cloned_piece = self.calculator.get_simulated_piece(piece)
            valid_moves = []  # moves who don't leave the king in check
            for move in piece.valid_moves:
                history_element = self.calculator.move(cloned_piece, piece.square + move)
                for enemy_cloned_piece in self.calculator.set[cloned_piece.enemy_color]:
                    enemy_cloned_piece.update_valid_moves()
                if not self.calculator.king[piece.color].in_check:
                    valid_moves.append(move)
                self.calculator.undo(history_element)

            piece.valid_moves = tuple(valid_moves)


class ChessBoardCalculator(ChessBoard):

    def __init__(self, board):

        ChessBoard.__init__(self, board.game)

        self.real_board = board

        self.pieces_correspondence = {}
        for i, piece in enumerate(board.pieces):
            self.pieces_correspondence[piece] = self.pieces[i]

    def clone(self):

        self._squares = [0] * 80
        for piece, clone_piece in self.pieces_correspondence.items():
            clone_piece.is_captured = piece.is_captured
            if not clone_piece.is_captured:
                self[piece.square] = clone_piece
                clone_piece.go_to(piece.square)

    def get_simulated_piece(self, piece):

        return self.pieces_correspondence[piece]


class ChessBoardDisplay(bp.Zone):

    def __init__(self, board, scene):

        self.square_size = 80

        bp.Zone.__init__(self, scene, size=(self.square_size * 8, self.square_size * 8),
                         background_image=scene.application.images["chessboard"], sticky="center")

        self.board = board

        # This grid layer contains the matermarks made for displaying the selected piece valid moves (vm_watermark)
        self.vm_watermarks_layer = bp.GridLayer(self, bp.Rectangle, weight=1, name="vm_watermarks_layer",
                                                row_height=self.square_size, col_width=self.square_size,
                                                nbcols=8, nbrows=8)
        # This layer contains the informative squares, as the selection square
        self.informative_squares_layer = bp.Layer(self, bp.Rectangle, weight=2, name="informative_squares_layer")

        # This grid layer contains the pieces, captured and on the board ones
        self.pieces_layer = bp.GridLayer(self, PieceWidget, name="pieces_layer", weight=3,
                                         row_height=self.square_size, col_width=self.square_size,
                                         nbcols=8, nbrows=8)

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
                                          choices=("Queen", "Rook", "Bishop", "Knight"))

        def promote(ans):
            self.pawn_to_promote.promote(eval(ans))
        self.promotion_dialog.signal.ANSWERED.connect(promote, owner=None)

        self.orientation = "w"

        self.all_piecewidgets = []

    def flip(self):

        self.orientation = "b" if self.orientation == "w" else "w"

        assert self.selected_piece is None

        with bp.paint_lock:  # freezes the display durong the operation

            pws = tuple(self.children)
            swapped = []
            for pw in pws:
                if isinstance(pw, PieceWidget):
                    if pw in swapped:
                        continue
                    try:
                        pw.piece.go_to(pw.piece.square)
                    except PermissionError:
                        pw2 = self.board[79 - pw.piece.square].widget
                        self.pieces_layer.swap(pw, pw2)
                        swapped.append(pw2)

    def select(self, widget):

        if widget.is_asleep:
            return  # occurs when a piece is captured : the selection signal is emitted right after it falls asleep

        self._selection_square.set_pos(topleft=widget.rect.topleft)
        self._selection_square.show()
        self.selected_piece = widget

        if widget.piece.color != self.board.game.turn:
            return

        for move in widget.piece.valid_moves:
            square = widget.piece.square + move
            vm_watermark = self.vm_watermarks[square]
            vm_watermark.show()
            self.visible_vm_watermarks.append(vm_watermark)

    def unselect(self, widget):

        assert widget is self.selected_piece
        self.selected_piece = None
        self._selection_square.hide()

        for vm_watermark in self.visible_vm_watermarks:
            if vm_watermark.collidemouse():
                self.board.game.move(widget.piece, vm_watermark.square)
            vm_watermark.hide()
        self.visible_vm_watermarks.clear()


class MoveForHistoric:

    def __init__(self, game, piece, old_square, square, captured_piece, rook_castle, en_passant):

        self.piece = piece
        self.start_square = old_square
        self.end_square = square
        self.capture = captured_piece
        self.promotion = None
        self.rook_castle = rook_castle
        self.en_passant = en_passant

        n = ""

        # the name of the piece, not for pawns
        if self.piece.LETTER != "p":
            n += self.piece.LETTER.capitalize()

        # When two allied knights, rooks or queens could have jump on this square
        for thing in (("n", game.board.knight), ("r", game.board.rook), ("q", game.board.queen)):
            if self.piece.LETTER == thing[0]:
                allies = []  # allies of same type who also could have make the move
                for piece2 in thing[1][self.piece.color]:
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
                        n += file_dict[self.start_square // 10] + str(10 - self.start_square % 10)

        # NOTE : some very rare times, there is 3 queens who can go on the same square
        # does my notation method handles that ?

        if self.capture != 0:

            # When a pawn captures something, we write its origin file
            if self.piece.LETTER == "p":
                n += file_dict[self.start_square // 10]
            n += "x"

        n += self.piece.coordinates
        self.notation = n
