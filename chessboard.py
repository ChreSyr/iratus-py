

import baopig as bp
from board import Board, BoardDisplay, BoardPosition, VM_Watermark
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

        self.display = BoardDisplay(self, scene, square_size=80)
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


class MoveForHistoric:

    def __init__(self, game, piece, old_square, square, captured_piece, rook_castle, en_passant):

        self.piece = piece
        self.start_square = old_square
        self.end_square = square
        self.capture = captured_piece
        self.promotion = None
        self.rook_castle = rook_castle
        self.en_passant = en_passant

        self.notation = ""
        self._init_notation(game)

    def _init_notation(self, game):

        n = ""

        # the name of the piece, not for pawns
        if self.piece.LETTER != "p":
            n += self.piece.LETTER.capitalize()

        # When two allied knights, rooks or queens could have jump on this square
        for thing in (("n", game.board.knight), ("r", game.board.rook), ("q", game.board.queen)):
            if self.piece.LETTER == thing[0]:
                allies = []  # allies of same type who also could have make the move
                for piece2 in thing[1][self.piece.color]:
                    if piece2 is not self.piece:
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

        if self.rook_castle is not None:
            if self.rook_castle.piece.square // 10 == 5:
                n = "0-0"
            else:
                n = "0-0-0"

        self.notation = n
