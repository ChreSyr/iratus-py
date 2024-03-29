
from board import Board, BoardDisplay, BoardPosition
from dynamite import Dynamite
from trap import Trap
from pawn import TorpedoPawn
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
            TorpedoPawn(self, "b", square)
        for square in range(7, 78, 10):
            TorpedoPawn(self, "w", square)

        Stone(self, "b", 0), Stone(self, "b", 70), Stone(self, "w", 9), Stone(self, "w", 79)
        Trap(self, "b", 30), Trap(self, "b", 40), Trap(self, "w", 39), Trap(self, "w", 49)
        Knight(self, "b", 11), Knight(self, "b", 61), Knight(self, "w", 18), Knight(self, "w", 68)
        Bishop(self, "b", 21), Bishop(self, "b", 51), Bishop(self, "w", 28), Bishop(self, "w", 58)
        dogs = (Dog(self, "b", 10), Dog(self, "b", 60), Dog(self, "w", 19), Dog(self, "w", 69))
        Leash(self, "b", 20, dogs[0]), Leash(self, "b", 50, dogs[1])
        Leash(self, "w", 29, dogs[2]), Leash(self, "w", 59, dogs[3])
        Rook(self, "b", 1), Rook(self, "b", 71), Rook(self, "w", 8), Rook(self, "w", 78)
        Queen(self, "b", 31), Queen(self, "w", 38)
        self.king = {"b": King(self, "b", 41), "w": King(self, "w", 48)}

    def get_position(self):

        return IratusBoardPosition(self, self.game.turn)

    def init_display(self, scene):

        if self.display is not None:
            raise PermissionError

        self.display = BoardDisplay(self, scene, square_size=64)
        for piece in self.pieces:
            piece.init_display()
        for ep in self.extrapieces:
            ep.init_display()

        self.calculator = IratusBoardCalculator(self)

    def update_pieces_vm(self):

        for piece in self.pieces:
            piece.update_valid_moves()

        self.calculator.clone()
        for piece in self.set[self.game.turn]:
            cloned_piece = self.calculator.get_simulated_piece(piece)
            valid_moves = []  # moves who don't leave the king in check

            if hasattr(piece, "still_has_to_move") and piece.still_has_to_move is False:

                for move in piece.valid_moves:

                    history_element = self.calculator.move(cloned_piece.square, piece.square + move)
                    for enemy_cloned_piece in self.calculator.set[cloned_piece.enemy_color]:
                        enemy_cloned_piece.update_valid_moves()

                    if history_element.next_turn == piece.color:

                        valid = False
                        cloned_piece.update_valid_moves()
                        for move2 in cloned_piece.valid_moves:

                            history_element2 = self.calculator.move(cloned_piece.square, cloned_piece.square + move2)
                            for enemy_cloned_piece2 in self.calculator.set[cloned_piece.enemy_color]:
                                enemy_cloned_piece2.update_valid_moves()

                            if not self.calculator.king[piece.color].in_check:
                                valid = True
                            self.calculator.undo(history_element2)
                            if valid:
                                break

                    else:
                        valid = not self.calculator.king[piece.color].in_check

                    self.calculator.undo(history_element)
                    if valid:
                        valid_moves.append(move)

            else:
                for move in piece.valid_moves:

                    history_element = self.calculator.move(cloned_piece.square, piece.square + move)
                    for enemy_cloned_piece in self.calculator.set[cloned_piece.enemy_color]:
                        enemy_cloned_piece.update_valid_moves()
                    if not self.calculator.king[piece.color].in_check:
                        valid_moves.append(move)

                    self.calculator.undo(history_element)

            piece.valid_moves = tuple(valid_moves)


class IratusBoardPosition(BoardPosition):

    def __init__(self, board, turn):

        BoardPosition.__init__(self, board, turn)
        self.extrapieces = {
            "w": tuple((wep.square, wep.state) for wep in board.extrapieces_set["w"]),
            "b": tuple((bep.square, bep.state) for bep in board.extrapieces_set["b"])
        }
        self._EQ_ATTRIBUTES += ("extrapieces",)


class IratusBoardCalculator(IratusBoard):

    def __init__(self, board):

        IratusBoard.__init__(self, board.game)

        self.real_board = board

        self.pieces_correspondence = {}
        for i, piece in enumerate(board.pieces):
            self.pieces_correspondence[piece] = self.pieces[i]

        self.ep_correspondence = {}
        for i, ep in enumerate(board.extrapieces):
            self.ep_correspondence[ep] = self.extrapieces[i]

    def clone(self):

        self._squares = [0] * 80
        for piece, clone_piece in self.pieces_correspondence.items():
            clone_piece.copy(piece)
        for ep, clone_ep in self.ep_correspondence.items():
            clone_ep.copy(ep)

    def get_simulated_piece(self, piece):

        try:
            return self.pieces_correspondence[piece]
        except KeyError:
            return self.ep_correspondence[piece]


class Iratus2Board(IratusBoard):

    def _create_pieces(self):

        # Creating pieces
        for square in range(2, 73, 10):
            TorpedoPawn(self, "b", square)
        for square in range(7, 78, 10):
            TorpedoPawn(self, "w", square)

        Stone(self, "b", 0), Stone(self, "b", 70), Stone(self, "w", 9), Stone(self, "w", 79)
        Dynamite(self, "b", 30), Dynamite(self, "b", 40), Dynamite(self, "w", 39), Dynamite(self, "w", 49)
        Knight(self, "b", 11), Knight(self, "b", 61), Knight(self, "w", 18), Knight(self, "w", 68)
        Bishop(self, "b", 21), Bishop(self, "b", 51), Bishop(self, "w", 28), Bishop(self, "w", 58)
        dogs = (Dog(self, "b", 10), Dog(self, "b", 60), Dog(self, "w", 19), Dog(self, "w", 69))
        Leash(self, "b", 20, dogs[0]), Leash(self, "b", 50, dogs[1])
        Leash(self, "w", 29, dogs[2]), Leash(self, "w", 59, dogs[3])
        Rook(self, "b", 1), Rook(self, "b", 71), Rook(self, "w", 8), Rook(self, "w", 78)
        Queen(self, "b", 31), Queen(self, "w", 38)
        self.king = {"b": King(self, "b", 41), "w": King(self, "w", 48)}

    def init_display(self, scene):

        if self.display is not None:
            raise PermissionError

        self.display = BoardDisplay(self, scene, square_size=64)
        for piece in self.pieces:
            piece.init_display()
        for ep in self.extrapieces:
            ep.init_display()

        self.calculator = Iratus2BoardCalculator(self)


class Iratus2BoardCalculator(Iratus2Board):

    def __init__(self, board):

        IratusBoard.__init__(self, board.game)

        self.real_board = board

        self.pieces_correspondence = {}
        for i, piece in enumerate(board.pieces):
            self.pieces_correspondence[piece] = self.pieces[i]

        self.ep_correspondence = {}
        for i, ep in enumerate(board.extrapieces):
            self.ep_correspondence[ep] = self.extrapieces[i]

    def clone(self):

        self._squares = [0] * 80
        for piece, clone_piece in self.pieces_correspondence.items():
            clone_piece.copy(piece)
        for ep, clone_ep in self.ep_correspondence.items():
            clone_ep.copy(ep)

    def get_simulated_piece(self, piece):

        try:
            return self.pieces_correspondence[piece]
        except KeyError:
            return self.ep_correspondence[piece]
