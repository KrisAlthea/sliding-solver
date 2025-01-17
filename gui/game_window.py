from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout, QDialog, QTextEdit
import copy

from game_logic import GameLogic
from gui.select_size_dialog import SelectSizeDialog


class GameWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget

        # 准备存储解题过程
        self.solution_states = None # 存放所有中间状态
        self.solution_moves = None  # 存放移动方向
        self.current_step_index = 0

        self.init_ui()

    def init_ui(self):

        layout = QHBoxLayout()

        # 按钮：返回主菜单
        btn_back = QPushButton("Return Main")
        btn_back.clicked.connect(self.go_back)
        layout.addWidget(btn_back)

        # 初始化棋盘逻辑
        self.game = GameLogic(size=3)
        self.game.generate_board()

        # 棋盘区域
        self.grid_layout = QGridLayout()
        layout.addLayout(self.grid_layout)

        # 加载棋盘状态到界面
        self.load_board()

        # 右侧功能按钮及展示区
        self.qvbox_layout = QVBoxLayout()
        layout.addLayout(self.qvbox_layout)

        # 解答按钮
        btn_solve = QPushButton("Solve")
        btn_solve.clicked.connect(self.solve_puzzle)
        self.qvbox_layout.addWidget(btn_solve)

        # 新增按钮: 上一步/下一步
        self.btn_prev = QPushButton("⬅️")  # 上一步
        self.btn_prev.clicked.connect(self.show_previous_step)
        self.btn_next = QPushButton("➡️")  # 下一步
        self.btn_next.clicked.connect(self.show_next_step)

        # 初始禁用，等拿到解题结果后再启用
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.qvbox_layout.addWidget(self.btn_prev)
        self.qvbox_layout.addWidget(self.btn_next)

        # 步骤展示区(比如用QTextEdit，或者QLabel等都行)
        self.steps_display = QTextEdit()
        self.steps_display.setReadOnly(True)
        self.qvbox_layout.addWidget(self.steps_display)

        # 设置棋盘按钮
        btn_set_size = QPushButton("Set Size")
        btn_set_size.clicked.connect(self.set_size)
        self.qvbox_layout.addWidget(btn_set_size)

        self.setLayout(layout)

    def load_board(self):
        """
        从 self.game.board 里读取并刷新UI。
        """
        # 清空之前的格子
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

    def load_state(self, board_2d):
        """
        直接使用传入的棋盘状态(二位列表)刷新UI。
        """
        # 清空UI
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # 按照 board_2d 布局，逐个放置按钮
        for i, row in enumerate(board_2d):
            for j, num in enumerate(row):
                if num == 0:
                    continue
                button = QPushButton(str(num))
                # 这里的点击事件可要可不要，因为处于“演示模式”时，未必需要再点移动
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
        """
        点击 Solve 后：
        1) 用 A* 求解, 拿到移动方向
        2) 基于移动方向，生成所有中间状态存进 self.solution_states
        3) 在文本区域显示步骤
        4) 启用 “上一/下一步” 按钮
        """
        self.solution_moves = self.game.solve()  # A* 返回的移动方向列表
        if not self.solution_moves:
            QMessageBox.information(self, "Solution", "No solution found or already solved.")
            return

        # 生成所有中间状态
        temp_game = copy.deepcopy(self.game)  # 复制当前游戏
        self.solution_states = []
        self.solution_states.append(copy.deepcopy(temp_game.board))  # 初始状态

        for mv in self.solution_moves:
            temp_game.move(GameLogic.directions[mv])
            self.solution_states.append(copy.deepcopy(temp_game.board))

        # 在文本区域显示步骤(带序号)
        steps_text = ""
        for i, mv in enumerate(self.solution_moves, start=1):
            steps_text += f"{i}. {mv}\n"
        self.steps_display.setText(steps_text)

        # 重置索引到开头, 并启用按钮
        self.current_step_index = 0
        self.btn_prev.setEnabled(False)  # 刚开始不能再往前
        self.btn_next.setEnabled(True)   # 可以往后
        # 显示当前(第0步)状态
        self.load_state(self.solution_states[self.current_step_index])

    def show_previous_step(self):
        """
        上一步
        """
        if self.solution_states is None:
            return

        if self.current_step_index > 0:
            self.current_step_index -= 1
            self.load_state(self.solution_states[self.current_step_index])
            self.btn_next.setEnabled(True)

        # 如果已经到最开头，就禁用 '上一步'
        if self.current_step_index == 0:
            self.btn_prev.setEnabled(False)

    def show_next_step(self):
        """
        下一步
        """
        if self.solution_states is None:
            return

        if self.current_step_index < len(self.solution_states) - 1:
            self.current_step_index += 1
            self.load_state(self.solution_states[self.current_step_index])
            self.btn_prev.setEnabled(True)

        # 如果到达最后一步，就禁用 '下一步'
        if self.current_step_index == len(self.solution_states) - 1:
            self.btn_next.setEnabled(False)

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