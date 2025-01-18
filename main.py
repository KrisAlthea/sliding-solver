import sys
from PyQt5.QtWidgets import QApplication, QStackedWidget

from gui.game_window import GameWindow
from gui.main_window import MainWindow


class App(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)

        self.stacked_widget = QStackedWidget()

        self.main_window = MainWindow(self.stacked_widget)
        self.game_window = GameWindow(self.stacked_widget)

        self.stacked_widget.addWidget(self.main_window)
        self.stacked_widget.addWidget(self.game_window)

        self.stacked_widget.setCurrentIndex(0)
        self.stacked_widget.show()

        # 加载样式表
        with open("assets/style.qss", "r") as f:
            self.setStyleSheet(f.read())

if __name__ == "__main__":
    PuzzleApp = App(sys.argv)
    sys.exit(PuzzleApp.exec_())