from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout, QDialog

from game_logic import GameLogic
from gui.select_size_dialog import SelectSizeDialog


class GameWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):

        layout = QHBoxLayout()

        # 添加返回按钮
        btn_back = QPushButton("Return Main")
        btn_back.clicked.connect(self.go_back)
        layout.addWidget(btn_back)

        # 初始化棋盘逻辑
        self.game = GameLogic(size=3)
        self.game.generate_board()

        # 添加棋盘
        self.grid_layout = QGridLayout()
        layout.addLayout(self.grid_layout)

        # 加载棋盘状态到界面
        self.load_board()

        # 右侧功能按钮
        self.qvbox_layout = QVBoxLayout()
        layout.addLayout(self.qvbox_layout)

        # 解答按钮
        btn_solve = QPushButton("Solve")
        btn_solve.clicked.connect(self.solve_puzzle)
        self.qvbox_layout.addWidget(btn_solve)

        # 设置棋盘按钮
        btn_set_size = QPushButton("Set Size")
        btn_set_size.clicked.connect(self.set_size)
        self.qvbox_layout.addWidget(btn_set_size)

        self.setLayout(layout)

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

    def solve_puzzle(self):
        solution = self.game.solve()
        if solution:
            QMessageBox.information(self, "Solution", f"Steps to solve:\n{solution}")

    def set_size(self):
        # 选择棋盘大小
        dialog = SelectSizeDialog()
        if dialog.exec_() == QDialog.Accepted:
            size = dialog.get_selected_size()

            # 更新棋盘逻辑
            self.game.size = size
            self.game.generate_board()

            # 重新加载棋盘
            self.load_board()

    def go_back(self):
        self.stacked_widget.setCurrentIndex(0)