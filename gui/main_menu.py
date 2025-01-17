from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QApplication, QDialog

from gui.game_window import GameWindow
from gui.select_size_dialog import SelectSizeDialog


class MainMenu(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # 创建布局
        layout = QVBoxLayout()

        title = QLabel("Sliding Solver")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        start_button = QPushButton("Start Game")
        start_button.clicked.connect(self.start_game)
        layout.addWidget(start_button)

        custom_button = QPushButton("Customize Board")
        custom_button.clicked.connect(self.custom_board)
        layout.addWidget(custom_button)

        history_button = QPushButton("History")
        history_button.clicked.connect(self.view_history)
        layout.addWidget(history_button)

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.exit_game)
        layout.addWidget(exit_button)

        self.setLayout(layout)

    def start_game(self):
        # 选择棋盘大小
        dialog = SelectSizeDialog()
        if dialog.exec_() == QDialog.Accepted:
            size = dialog.get_selected_size()
            self.main_window.switch_to_game(size)

    def custom_board(self):
        print("Customize Board clicked!")

    def view_history(self):
        print("View History clicked!")

    def exit_game(self):
        QApplication.quit()