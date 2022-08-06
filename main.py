

# BAOPIG TODOs :
# Remove print("baopig from WIP")
# Dialog.handle_answer(answer)
# When a button is resized, update the text size


import os
os.chdir(os.path.dirname(os.path.realpath(__file__)))  # executable from console
# import sys
# sys.path.insert(0, 'C:\\Users\\symrb\\Documents\\python\\baopig')
import baopig as bp
load = bp.image.load
from scenes import MenuScene, GameScene
from game import Game
from board import BoardDisplay
from chessboard import ChessBoard
from iratusboard import IratusBoard
from dog import EnragedDog


iratus_theme = bp.Theme()
iratus_theme.set_style_for(bp.Button, background_color=(18, 185, 18), padding=(3, 5))
iratus_theme.set_style_for(bp.Text, font_file="pierceroman", font_height=30, font_bold=True)
iratus_theme.set_style_for(bp.DialogFrame, pos=("50%", 10), loc="midtop", width="90%")
iratus_theme.set_style_for(bp.DialogAnswerButton, width=500)


class QuitGameDialog(bp.Dialog):

    def __init__(self, app):
        bp.Dialog.__init__(self, app, title="Do you really want to quit this game ?", choices=("Yes", "Nope"))

    def handle_answer(self, answer):
        if answer == "Yes":
            self.application.new_game()


class IratusApp(bp.Application):

    def __init__(self):

        bp.Application.__init__(self, theme=iratus_theme, size=(960, 640))

        self.images = {}

        for p in ("p", "r", "n", "b", "q", "k") + ("d", "ed", "l", "t", "c", "s"):
            for c in ("w", "b"):
                self.images[c+p] = load("Images/"+c+p+".png")

        self.chess_scene = GameScene(self, board_class=ChessBoard, name="ChessScene")
        self.iratus_scene = GameScene(self, board_class=IratusBoard, name="IratusScene")
        iratus_promotion_choices = BoardDisplay.STYLE["promotion_choices"].copy()
        iratus_promotion_choices["Enraged Dog"] = EnragedDog
        self.iratus_scene.set_style_for(BoardDisplay, background_image=bp.image.load("Images/iratusboard.png"),
                                        promotion_choices=iratus_promotion_choices)
        self.menu_scene = MenuScene(self)

        self.quit_game_dialog = QuitGameDialog(self)

    current_game = property(lambda self: self.focused_scene.current_game)

    def new_game(self):  # TODO : a better game management -> close ?

        self.focused_scene.current_game = Game(self.focused_scene)


iratus_app = IratusApp()


if __name__ == "__main__":
    iratus_app.launch()
