

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

        super().capture(capturer)
        if not self.dog.is_captured:
            dog_enrage = "transform", self.dog, EnragedDog
            return dog_enrage,

    def go_to(self, square):

        start_square = self.square
        super().go_to(square)

        if (abs(self.square % 10 - self.dog.square % 10) > 1) or (abs(self.square // 10 - self.dog.square // 10) > 1):
            dog_pull = "after_move", self.dog.square, start_square
            return dog_pull,
