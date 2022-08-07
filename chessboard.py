

from board import Board, BoardDisplay, BoardPosition
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

    def update_pieces_vm(self):

        for piece in self.pieces:
            piece.update_valid_moves()

        self.calculator.clone()
        for piece in self.set[self.game.turn]:
            cloned_piece = self.calculator.get_simulated_piece(piece)
            valid_moves = []  # moves who don't leave the king in check
            for move in piece.valid_moves:
                history_element = self.calculator.move(cloned_piece.square, piece.square + move)
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
            clone_piece.copy(piece)

    def get_simulated_piece(self, piece):

        return self.pieces_correspondence[piece]
