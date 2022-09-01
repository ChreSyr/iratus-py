

from extrapiece import Bonus


class Dynamite(Bonus):

    LETTER = "dy"

    def handle_allycapture(self, capturer):

        super().handle_allycapture(capturer)

        if capturer:  # False when a piece with dynamite is captured by a piece with dynamite
            capture = "capture", capturer
            return capture,

    def update_ally_vm(self):

        if self.ally.square not in self.ally.antiking_squares:
            self.ally.antiking_squares += (self.ally.square,)
