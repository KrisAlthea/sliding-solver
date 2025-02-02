from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QDialog, QApplication, QMessageBox


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
        btn_exit = QPushButton("Exit")

        layout.addWidget(btn_start)
        layout.addWidget(btn_exit)

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

