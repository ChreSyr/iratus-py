

from extrapiece import Bonus


class Dynamite(Bonus):

    LETTER = "dy"

    def handle_collision(self, mainpiece):

        if mainpiece.color == self.color:
            assert mainpiece.bonus is None
            set_bonus = "set_bonus", mainpiece, None, self
            return set_bonus,
        else:
            self.is_captured = True
            if self.widget is not None:
                self.widget.sleep()

            capture = "capture", mainpiece, self
            return capture,

    def update_ally_vm(self):

        if self.ally.square not in self.ally.antiking_squares:
            self.ally.antiking_squares += (self.ally.square,)
