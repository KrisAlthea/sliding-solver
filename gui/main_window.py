from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QDialog, QApplication, QMessageBox


class MainWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()


    def init_ui(self):
        self.setWindowTitle("Sliding Solver")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)  # 居中对齐

        title = QLabel("Sliding Solver")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont("Helvetica", 24, QFont.Bold)
        title.setFont(title_font)
        layout.addWidget(title)

        btn_start = QPushButton("Start")
        btn_exit = QPushButton("Exit")
        btn_start.setFixedWidth(200)
        btn_exit.setFixedWidth(200)
        btn_font = QFont("Helvetica", 14)
        btn_start.setFont(btn_font)
        btn_exit.setFont(btn_font)

        layout.addWidget(btn_start, alignment=Qt.AlignCenter)
        layout.addWidget(btn_exit, alignment=Qt.AlignCenter)

        self.setLayout(layout)

        btn_start.clicked.connect(self.start_game)
        btn_exit.clicked.connect(self.exit_game)

    def start_game(self):
        self.stacked_widget.setCurrentIndex(1)

    def game_history(self):
        self.stacked_widget.setCurrentIndex(2)

    def exit_game(self):
        reply = QMessageBox.question(self, '确认退出', '确定要退出游戏吗？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.quit()

