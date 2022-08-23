from piece import Piece, PieceWidget


class BonusWidget(PieceWidget):

    LAYER = "back_layer"


class Bonus(Piece):

    WIDGET_CLASS = BonusWidget

    def __init__(self, board, color, square):

        Piece.__init__(self, board, color, square)

        self._ally = None

    ally = property(lambda self: self._ally)
    is_availible = property(lambda self: self._ally is None)

    def _handle_ally_widget_motion(self):

        if self.widget.is_awake:
            self.widget.set_pos(topleft=self._ally.widget.rect.topleft)
            self.widget.motion_end = self.widget.motion_pos = self.widget.rect.topleft

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
