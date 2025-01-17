from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QPushButton, QMessageBox

from game_logic import GameLogic


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sliding Solver")
        self.setGeometry(100, 100, 400, 400)

        # 初始化棋盘逻辑
        self.game = GameLogic(size=3)
        self.game.generate_board()

        # 创建主窗口小部件和布局
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.grid_layout = QGridLayout()
        central_widget.setLayout(self.grid_layout)

        # 加载棋盘状态到界面
        self.load_board()

    def load_board(self):
        # 清空
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # 遍历棋盘添加按钮
        for i, row in enumerate(self.game.board):
            for j, num in enumerate(row):
                if num == 0:
                    continue
                button = QPushButton(str(num))
                button.clicked.connect(lambda _, x=i, y=j: self.handle_move(x, y))
                self.grid_layout.addWidget(button, i, j)

    def handle_move(self, x, y):
        # 计算点击的按钮与空格的相对位置
        empty_x, empty_y = self.game.empty_pos
        direction = (x - empty_x, y - empty_y)

        if direction in GameLogic.directions.values():
            self.game.move(direction)
            self.load_board()

            # 检查是否完成
            if self.game.is_solved():
                QMessageBox.information(self, "Victory", "Congratulations! You solved the puzzle!")
