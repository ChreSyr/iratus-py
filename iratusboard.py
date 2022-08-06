

import baopig as bp
from board import Board, BoardDisplay, BoardPosition, Move
from piece import Piece, PieceWidget
from trap import Trap, TrapWidget, CageWidget
from pawn import IPawn
from stone import Stone
from knight import Knight
from bishop import Bishop
from leash import Leash
from dog import Dog
from rook import Rook
from queen import Queen
from king import King


class IratusBoard(Board):

    def __init__(self, game):

        Board.__init__(self, game, nbranks=10)

    def _create_pieces(self):

        # Creating pieces
        for square in range(2, 73, 10):
            IPawn(self, "b", square)
        for square in range(7, 78, 10):
            IPawn(self, "w", square)

        self.stone = {"b": (Stone(self, "b", 0), Stone(self, "b", 70)),
                      "w": (Stone(self, "w", 9), Stone(self, "w", 79))}
        self.trap = {"b": (Trap(self, "b", 30), Trap(self, "b", 40)),
                     "w": (Trap(self, "w", 39), Trap(self, "w", 49))}
        self.knight = {"b": (Knight(self, "b", 11), Knight(self, "b", 61)),
                       "w": (Knight(self, "w", 18), Knight(self, "w", 68))}
        self.bishop = {"b": (Bishop(self, "b", 21), Bishop(self, "b", 51)),
                       "w": (Bishop(self, "w", 28), Bishop(self, "w", 58))}
        self.dog = {"b": (Dog(self, "b", 10), Dog(self, "b", 60)),
                    "w": (Dog(self, "w", 19), Dog(self, "w", 69))}
        self.leash = {"b": (Leash(self, "b", 20, self.dog["b"][0]), Leash(self, "b", 50, self.dog["b"][1])),
                      "w": (Leash(self, "w", 29, self.dog["w"][0]), Leash(self, "w", 59, self.dog["w"][1]))}
        self.rook = {"b": (Rook(self, "b", 1), Rook(self, "b", 71)),
                     "w": (Rook(self, "w", 8), Rook(self, "w", 78))}
        self.queen = {"b": (Queen(self, "b", 31),), "w": (Queen(self, "w", 38),)}
        self.king = {"b": King(self, "b", 41), "w": King(self, "w", 48)}

    def get_position(self):

        return IratusBoardPosition(self, self.game.turn)

    def init_display(self, scene):

        if self.display is not None:
            raise PermissionError

        self.display = BoardDisplay(self, scene, square_size=64)
        for piece in self.pieces:
            piece.init_display()
        for set_trap in self.trap.values():
            for trap in set_trap:
                trap.init_display()

        self.calculator = IratusBoardCalculator(self)

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
                elif piece.LETTER == "ed" and piece.still_has_to_move is False:
                    cloned_piece.update_valid_moves()
                    for move2 in cloned_piece.valid_moves:
                        history_element2 = self.calculator.move(cloned_piece.square, cloned_piece.square + move2)
                        for enemy_cloned_piece2 in self.calculator.set[cloned_piece.enemy_color]:
                            enemy_cloned_piece2.update_valid_moves()
                        if not self.calculator.king[piece.color].in_check:
                            valid_moves.append(move)
                            self.calculator.undo(history_element2)
                            break
                        self.calculator.undo(history_element2)
                self.calculator.undo(history_element)

            piece.valid_moves = tuple(valid_moves)


class IratusBoardPosition(BoardPosition):

    def __init__(self, board, turn):

        BoardPosition.__init__(self, board, turn)
        self.traps = {
            "w": tuple((wtrap.square, wtrap.state) for wtrap in board.trap["w"]),
            "b": tuple((btrap.square, btrap.state) for btrap in board.trap["b"])
        }
        self._eq_attributes += ("traps",)


class IratusBoardCalculator(IratusBoard):

    def __init__(self, board):

        IratusBoard.__init__(self, board.game)

        self.real_board = board

        self.pieces_correspondence = {}
        for i, piece in enumerate(board.pieces):
            self.pieces_correspondence[piece] = self.pieces[i]

        self.traps_correspondence = {}
        for color in "w", "b":
            for i in 0, 1:
                self.traps_correspondence[board.trap[color][i]] = self.trap[color][i]

    def clone(self):

        self._squares = [0] * 80
        for piece, clone_piece in self.pieces_correspondence.items():
            clone_piece.copy(piece)

        for trap, clone_trap in self.traps_correspondence.items():
            clone_trap.square = trap.square
            clone_trap.state = trap.state

    def get_simulated_piece(self, piece):

        return self.pieces_correspondence[piece]
