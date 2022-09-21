

from mainpiece import MainPiece, MainPieceMovingTwice


class Dog(MainPiece):

    LETTER = "d"
    moves = ((-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1))

    def __init__(self, board, color, square):

        MainPiece.__init__(self, board, color, square)

        self.leash = None

    def capture(self, capturer):

        commands = super().capture(capturer)
        if not self.leash.is_captured:
            capture = "capture", self.leash
            if commands is None:
                commands = capture,
            else:
                commands = commands + (capture,)
        return commands

    def update_valid_moves(self):

        if self.is_captured:
            return

        self.valid_moves = ()
        self.antiking_squares = ()

        x = self.leash.square // 10
        y = self.leash.square % 10
        from_dog_to_leash = self.leash.square - self.square

        for move in self.moves:

            dx, dy = move

            if not self.board.has_square(x + dx, y + dy):
                continue

            d = dx * 10 + dy
            square = self.leash.square + d
            if square not in self.board.existing_squares:
                raise AssertionError
            self.antiking_squares += (square,)

            start_square = self.square
            end_square = square
            dx = end_square // 10 - start_square // 10
            dy = end_square % 10 - start_square % 10

            if self.can_go_to(square, (dx, dy)):
                self.valid_moves += (from_dog_to_leash + d,)

        if self.bonus:
            self.bonus.update_ally_vm()
        if self.malus:
            self.malus.update_victim_vm()


class EnragedDog(MainPieceMovingTwice):

    # TODO : when an enraged dog gets trapped on first move ?
    # TODO : solve : when an enraged dog gets captured on the first move, the allies can move

    LETTER = "ed"
    moves = ((1, 0), (0, 1), (-1, 0), (0, -1))
