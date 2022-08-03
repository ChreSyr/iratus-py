

# BAOPIG TODOs :
# Remove print("baopig from WIP")


import os
os.chdir(os.path.dirname(os.path.realpath(__file__)))  # executable from console
# import sys
# sys.path.insert(0, 'C:\\Users\\symrb\\Documents\\python\\baopig')
import baopig as bp
load = bp.image.load
from scenes import MenuScene, GameScene
from game import Game
from chessboard import ChessBoard
from iratusboard import IratusBoard


iratus_theme = bp.Theme()
iratus_theme.set_style_for(bp.Button, background_color=(18, 185, 18), padding=(3, 5))
iratus_theme.set_style_for(bp.Text, font_file="pierceroman", font_height=30, font_bold=True)
iratus_theme.set_style_for(bp.DialogFrame, pos=("50%", 10), loc="midtop", width="90%")


class IratusApp(bp.Application):

    def __init__(self):

        bp.Application.__init__(self, theme=iratus_theme, size=(960, 640))

        self.images = {"chessboard": load("Images/chessboard.png"),
                       "iratusboard": load("Images/iratusboard.png")}

        for p in ("p", "r", "n", "b", "q", "k") + ("d", "ed", "l", "t", "c", "s"):
            for c in ("w", "b"):
                self.images[c+p] = load("Images/"+c+p+".png")

        self.iratus_scene = GameScene(self, board_class=IratusBoard, name="IratusScene")
        self.chess_scene = GameScene(self, board_class=ChessBoard, name="ChessScene")
        self.menu_scene = MenuScene(self)

        self.quit_game_dialog = bp.Dialog(self, title="Do you really want to quit this game ?",
                                          choices=("Yes", "Nope"))
        def answer(ans):
            if ans == "Yes":
                self.new_game()
        self.quit_game_dialog.signal.ANSWERED.connect(answer, owner=None)

    current_game = property(lambda self: self.focused_scene.current_game)

    def new_game(self):  # TODO : a better game management -> close ?

        self.focused_scene.current_game = Game(self.focused_scene)


iratus_app = IratusApp()


if __name__ == "__main__":
    iratus_app.launch()
