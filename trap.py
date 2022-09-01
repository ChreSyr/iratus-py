

from extrapiece import Bonus, Malus


class Trap(Bonus):

    LETTER = "t"

    def __init__(self, board, color, square):

        Bonus.__init__(self, board, color, square)

        self.state = 0  # 0 : trap , 1 : cage , 2 : destroyed
        self.cage = Cage(self)
        # self.cage.is_captured = True

    def handle_allycapture(self, capturer):

        super().handle_allycapture(capturer)

        if capturer:  # False when the capturer got dynamited
            lock_up = "set_malus", capturer, self.cage
            return lock_up,

    def init_display(self):

        super().init_display()
        self.cage.init_display()
        self.cage.widget.hide()


class Cage(Malus):

    LETTER = "c"

    def __init__(self, trap):

        Malus.__init__(self, trap.board, trap.color, trap.square)
        self.trap = trap

    def set_victim(self, piece):

        super().set_victim(piece)

        self.is_captured = self.victim is None
        if not self.is_captured:
            self.go_to(piece.square)

        if self.widget:
            if self.is_captured:
                self.widget.hide()
            else:
                self.widget.show()
