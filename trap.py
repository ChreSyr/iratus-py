

from extrapiece import Bonus, Malus


class Trap(Bonus):

    LETTER = "t"

    def __init__(self, board, color, square):

        Bonus.__init__(self, board, color, square)

        self.cage = Cage(self)
        # self.cage.is_captured = True

    def handle_allycapture(self, capturer):

        return

        super().handle_allycapture(capturer)

        if capturer:  # False when the capturer got dynamited
            lock_up = "set_malus", capturer, capturer.malus, self.cage
            return lock_up,

    def handle_collision(self, mainpiece):

        if mainpiece.color == self.color:
            assert mainpiece.bonus is None
            set_bonus = "set_bonus", mainpiece, None, self
            return set_bonus,
        else:
            self.is_captured = True
            if self.widget is not None:
                self.widget.sleep()

            assert mainpiece.malus is None
            set_malus = "set_malus", mainpiece, None, self.cage
            return set_malus,

    def init_display(self):

        super().init_display()
        self.cage.init_display()
        self.cage.widget.hide()


class Cage(Malus):

    LETTER = "c"

    def __init__(self, trap):

        Malus.__init__(self, trap.board, trap.color, trap.square)
        self.trap = trap
        self.is_captured = True

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

    def update_victim_vm(self):
        self.victim.valid_moves = ()
        self.victim.antiking_squares = ()
