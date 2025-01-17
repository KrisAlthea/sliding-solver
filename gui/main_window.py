from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QDialog, QApplication

from gui.game_window import GameWindow
from gui.main_menu import MainMenu
from gui.select_size_dialog import SelectSizeDialog


class MainWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()


    def init_ui(self):
        self.setWindowTitle("Sliding Solver")

        layout = QVBoxLayout()

        title = QLabel("Sliding Solver")
        layout.addWidget(title)

        btn_start = QPushButton("Start")
        btn_customize = QPushButton("Customize")
        btn_history = QPushButton("History")
        btn_exit = QPushButton("Exit")

        layout.addWidget(btn_start)
        layout.addWidget(btn_customize)
        layout.addWidget(btn_history)
        layout.addWidget(btn_exit)

        self.setLayout(layout)

        btn_start.clicked.connect(self.start_game)
        btn_customize.clicked.connect(self.customize_game)
        btn_history.clicked.connect(self.game_history)
        btn_exit.clicked.connect(self.exit_game)

    def start_game(self):
        self.stacked_widget.setCurrentIndex(1)

    def customize_game(self):
        self.stacked_widget.setCurrentIndex(2)

    def game_history(self):
        self.stacked_widget.setCurrentIndex(3)

    def exit_game(self):
        QApplication.quit()
