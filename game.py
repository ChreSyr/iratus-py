import baopig as bp


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
        # self.counter50rule = 0

        # w is white won, b is black won, d is drawn
        self.result = None

        # If True, flip the board at each move
        self.always_flip = False

        # Initializing pieces valid moves
        for piece in self.board.set[self.turn]:
            piece.update_valid_moves()

        # Initializing board and pieces display
        self.board.init_display(scene)

        # Store the first position
        self.fat_history.append(self.board.get_position())

    def check_for_end(self):

        game_state = self.get_game_state()

        if game_state == "checkmate":
            self.history[-1].notation += "#"
        elif self.board.king[self.turn].in_check:
            self.history[-1].notation += "+"

        # TODO : cage, compact edog notation

        if game_state in ("checkmate", "stalemate",
                          "draw by repetition", "draw by insufficient material", "draw by 50-moves rule"):
            description = ""
            if game_state == "checkmate":
                last_move = self.history[-1]
                winner = "Black" if last_move.turn == "b" else "White"
                description = winner + " won"
            end_dialog = bp.Dialog(self.app, one_shot=True, title=game_state.capitalize(), description=description,
                                   choices=("That was a real good game",))
            bp.Timer(.2, end_dialog.open).start()

    def get_game_state(self):

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
                return "draw by repetition"

        game_state = "keep going"

        for piece in self.board.set[self.turn]:
            if not piece.is_captured and piece.valid_moves:
                # Still at least one valid move

                if self.history:
                    if self.history[-1].counter50rule > 50:
                        return "draw by 50-moves rule"

                return game_state

        # No more move : checkmate or stalemate
        if self.board.king[self.turn].in_check:
            return "checkmate"
        else:
            return "stalemate"

    def move(self, start_square, end_square):

        piece = self.board[start_square]
        assert piece.color is self.turn

        move = self.board.move(start_square, end_square)
        self.history.append(move)  # piece, old_square, square, captured_piece

        # Next turn
        # For the color who just played, we need to update the antiking squares
        self.turn = move.next_turn

        # We need to update the antiking squares for both colors
        self.board.update_pieces_vm()

        # This occurs after the valid moves update because we need the castling rights
        self.fat_history.append(self.board.get_position())
        self.back_history.clear()

        if self.always_flip:
            if move.turn != move.next_turn:
                self.board.display.flip(animate=False)

        self.check_for_end()

    def redo(self):
        """
        Redo the last undone move
        """

        if len(self.back_history) == 0:
            return

        last_undone_move = self.back_history.pop(-1)
        piece = self.board[last_undone_move.start_square]

        assert piece.color is self.turn

        self.board.redo(last_undone_move)
        self.history.append(last_undone_move)

        self.turn = last_undone_move.next_turn

        self.board.update_pieces_vm()

        # This occurs after the valid moves update because we need the castling rights
        self.fat_history.append(self.board.get_position())

        if self.always_flip:
            if last_undone_move.turn != last_undone_move.next_turn:
                self.board.display.flip(animate=False)

    def undo(self):
        """
        Undo the last move
        """

        if len(self.history) == 0:
            return

        last_move = self.history.pop(-1)
        self.fat_history.pop(-1)
        self.back_history.append(last_move)

        self.board.undo(last_move)

        # if self.fat_history:
        #     position = self.fat_history[-1]
        #     for color, king in self.board.king.items():
        #         king.castle_rights = position.castle_rights[color]

        # Next turn, updating valid moves
        self.turn = last_move.turn
        self.board.update_pieces_vm()

        if self.always_flip:
            if last_move.turn != last_move.next_turn:
                self.board.display.flip(animate=False)
