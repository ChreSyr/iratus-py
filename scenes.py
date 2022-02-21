

import baopig as bp


class ChessScene(bp.Scene):

    def __init__(self, app):

        bp.Scene.__init__(self, app)
        self.set_selectionrect_visibility(False)

        self.current_game = None

        GameButtonsZone(self)

    def receive(self, event):

        if event.type is bp.KEYDOWN:
            print(2)


class IratusScene(bp.Scene):

    def __init__(self, app):

        bp.Scene.__init__(self, app)
        self.set_selectionrect_visibility(False)

        self.current_game = None

        GameButtonsZone(self)

    def open(self):

        # TODO : remove this in the final version
        if self.current_game is None:
            self.app.new_game()

    def receive(self, event):

        if event.type is bp.KEYDOWN:
            b = self.current_game.board
            print(2)


class GameButtonsZone(bp.Zone):

    def __init__(self, scene):

        bp.Zone.__init__(self, scene, size=(140, "100%"), background_color = "gray")

        bp.GridLayer(self, row_height=60, col_width=140, nbcols=1)

        bp.Button(self, text="Menu", row=0, sticky="center",
                  command=bp.PrefilledFunction(self.app.open, "MenuScene"))

        def new_game():
            if self.app.current_game is not None:
                self.app.quit_game_dialog.open()
            else:
                self.app.new_game()
        bp.Button(self, text="New Game", row=1, sticky="center", command=new_game)

        def undo():
            self.scene.app.current_game.undo()
        bp.Button(self, text="Undo", row=2, sticky="center", command=undo)

        def redo():
            self.scene.app.current_game.redo()
        bp.Button(self, text="Redo", row=3, sticky="center", command=redo)

        def flip():
            self.scene.app.current_game.board.display.flip()
        bp.Button(self, text="Flip board", row=4, sticky="center", command=flip)

        def print_game():
            game = self.scene.app.current_game
            for move in game.history:
                try:
                    print(move.notation, end=" ")
                except AttributeError:
                    print()
            print()
        bp.Button(self, text="Print game in console", row=5, sticky="center", command=print_game)


class MenuScene(bp.Scene):

    def __init__(self, app):

        bp.Scene.__init__(self, app)

        MenuButtonsZone(self)


class MenuButtonsZone(bp.Zone):

    def __init__(self, scene):

        bp.Zone.__init__(self, scene, size=(140, "100%"), background_color = "gray")

        bp.GridLayer(self, row_height=60, col_width=140, nbcols=1)

        bp.Button(self, text="Play chess", row=0, sticky="center",
                  command=bp.PrefilledFunction(self.app.open, "ChessScene"))

        bp.Button(self, text="Play iratus", row=1, sticky="center",
                  command=bp.PrefilledFunction(self.app.open, "IratusScene"))
