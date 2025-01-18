from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout, QDialog, \
    QTextEdit, QLabel, QFrame
from PyQt5.QtCore import QTimer
import copy
import time

from game_logic import GameLogic
from gui.customize_dialog import CustomizeGameDialog
from gui.select_size_dialog import SelectSizeDialog


class GameWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.game = None
        self.stacked_widget = stacked_widget
        self.start_time = 0
        self.step_count = 0
        # 准备存储解题过程
        self.solution_states = None # 存放所有中间状态
        self.solution_moves = None  # 存放移动方向
        self.current_step_index = 0

        self.init_ui()

    def init_ui(self):

        layout = QVBoxLayout()

        top_bar_layout = QHBoxLayout()
        game_layout = QHBoxLayout()
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        layout.addLayout(top_bar_layout)
        layout.addWidget(divider)
        layout.addLayout(game_layout)

        # 左侧功能区
        game_layout_left = QVBoxLayout()
        game_layout.addLayout(game_layout_left)
        # 棋盘区域
        self.grid_layout = QGridLayout()
        game_layout.addLayout(self.grid_layout)
        # 右侧功能区
        game_layout_right = QVBoxLayout()
        game_layout.addLayout(game_layout_right)

        # 按钮：返回主菜单
        btn_back = QPushButton("Main")
        btn_back.clicked.connect(self.go_back)
        top_bar_layout.addWidget(btn_back)

        # 计步器，计时器
        self.lbl_steps = QLabel("steps: 0")
        self.lbl_time = QLabel("time: 00:00")
        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.timeout.connect(self.update_time_label)
        top_bar_layout.addWidget(self.lbl_steps)
        top_bar_layout.addWidget(self.lbl_time)
        # 解答按钮
        btn_solve = QPushButton("Solve")
        btn_solve.clicked.connect(self.solve_puzzle)
        top_bar_layout.addWidget(btn_solve)

        # 按钮: 设置棋盘大小
        btn_set_size = QPushButton("Set Size")
        btn_set_size.clicked.connect(self.set_size)
        game_layout_left.addWidget(btn_set_size)

        # 按钮: 自定义棋盘
        btn_customize = QPushButton("Customize")
        btn_customize.clicked.connect(self.customize)
        game_layout_left.addWidget(btn_customize)

        # 初始化棋盘逻辑
        self.game = GameLogic(size=3)
        self.game.generate_board()
        # 加载棋盘状态到界面
        self.load_board()

        # 按钮: 上一步/下一步
        self.btn_prev = QPushButton("◀️")  # 上一步
        self.btn_prev.clicked.connect(self.show_previous_step)
        self.btn_next = QPushButton("▶️")  # 下一步
        self.btn_next.clicked.connect(self.show_next_step)

        # 初始禁用，等拿到解题结果后再启用
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)
        game_layout_right.addWidget(self.btn_prev)
        game_layout_right.addWidget(self.btn_next)

        # 步骤展示区(比如用QTextEdit，或者QLabel等都行)
        self.steps_display = QTextEdit()
        self.steps_display.setReadOnly(True)
        game_layout_right.addWidget(self.steps_display)

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
            success = self.game.move(direction)
            if success:
                self.step_count += 1
                # 走第一步同时开始计时
                if self.step_count == 1:
                    self.start_time = time.time()
                    self.elapsed_timer.start(1000)  # 每 1 秒触发一次 update_time_label
                    self.lbl_time.setText("time: 00:00")
                self.lbl_steps.setText(f"steps: {self.step_count}")
            self.load_board()
            # 检查是否完成
            if self.game.is_solved():
                self.elapsed_timer.stop()
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
        self.elapsed_timer.stop()
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

            # 重新计步
            self.step_count = 0
            # 重新加载棋盘
            self.load_board()

    def go_back(self):
        self.stacked_widget.setCurrentIndex(0)

    def customize(self):
        # 弹出一个自定义对话框
        dialog = CustomizeGameDialog()
        if dialog.exec_() == QDialog.Accepted:
            # 获取玩家编辑好的布局(二维列表)
            board_2d = dialog.get_custom_layout()
            # 赋值给 self.game
            self.game.board = board_2d
            # 找空格
            for i in range(self.game.size):
                for j in range(self.game.size):
                    if self.game.board[i][j] == 0:
                        self.game.empty_pos = (i, j)
                        break
            # 检查 solvable（如果对话框已经检查过，这里可略过）
            if not self.game.is_solvable():
                QMessageBox.information(self, "Error", "Puzzle is not solvable.")
            else:
                # 更新UI
                self.load_board()
                # 重新计步
                self.step_count = 0

    def update_time_label(self):
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.lbl_time.setText(f"time: {minutes:02d}:{seconds:02d}")