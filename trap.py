

from bonus import Bonus


class Trap(Bonus):

    LETTER = "t"

    def __init__(self, board, color, square):

        Bonus.__init__(self, board, color, square)

        self.state = 0  # 0 : trap , 1 : cage , 2 : destroyed
        # self.cage = Cage(self)

    def handle_allycapture(self, capturer):

        super().handle_allycapture(capturer)

        capture = "capture", capturer,
        return capture,
