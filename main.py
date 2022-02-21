

import baopig as bp
from scenes import ChessScene, IratusScene, MenuScene
from chessgame import ChessGame
from iratusgame import IratusGame


iratus_theme = bp.Theme()
iratus_theme.set_style_for(bp.Button, background_color="green")
iratus_theme.set_style_for(bp.Text, font_file="Skia", font_height=35)
iratus_theme.set_style_for(bp.DialogFrame, pos=("50%", 10), pos_location="midtop", width="90%")


class IratusApp(bp.Application):

    def __init__(self):

        bp.Application.__init__(self, theme=iratus_theme)

        self.set_default_size((960, 640))

        # self.images = {"chessboard": bp.transform.scale(bp.image.load("Images/" + "chessboard.png"), (512, 512)),
        #                "iratusboard": bp.transform.scale(bp.image.load("Images/" + "iratusboard.png"), (512, 640))}

        self.images = {"chessboard": bp.image.load("Images/" + "chessboard.png"),
                       "iratusboard": bp.image.load("Images/" + "iratusboard.png")}

        for p in ("p", "r", "n", "b", "q", "k") + ("d", "ed", "l", "t", "c", "s"):
            for c in ("w", "b"):
                # self.images[c+p] = bp.transform.scale(bp.image.load("Images/"+c+p+".png"), (64, 64))
                self.images[c+p] = bp.image.load("Images/"+c+p+".png")

        self.iratus_scene = IratusScene(self)
        self.chess_scene = ChessScene(self)
        self.menu_scene = MenuScene(self)

        self.quit_game_dialog = bp.Dialog(self, title="Do you really want to quit this game ?",
                                          choices=("Yes", "Nope"))
        def answer(ans):
            if ans == "Yes":
                self.new_game()
        self.quit_game_dialog.signal.ANSWERED.connect(answer)

    current_game = property(lambda self: self.focused_scene.current_game)

    def react_quit_game_dialog(self, ans):
        if ans == "Yes":
            self.new_game()

    def new_game(self):  # TODO : a better game management

        if self.focused_scene is self.chess_scene:
            self.focused_scene.current_game = ChessGame(self)
        elif self.focused_scene is self.iratus_scene:
            self.focused_scene.current_game = IratusGame(self)


iratus_app = IratusApp()


if __name__ == "__main__":
    iratus_app.launch()
