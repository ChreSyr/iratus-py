

from mainpiece import MainPiece
from dog import EnragedDog


class Leash(MainPiece):

    LETTER = "l"
    moves = ((-1, -1), (1, -1), (1, 1), (-1, 1))  # , (-2, -2), (2, -2), (2, 2), (-2, 2))

    def __init__(self, board, color, square, dog):

        MainPiece.__init__(self, board, color, square)

        assert dog.leash is None

        self.dog = dog
        dog.leash = self

    def capture(self, capturer):

        commands = super().capture(capturer)
        if not self.dog.is_captured:
            dog_enrage = "transform", self.dog, EnragedDog
            if commands is None:
                commands = dog_enrage,
            else:
                commands = commands + (dog_enrage,)
        return commands

    def go_to(self, square):

        start_square = self.square
        commands = super().go_to(square)

        if (abs(self.square % 10 - self.dog.square % 10) > 1) or (abs(self.square // 10 - self.dog.square // 10) > 1):
            dog_pull = "after_move", self.dog.square, start_square
            return commands + (dog_pull,)

        return commands
