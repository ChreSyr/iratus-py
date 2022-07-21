

import os
os.chdir(os.path.dirname(os.path.realpath(__file__)))  # executable from console
# import sys
# sys.path.insert(0, 'C:\\Users\\symrb\\Documents\\python\\baopig')
import baopig as bp
load = bp.image.load
from scenes import ChessScene, IratusScene, MenuScene
from chessgame import ChessGame
from iratusgame import IratusGame


iratus_theme = bp.Theme()
iratus_theme.set_style_for(bp.Button, background_color=(18, 185, 18), padding=(3, 5))
iratus_theme.set_style_for(bp.Text, font_file="pierceroman", font_height=30, font_bold=True)
iratus_theme.set_style_for(bp.DialogFrame, pos=("50%", 10), loc="midtop", width="90%")


class IratusApp(bp.Application):

    def __init__(self):

        bp.Application.__init__(self, theme=iratus_theme)

        self.set_default_size((960, 640))

        self.images = {"chessboard": load("Images/" + "chessboard.png"),
                       "iratusboard": load("Images/" + "iratusboard.png")}

        for p in ("p", "r", "n", "b", "q", "k") + ("d", "ed", "l", "t", "c", "s"):
            for c in ("w", "b"):
                self.images[c+p] = load("Images/"+c+p+".png")

        self.iratus_scene = IratusScene(self)
        self.chess_scene = ChessScene(self)
        self.menu_scene = MenuScene(self)

        self.quit_game_dialog = bp.Dialog(self, title="Do you really want to quit this game ?",
                                          choices=("Yes", "Nope"))
        def answer(ans):
            if ans == "Yes":
                self.new_game()
        self.quit_game_dialog.signal.ANSWERED.connect(answer, owner=None)

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
