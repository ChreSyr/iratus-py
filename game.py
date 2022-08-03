

class Game:

    def __init__(self, scene):

        self.app = scene.application

        self.board = scene.board_class(self)

        # a history element is an object saying (a "piece" came from "square1" to "square2" and captured "something")
        self.history = []
        self.back_history = []  # stores undone moves
        self.fat_history = []  # stores board positions (for draws by repetition)

        # w is white to move, b is black to move
        self.turn = "w"

        # for 50-moves rule
        self.counter50rule = 0

        # w is white won, b is black won, d is drawn
        self.result = None

        # Initializing pieces valid moves
        for piece in self.board.set[self.turn]:
            piece.update_valid_moves()

        # Initializing board and pieces display
        self.board.init_display(scene)

    def check_for_end(self):

        # Draw by 50-moves rule
        if self.history[-1].piece.LETTER == "p":
            self.counter50rule = 0
        elif self.history[-1].capture != 0:
            self.counter50rule = 0
        else:
            self.counter50rule += 1
        if self.counter50rule >= 50:
            return "Draw by 50-moves rule"

        # Draw by insufficient material
        remaining_pieces = {"w": [], "b": []}
        for piece in self.board.pieces:
            if piece.is_captured is False:
                if piece.LETTER == "k":
                    continue
                remaining_pieces[piece.color].append(piece)

        def insufficient_materiel(set):
            # TODO : sligthly more accurate draws
            # For example, if the two players still have a kniht, checkmate is possible
            if len(set) == 0:
                return True
            if len(set) == 1:
                return set[0].LETTER in ("n", "b")
            if len(set) == 2:
                return set[0].LETTER == set[0].LETTER == "n"
            return False
        if insufficient_materiel(remaining_pieces["w"]) and insufficient_materiel(remaining_pieces["b"]):
            return "draw by insufficient material"

        # Draw by repetition
        if len(self.fat_history) > 5:
            current_position = self.fat_history[-1]
            count = 1
            for position in self.fat_history[:-1]:
                if position == current_position:
                    count += 1
            if count == 3:
                return "Draw by repetition"

        game_state = "keep going"
        if self.board.king[self.turn].in_check:
            game_state = "check"

        for piece in self.board.set[self.turn]:
            if not piece.is_captured and piece.valid_moves:

                # Still at least one valid move

                return game_state

        # No more move : checkmate or stalemate
        if self.board.king[self.turn].in_check:
            return "checkmate"
        else:
            return "stalemate"

    def move(self, piece, square):

        assert piece.color is self.turn

        self.history.append(self.board.move(piece, square))  # piece, old_square, square, captured_piece

        # Next turn
        # For the color who just played, we need to update the antiking squares
        self.turn = piece.enemy_color

        # Enraged dog exception
        # TODO
        if piece.LETTER == "d" and piece.is_enraged:
            if piece.cage is None:
                piece.still_has_to_move = not piece.still_has_to_move
                if piece.still_has_to_move:
                    self.turn = piece.color
            else:  # the dog just got trapped
                piece.still_has_to_move = False

        # We need to update the antiking squares for both colors
        self.board.update_pieces_vm()

        # This occurs after the valid moves update because we need the castling rights
        self.fat_history.append(self.board.get_position())
        self.back_history.clear()

        game_state = self.check_for_end()

        if game_state == "checkmate":
            self.history[-1].notation += "#"
        elif game_state == "check":
            self.history[-1].notation += "+"

        # TODO : promotion, cage, compact edog notation, result of the game

    def redo(self):
        """
        Redo the last undone move
        """

        if len(self.back_history) == 0:
            return

        last_undone_move = self.back_history.pop(-1)

        assert last_undone_move.piece.color is self.turn

        # TODO
        if hasattr(last_undone_move, "unequiped_trap"):
            if last_undone_move.unequiped_trap is not None:
                last_undone_move.unequiped_trap.trap_widget.hide()  # so the unequipement works

        self.history.append(self.board.move(last_undone_move.piece, last_undone_move.end_square, redo=last_undone_move))

        self.turn = last_undone_move.piece.enemy_color

        # Enraged dog exception
        # TODO
        piece = last_undone_move.piece
        if piece.LETTER == "d" and piece.is_enraged:
            if piece.cage is None and last_undone_move.broken_cage is None:
                piece.still_has_to_move = not piece.still_has_to_move
                if piece.still_has_to_move:
                    self.turn = piece.color
            else:  # just got trapped
                piece.still_has_to_move = False

        self.board.update_pieces_vm()

        # This occurs after the valid moves update because we need the castling rights
        self.fat_history.append(self.board.get_position())

    def undo(self):
        """
        Undo the last move
        """

        if len(self.history) == 0:
            return

        last_move = self.history.pop(-1)
        self.fat_history.pop(-1)
        self.back_history.append(last_move)

        # TODO
        if last_move.piece.LETTER == "d" and last_move.piece.is_enraged and \
                        last_move.piece.still_has_to_move is False and \
                        last_move.piece.cage is None and last_move.broken_cage is None:
            last_move.piece.still_has_to_move = True

        elif last_move.piece.LETTER == "d" and last_move.piece.still_has_to_move is True:
            last_move.piece.still_has_to_move = False
        else:
            assert last_move.piece.color is not self.turn

        self.board.undo(last_move)

        if self.fat_history:
            position = self.fat_history[-1]
            for color, king in self.board.king.items():
                king.castle_rights = position.castle_rights[color]

        # Next turn, updating valid moves
        self.turn = last_move.piece.color
        self.board.update_pieces_vm()