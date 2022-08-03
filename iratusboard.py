

import baopig as bp
from board import Board, VM_Watermark
from piece import Piece, PieceWidget, file_dict
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

        self.display = IratusBoardDisplay(self, scene)
        for piece in self.pieces:
            piece.init_display()
        for set_trap in self.trap.values():
            for trap in set_trap:
                trap.init_display()

        self.calculator = IratusBoardCalculator(self)

    def move(self, piece, square, redo=None):
        """
        Moves a piece on a square, removes captured pieces
        Should only be called by the game
        :param piece: a Piece
        :param square: an integer
        """

        # TODO : rework redo param, use the notation of the promotion instead

        assert piece.board is self

        stone_roll = None
        dog_pull = None
        rook_castle = None
        trap_equipement = False
        trap_capture = False
        unequiped_trap = None
        destroyed_trap = None
        broken_cage = None
        wasted_leash1 = None  # in the worst scenario, two leashes can be wasted during the same turn
        wasted_leash2 = None  # happens when a dog captures a leash equiped with a trap
        old_square = piece.square
        captured_piece = self[square]

        if piece.trap is not None and piece.trap.trap_widget.is_hidden:
            unequiped_trap = piece.trap
            piece.trap.trap_widget.show()
            piece.unequip()

        # En passant
        if captured_piece == 0 and piece.LETTER == "p":
            stepback = 1 if piece.color == "w" else -1
            piece_behind = self[square + stepback]
            if piece_behind != 0 and piece_behind.color != piece.color and piece_behind.LETTER == "p":
                last_move = self.game.history[-1]
                if last_move.piece is piece_behind and abs(last_move.start_square - last_move.end_square) == 2:
                    self[piece_behind.square] = 0
                    captured_piece = piece_behind

        # If it was a piece
        if isinstance(captured_piece, Piece):
            assert captured_piece.board is self

            if captured_piece.color == piece.color:  # Chess pieces can't capture each other

                try:
                    # Cage break
                    assert captured_piece.is_trapped
                    assert piece.LETTER == "s"

                    broken_cage = captured_piece.cage
                    captured_piece.cage.release(captured_piece)  # The prisonner is released
                    piece.capture()  # The stone breaks

                    piece, captured_piece = captured_piece, piece

                except AssertionError:
                    print(2)

            else:

                # Stone roll
                if isinstance(captured_piece, Stone):
                    stone_roll = captured_piece.roll(square // 10 - old_square // 10, square % 10 - old_square % 10)
                    if stone_roll is not None:  # The stone has not been ejected
                        # print("Stone roll : from {} to {}".format(square, captured_piece.square))
                        captured_piece = 0
                    # else, the stone calls itself its capture() function

                elif isinstance(captured_piece, Dog):
                    if not captured_piece.leash.is_captured:
                        wasted_leash1 = (captured_piece.leash, captured_piece.leash.square)

                elif isinstance(captured_piece, Leash):
                    captured_piece.dog.enrage()

                if captured_piece != 0:
                    captured_piece.capture()
                    if captured_piece.trap is not None:

                        # A leash breaks traps
                        if piece.LETTER == "l":
                            destroyed_trap = captured_piece.trap
                            captured_piece.trap.destroy()

                        else:
                            trap_capture = True
                            captured_piece.trap.trap(piece)
                            if piece.LETTER == "d" and piece.leash is not None:
                                wasted_leash2 = (piece.leash, piece.leash.square)
                                piece.enrage()

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
            promotion = redo.promotion
        else:
            piece.go_to(square)
            promotion = None

        # Trap capture when no piece was on the trap
        if captured_piece == 0:
            for trap in self.trap[piece.enemy_color]:
                if trap.square is square and trap.state == 0:

                    # A leash breaks traps
                    if piece.LETTER == "l":
                        destroyed_trap = trap
                        trap.destroy()

                    else:
                        trap_capture = True
                        trap.trap(piece)
                        if piece.LETTER == "d" and piece.leash is not None:
                            wasted_leash2 = (piece.leash, piece.leash.square)
                            piece.enrage()

                    break

        if wasted_leash1 is not None:
            self[wasted_leash1[1]] = 0
            wasted_leash1[0].capture()
        if wasted_leash2 is not None:
            self[wasted_leash2[1]] = 0
            wasted_leash2[0].capture()

        # Trap stuff
        if piece.trap is None:
            # Trap equipement
            for trap in self.trap[piece.color]:
                if trap.ally is None and trap.square == square:
                    piece.equip(trap)
                    trap_equipement = True
        else:
            piece.trap.move(square)

        # Dog pull
        if piece.LETTER == "l":
            leash = piece
            dog = leash.dog
            if abs(leash.square % 10 - dog.square % 10) > 1:
                dog_pull = self.move(piece.dog, old_square)
            elif abs(leash.square // 10 - dog.square // 10) > 1:
                dog_pull = self.move(piece.dog, old_square)

        # Return information for the game history
        return MoveForHistoric(self.game, piece, old_square, square, captured_piece,
                               rook_castle, stone_roll, dog_pull,
                               trap_equipement, trap_capture,
                               unequiped_trap, destroyed_trap, broken_cage,
                               wasted_leash1, wasted_leash2,
                               promotion)

    def undo(self, move):

        assert move.piece.board is self

        if move.dog_pull is not None:
            assert move.piece.LETTER == "l"
            self.undo(move.dog_pull)

        if move.rook_castle is not None:
            assert move.piece.LETTER == "k"
            self.undo(move.rook_castle)

        if move.trap_equipement is True:
            assert move.piece.trap is not None
            move.piece.unequip()

        if move.trap_capture is True:
            assert move.piece.cage is not None
            move.piece.cage.untrap()

        if move.broken_cage is not None:
            assert move.capture.LETTER == "s"
            move.capture, move.piece = move.piece, move.capture
            move.broken_cage.unrelease(move.capture)
            self[move.start_square] = move.piece
            move.piece.uncapture()

        self[move.start_square] = move.piece
        self[move.end_square] = move.capture
        move.piece.undo(move)

        if move.wasted_leash1 is not None:
            self[move.wasted_leash1[1]] = move.wasted_leash1[0]
            move.wasted_leash1[0].uncapture()
        if move.wasted_leash2 is not None:
            self[move.wasted_leash2[1]] = move.wasted_leash2[0]
            move.wasted_leash2[0].uncapture()
            assert move.piece.LETTER == "d"
            move.piece.unenrage()

        if move.piece.trap is not None:
            move.piece.trap.move(move.start_square)

        if move.capture != 0:
            if move.broken_cage is None:
                assert move.capture.board is self
                move.capture.uncapture()

                if move.capture.LETTER == "l":
                    move.capture.dog.unenrage()

        if move.destroyed_trap is not None:
            assert move.piece.LETTER == "l"
            move.destroyed_trap.undestroy()
            if move.capture != 0:
                move.capture.equip(move.destroyed_trap)

        if move.unequiped_trap is not None:
            assert move.unequiped_trap.square is move.piece.square
            move.piece.equip(move.unequiped_trap)

        if move.stone_roll is not None:
            self.undo(move.stone_roll)

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
                elif piece.LETTER == "d" and piece.is_enraged and piece.still_has_to_move is False:
                    cloned_piece.update_valid_moves()
                    for move2 in cloned_piece.valid_moves:
                        history_element2 = self.calculator.move(cloned_piece, cloned_piece.square + move2)
                        for enemy_cloned_piece2 in self.calculator.set[cloned_piece.enemy_color]:
                            enemy_cloned_piece2.update_valid_moves()
                        if not self.calculator.king[piece.color].in_check:
                            valid_moves.append(move)
                            self.calculator.undo(history_element2)
                            break
                        self.calculator.undo(history_element2)
                self.calculator.undo(history_element)

            piece.valid_moves = tuple(valid_moves)


class IratusBoardPosition:
    """
    Saves a chess position in a final object
    """

    def __init__(self, board, turn):

        self.squares = [0] * 80

        for piece in board.pieces:
            if not piece.is_captured:
                self.squares[piece.square] = piece.LETTER
        self.castle_rights = {
            "w": board.king["w"].castle_rights.copy(),
            "b": board.king["b"].castle_rights.copy()
        }
        self.traps = {
            "w": tuple((wtrap.square, wtrap.state) for wtrap in board.trap["w"]),
            "b": tuple((btrap.square, btrap.state) for btrap in board.trap["b"])
        }
        self.turn = turn

    def __eq__(self, other):

        return self.squares == other.squares and \
                self.castle_rights == other.castle_rights and \
                self.traps == other.traps and \
                self.turn == other.turn


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
            clone_piece.is_captured = piece.is_captured
            if not clone_piece.is_captured:
                self[piece.square] = clone_piece
                clone_piece.go_to(piece.square)

                if clone_piece.LETTER == "d":
                    clone_piece.is_enraged = piece.is_enraged
                    clone_piece.still_has_to_move = piece.still_has_to_move
                    clone_piece.moves = piece.moves  # because it changes when enraged

        for trap, clone_trap in self.traps_correspondence.items():
            clone_trap.square = trap.square
            clone_trap.state = trap.state

    def get_simulated_piece(self, piece):

        return self.pieces_correspondence[piece]


class IratusBoardDisplay(bp.Zone):

    def __init__(self, board, scene):

        self.square_size = 64

        bp.Zone.__init__(self, scene, size=(self.square_size * 8, self.square_size * 10),
                         background_image=scene.application.images["iratusboard"], sticky="center")

        self.board = board

        # This grid layer contains the watermarks made for displaying the selected piece valid moves (vm_watermark)
        self.vm_watermarks_layer = bp.GridLayer(self, bp.Rectangle, weight=1, name="vm_watermarks_layer",
                                                row_height=self.square_size, col_width=self.square_size,
                                                nbcols=8, nbrows=10)

        # This layer contains the informative squares, as the selection square
        self.informative_squares_layer = bp.Layer(self, bp.Rectangle, weight=2, name="informative_squares_layer")

        # This layer contains the traps
        self.traps_layer = bp.Layer(self, TrapWidget, name="traps_layer", weight=3)

        # This grid layer contains the pieces, captured and on the board ones
        self.pieces_layer = bp.GridLayer(self, PieceWidget, name="pieces_layer", weight=4, nbcols=8, nbrows=10,
                                         row_height=self.square_size, col_width=self.square_size)

        # This grid is same as pieces_layer, and used for the board flip
        self.flipper_layer = bp.Layer(self, PieceWidget, name="flipper_layer", weight=4.1)

        # This layer contains the cages
        self.cages_layer = bp.Layer(self, CageWidget, name="cages_layer", weight=5)

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
                                          choices=("Queen", "Rook", "Bishop", "Knight", "Dog"))

        def promote(ans):
            self.pawn_to_promote.promote(eval(ans))
        self.promotion_dialog.signal.ANSWERED.connect(promote, owner=None)

        self.orientation = "w"

        self.all_piecewidgets = []

    def flip(self):

        # TODO : same for ChessBoardDisplay

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
                        pw2 = self.board[79 - pw.piece.square].widget
                        self.pieces_layer.swap(pw, pw2)
                        swapped.append(pw2)

            for color_traps in self.board.trap.values():
                for trap in color_traps:
                    nsquare = 79 - trap.square if self.orientation == "b" else trap.square
                    x, y = nsquare // 10, nsquare % 10
                    trap.trap_widget.set_pos(topleft=(x * self.square_size, y * self.square_size))
                    trap.cage_widget.set_pos(topleft=(x * self.square_size, y * self.square_size))

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

        if self.board.ed_secondmove is not None:
            if widget.piece != self.board.ed_secondmove:
                return

        start_square = widget.piece.square
        for move in widget.piece.valid_moves:
            if self.orientation == "w":
                vm_watermark = self.vm_watermarks[start_square + move]
            else:
                vm_watermark = self.vm_watermarks[79 - start_square - move]
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
                    self.board.game.move(widget.piece, 79 - vm_watermark.square)
            vm_watermark.hide()
        self.visible_vm_watermarks.clear()


class MoveForHistoric:

    def __init__(self, game, piece, old_square, square, captured_piece,
                 rook_castle, stone_roll, dog_pull,
                 trap_equipement, trap_capture,
                 unequiped_trap, destroyed_trap, broken_cage,
                 wasted_leash1, wasted_leash2,
                 promotion=None):

        self.piece = piece
        self.start_square = old_square
        self.end_square = square
        self.capture = captured_piece
        self.rook_castle = rook_castle
        self.stone_roll = stone_roll
        self.dog_pull = dog_pull
        self.trap_equipement = trap_equipement
        self.trap_capture = trap_capture
        self.unequiped_trap = unequiped_trap
        self.destroyed_trap = destroyed_trap
        self.broken_cage = broken_cage
        self.wasted_leash1 = wasted_leash1
        self.wasted_leash2 = wasted_leash2
        self.promotion = promotion

        n = ""

        # E for enraged dogs
        if piece.LETTER == "d" and piece.is_enraged:
            n += "E"  # For enraged dog

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

        # When two allied dogs could have jumped on this square
        # TODO

        if self.capture != 0:

            # When a pawn captures something, we write its origin file
            if self.piece.LETTER == "p":
                n += file_dict[self.start_square // 10]
            n += "x"

        n += self.piece.coordinates

        if rook_castle is not None:
            if rook_castle.piece.square // 10 == 5:
                n = "0-0"
            else:
                n = "0-0-0"



        self.notation = n

