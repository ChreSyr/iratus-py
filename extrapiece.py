
from piece import Piece, PieceWidget


class ExtraPieceWidget(PieceWidget):

    LAYER = "back_layer"


class ExtraPiece(Piece):

    WIDGET_CLASS = ExtraPieceWidget

    def __init__(self, board, color, square):

        Piece.__init__(self, board, color, square)

        self._mainpiece = None

    # 0 mean empty, 1 mean attached to a mainpieceused
    # For board position (3 times repeat)
    state = property(lambda self: 1 if self._mainpiece else 0)

    def can_equip(self, mainpiece):
        """ Return True if the mainpiece can be attached to this extrapiece """

    def copy(self, original):

        self.is_captured = original.is_captured
        if self.is_captured:
            return

        if self.square != original.square:
            self.go_to(original.square)


class Bonus(ExtraPiece):

    ally = property(lambda self: self._mainpiece)
    is_availible = property(lambda self: self._mainpiece is None)

    def _handle_ally_widget_motion(self):

        if self.widget.is_awake:
            self.widget.set_pos(topleft=self.ally.widget.rect.topleft)
            self.widget.motion_end = self.widget.motion_pos = self.widget.rect.topleft

    def can_equip(self, mainpiece):

        if self.is_captured:
            return False
        if not self.is_availible:
            return False
        return self.color == mainpiece.color

    def handle_allycapture(self, capturer):

        return ("set_bonus", self.ally, self, None),

        self.is_captured = True

        if self.widget is not None:
            self.widget.sleep()

    def handle_allyuncapture(self):

        self.is_captured = False

        if self.widget is not None:
            self.widget.wake()

    def handle_collision(self, mainpiece):
        """ Handle when a piece walks on this extrapiece """

    def set_ally(self, piece):

        if self.ally is not None and self.ally.widget is not None:
            self.ally.widget.signal.MOTION.disconnect(self._handle_ally_widget_motion)
        self._mainpiece = piece
        if piece is not None and piece.widget is not None:
            piece.widget.signal.MOTION.connect(self._handle_ally_widget_motion, owner=self.widget)

    def update_ally_vm(self):
        """ Upadte self.ally.valid_moves or antiking_squares """


class MalusWidget(ExtraPieceWidget):

    LAYER = "front_layer"


class Malus(ExtraPiece):

    WIDGET_CLASS = MalusWidget

    victim = property(lambda self: self._mainpiece)

    def _handle_victim_widget_motion(self):

        if self.widget.is_awake:
            self.widget.set_pos(topleft=self._mainpiece.widget.rect.topleft)
            self.widget.motion_end = self.widget.motion_pos = self.widget.rect.topleft

    def can_equip(self, mainpiece):

        return False

    def handle_victimcapture(self, capturer):
        """ Called from victim.capture() """

    def set_victim(self, piece):

        if self.victim is not None and self.victim.widget is not None:
            self.victim.widget.signal.MOTION.disconnect(self._handle_victim_widget_motion)
        self._mainpiece = piece
        if piece is not None and piece.widget is not None:
            piece.widget.signal.MOTION.connect(self._handle_victim_widget_motion, owner=self.widget)

        self.is_captured = self.victim is None

        if self.widget:
            if self.is_captured:
                self.widget.hide()
            else:
                self.widget.show()

        if piece is not None:
            self.go_to(piece.square)

    def update_victim_vm(self):
        """ Upadte self.victim.valid_moves or antiking_squares """
