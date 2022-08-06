

import baopig as bp


class GameScene(bp.Scene):

    def __init__(self, app, board_class, name):

        bp.Scene.__init__(self, app, can_select=False, name=name)

        self.board_class = board_class
        self.current_game = None

        GameButtonsZone(self)

    def handle_scene_open(self):

        # TODO : remove this in the final version
        if self.current_game is None:
            self.application.new_game()

    def receive(self, event):

        # TODO : remove this in the final version
        if event.type is bp.KEYDOWN:
            b = self.current_game.board
            print(2)  # made for debugging


class GameButtonsZone(bp.Zone):

    def __init__(self, scene):

        bp.Zone.__init__(self, scene, size=(140, "100%"), background_color="gray")

        bp.GridLayer(self, row_height=50, col_width=120, nbcols=1, spacing=10, padding=10)

        bp.Button(self, text="Menu", row=0, loc="center",
                  command=bp.PrefilledFunction(self.application.open, "MenuScene"))

        def new_game():
            if self.application.current_game is not None:
                self.application.quit_game_dialog.open()
            else:
                self.application.new_game()
        bp.Button(self, text="New Game", row=1, loc="center", command=new_game)

        def undo():
            self.application.current_game.undo()
        bp.Button(self, text="Undo", row=2, loc="center", command=undo)

        def redo():
            self.application.current_game.redo()
        bp.Button(self, text="Redo", row=3, loc="center", command=redo)

        def flip():
            self.application.current_game.board.display.flip()
        bp.Button(self, text="Flip board", row=4, loc="center", command=flip)

        def print_game():
            moves = []
            turn = None
            turn_number = 0
            for move in self.scene.application.current_game.history:
                try:
                    new_turn_number = int(move.turn_number)
                    if new_turn_number != turn_number:
                        turn_number = new_turn_number
                        moves.append(str(turn_number) + ".")

                    if turn != move.turn:
                        moves.append(move.notation)
                    else:
                        moves[-1] = moves[-1] + "-" + move.notation
                    turn = move.turn

                except AttributeError:
                    pass
            bp.Dialog(self.application, title="Current game :", description=' '.join(moves), choices=("Thanks",),
                      one_shot=True).open()
        bp.Button(self, text="Print game", row=5, loc="center", command=print_game)


class MenuScene(bp.Scene):

    def __init__(self, application):

        bp.Scene.__init__(self, application, can_select=False)

        MenuButtonsZone(self)


class MenuButtonsZone(bp.Zone):

    def __init__(self, scene):

        bp.Zone.__init__(self, scene, size=(140, "100%"), background_color="gray")

        bp.GridLayer(self, row_height=50, col_width=120, nbcols=1, spacing=10, padding=10)

        bp.Button(self, text="Play chess", row=0, loc="center",
                  command=bp.PrefilledFunction(self.application.open, "ChessScene"))

        bp.Button(self, text="Play iratus", row=1, loc="center",
                  command=bp.PrefilledFunction(self.application.open, "IratusScene"))
