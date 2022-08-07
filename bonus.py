from piece import Piece, PieceWidget


class BonusWidget(PieceWidget):

    LAYER = "back_layer"


class Bonus(Piece):

    WIDGET_CLASS = BonusWidget

    def __init__(self, board, color, square):

        Piece.__init__(self, board, color, square)

        self.ally = None

    def move(self):

        if piece.trap is not None and piece.trap.trap_widget.is_hidden:
            move.unequiped_trap = piece.trap
            piece.trap.trap_widget.show()
            piece.unequip()

        # Trap stuff
        if piece.bonus is None:
            # Trap equipement
            for bonus in self.bonus[piece.color]:
                if bonus.ally is None and bonus.square == move.end_square:
                    piece.equip(bonus)
                    move.trap_equipement = True
        else:
            piece.bonus.move(move.end_square)

    def undo(self):

        if move.trap_equipement is True:
            assert piece.trap is not None
            piece.unequip()

        if move.trap_capture is True:
            assert piece.cage is not None
            piece.cage.untrap()

        if move.broken_cage is not None:
            assert move.capture.LETTER == "s"
            move.capture, piece = piece, move.capture
            move.broken_cage.unrelease(move.capture)
            # self[move.start_square] = piece
            piece.uncapture()

        ...

        if piece.trap is not None:
            piece.trap.move(move.start_square)

        if move.destroyed_trap is not None:
            assert piece.LETTER == "l"
            move.destroyed_trap.undestroy()
            if move.capture != 0:
                move.capture.equip(move.destroyed_trap)

        if move.unequiped_trap is not None:
            assert move.unequiped_trap.square is piece.square
            piece.equip(move.unequiped_trap)
