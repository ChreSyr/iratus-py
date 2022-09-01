
from piece import Piece, PieceWidget


class ExtraPieceWidget(PieceWidget):

    LAYER = "back_layer"


class ExtraPiece(Piece):

    WIDGET_CLASS = ExtraPieceWidget

    def can_equip(self, mainpiece):
        """ Return True if the mainpiece can be attached to this extrapiece """


class Bonus(ExtraPiece):

    def __init__(self, board, color, square):

        ExtraPiece.__init__(self, board, color, square)

        self._ally = None

    ally = property(lambda self: self._ally)
    is_availible = property(lambda self: self._ally is None)

    def _handle_ally_widget_motion(self):

        if self.widget.is_awake:
            self.widget.set_pos(topleft=self._ally.widget.rect.topleft)
            self.widget.motion_end = self.widget.motion_pos = self.widget.rect.topleft

    def can_equip(self, mainpiece):

        if self.is_captured:
            return False
        if not self.is_availible:
            return False
        return self.color == mainpiece.color

    def handle_allycapture(self, capturer):

        self.is_captured = True

        if self.widget is not None:
            self.widget.sleep()

    def handle_allyuncapture(self):

        self.is_captured = False

        if self.widget is not None:
            self.widget.wake()

    def set_ally(self, piece):

        if self._ally is not None and self._ally.widget is not None:
            self._ally.widget.signal.MOTION.disconnect(self._handle_ally_widget_motion)
        self._ally = piece
        if piece is not None and piece.widget is not None:
            piece.widget.signal.MOTION.connect(self._handle_ally_widget_motion, owner=self.widget)

    def update_ally_vm(self):
        """ Upadte self.ally.valid_moves or antiking_squares """


class MalusWidget(ExtraPieceWidget):

    LAYER = "front_layer"


class Malus(ExtraPiece):

    WIDGET_CLASS = MalusWidget

    def __init__(self, board, color, square):

        ExtraPiece.__init__(self, board, color, square)

        self._victim = None

    victim = property(lambda self: self._victim)

    def _handle_victim_widget_motion(self):

        if self.widget.is_awake:
            self.widget.set_pos(topleft=self._victim.widget.rect.topleft)
            self.widget.motion_end = self.widget.motion_pos = self.widget.rect.topleft

    def can_equip(self, mainpiece):

        return False

    def set_victim(self, piece):

        if self._victim is not None and self._victim.widget is not None:
            self._victim.widget.signal.MOTION.disconnect(self._handle_victim_widget_motion)
        self._victim = piece
        if piece is not None and piece.widget is not None:
            piece.widget.signal.MOTION.connect(self._handle_victim_widget_motion, owner=self.widget)
