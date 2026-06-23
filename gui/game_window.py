from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout, QDialog, \
    QTextEdit, QLabel, QFrame
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QKeySequence, QFont
import copy
import time

from game_logic import GameLogic
from history.recording import build_game_record
from gui.customize_dialog import CustomizeGameDialog
from gui.select_size_dialog import SelectSizeDialog


# 方向中文映射
_DIR_CN = {"up": "↑", "down": "↓", "left": "←", "right": "→"}


class GameWindow(QWidget):
    def __init__(self, stacked_widget, history_store=None):
        super().__init__()
        self.game = None
        self.history_store = history_store
        self.stacked_widget = stacked_widget
        self.start_time = 0
        self.step_count = 0
        self.session_initial_board = None
        # 解题过程存储
        self.solution_states = None
        self.solution_moves = None
        self.current_step_index = 0
        # 动画回放
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self._playback_step)
        self.is_playing = False
        # 撤销栈
        self.undo_stack = []  # [(board_2d, empty_pos), ...]
        # 最优解步数
        self.optimal_steps = None

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

        # --- 顶部栏 ---
        btn_back = QPushButton("🏠 Main")
        btn_back.clicked.connect(self.go_back)
        top_bar_layout.addWidget(btn_back)

        self.lbl_steps = QLabel("steps: 0")
        self.lbl_steps.setFont(QFont("Monospace", 11))
        self.lbl_time = QLabel("time: 00:00")
        self.lbl_time.setFont(QFont("Monospace", 11))
        self.lbl_optimal = QLabel("")
        self.lbl_optimal.setStyleSheet("color: #888; font-size: 11px;")
        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.timeout.connect(self.update_time_label)
        top_bar_layout.addWidget(self.lbl_steps)
        top_bar_layout.addWidget(self.lbl_time)
        top_bar_layout.addWidget(self.lbl_optimal)

        btn_solve = QPushButton("🔍 Solve")
        btn_solve.clicked.connect(self.solve_puzzle)
        top_bar_layout.addWidget(btn_solve)

        # --- 左侧按钮 ---
        btn_set_size = QPushButton("📐 Set Size")
        btn_set_size.clicked.connect(self.set_size)
        game_layout_left.addWidget(btn_set_size)

        btn_customize = QPushButton("✏️ Customize")
        btn_customize.clicked.connect(self.customize)
        game_layout_left.addWidget(btn_customize)

        btn_undo = QPushButton("↩️ Undo")
        btn_undo.setShortcut(QKeySequence("Ctrl+Z"))
        btn_undo.clicked.connect(self.undo_move)
        game_layout_left.addWidget(btn_undo)

        btn_reset = QPushButton("🔄 Reset")
        btn_reset.clicked.connect(self.reset_board)
        game_layout_left.addWidget(btn_reset)

        # --- 初始化棋盘 ---
        self.game = GameLogic(size=3)
        self.game.generate_board()
        self.load_board()
        self.session_initial_board = copy.deepcopy(self.game.board)

        # --- 右侧控制 ---
        # 回放控制栏
        playback_layout = QHBoxLayout()
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFixedWidth(40)
        self.btn_prev.clicked.connect(self.show_previous_step)
        self.btn_prev.setEnabled(False)

        self.btn_play = QPushButton("▶ Play")
        self.btn_play.setFixedWidth(70)
        self.btn_play.clicked.connect(self.toggle_playback)
        self.btn_play.setEnabled(False)

        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedWidth(40)
        self.btn_next.clicked.connect(self.show_next_step)
        self.btn_next.setEnabled(False)

        playback_layout.addWidget(self.btn_prev)
        playback_layout.addWidget(self.btn_play)
        playback_layout.addWidget(self.btn_next)
        game_layout_right.addLayout(playback_layout)

        # 速度选择
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("speed:"))
        self.speed_buttons = {}
        for label, ms in [("0.5x", 1000), ("1x", 500), ("2x", 250), ("4x", 125)]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedWidth(45)
            btn.clicked.connect(lambda _, m=ms: self._set_speed(m))
            speed_layout.addWidget(btn)
            self.speed_buttons[label] = btn
        self.speed_buttons["1x"].setChecked(True)
        self.playback_interval = 500
        game_layout_right.addLayout(speed_layout)

        # 步骤展示区
        self.steps_display = QTextEdit()
        self.steps_display.setReadOnly(True)
        self.steps_display.setFont(QFont("Monospace", 10))
        game_layout_right.addWidget(self.steps_display)

        self.setLayout(layout)

    # ------------------------------------------------------------------
    # 棋盘渲染
    # ------------------------------------------------------------------

    def load_board_state(self, board_2d, enable_move=True, highlight_pos=None):
        """渲染棋盘。highlight_pos=(r,c) 高亮当前位置（回放时用）"""
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        size = len(board_2d)
        for i, row in enumerate(board_2d):
            for j, num in enumerate(row):
                if num == 0:
                    # 空格用透明占位
                    placeholder = QLabel("")
                    placeholder.setFixedSize(60, 60)
                    placeholder.setStyleSheet("background: #f0f0f0; border: 2px dashed #ccc; border-radius: 6px;")
                    self.grid_layout.addWidget(placeholder, i, j)
                    continue
                button = QPushButton(str(num))
                button.setFixedSize(60, 60)
                button.setFont(QFont("Arial", 16, QFont.Bold))
                style = "QPushButton { background: #4a90d9; color: white; border: none; border-radius: 6px; }"
                if highlight_pos and (i, j) == highlight_pos:
                    style = "QPushButton { background: #f5a623; color: white; border: 2px solid #d4880c; border-radius: 6px; }"
                if not enable_move:
                    style += "QPushButton:hover { background: #4a90d9; }"
                else:
                    style += "QPushButton:hover { background: #357abd; }"
                button.setStyleSheet(style)
                if enable_move:
                    button.clicked.connect(lambda _, x=i, y=j: self.handle_move(x, y))
                self.grid_layout.addWidget(button, i, j)

    def load_board(self):
        self.load_board_state(self.game.board)

    def load_state(self, board_2d, highlight_pos=None):
        self.load_board_state(board_2d, enable_move=False, highlight_pos=highlight_pos)

    # ------------------------------------------------------------------
    # 计时 / 计步
    # ------------------------------------------------------------------

    def _reset_steps_and_timer(self):
        self.elapsed_timer.stop()
        self.start_time = 0
        self.step_count = 0
        self.lbl_steps.setText("steps: 0")
        self.lbl_time.setText("time: 00:00")
        self.lbl_optimal.setText("")

    def _reset_solution_navigation(self):
        self.solution_states = None
        self.solution_moves = None
        self.current_step_index = 0
        self.btn_next.setEnabled(False)
        self.btn_prev.setEnabled(False)
        self.btn_play.setEnabled(False)
        self.steps_display.clear()
        self._stop_playback()
        self.optimal_steps = None
        if self.game is not None:
            self.load_board()

    def _reset_game_view_state(self):
        self._reset_steps_and_timer()
        self._reset_solution_navigation()
        self.undo_stack.clear()
        self.load_board()
        self.session_initial_board = copy.deepcopy(self.game.board)

    def _set_empty_position_from_board(self):
        for i, row in enumerate(self.game.board):
            for j, value in enumerate(row):
                if value == 0:
                    self.game.empty_pos = (i, j)
                    return
        raise ValueError("Puzzle board must contain one empty tile (0).")

    def _save_completed_game(self, source):
        if self.history_store is None:
            return

        elapsed = int(time.time() - self.start_time) if self.start_time else 0
        initial_board = copy.deepcopy(self.session_initial_board or self.game.board)
        final_board = copy.deepcopy(self.game.board)
        record = build_game_record(
            board_size=self.game.size,
            initial_board=initial_board,
            final_board=final_board,
            steps=self.step_count,
            duration_seconds=elapsed,
            source=source,
        )

        try:
            self.history_store.append_record(record)
        except (OSError, ValueError, TypeError) as exc:
            QMessageBox.warning(self, "History Error", f"Failed to save game history: {exc}")

    def update_time_label(self):
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.lbl_time.setText(f"time: {minutes:02d}:{seconds:02d}")

    # ------------------------------------------------------------------
    # 手动移动
    # ------------------------------------------------------------------

    def handle_move(self, x, y):
        empty_x, empty_y = self.game.empty_pos
        direction = (x - empty_x, y - empty_y)

        if direction in GameLogic.directions.values():
            # 保存撤销状态
            self.undo_stack.append((
                copy.deepcopy(self.game.board),
                self.game.empty_pos
            ))

            success = self.game.move(direction)
            if success:
                self.step_count += 1
                if self.step_count == 1:
                    self.start_time = time.time()
                    self.elapsed_timer.start(1000)
                    self.lbl_time.setText("time: 00:00")
                self.lbl_steps.setText(f"steps: {self.step_count}")
                # 更新最优解对比
                if self.optimal_steps is not None:
                    self.lbl_optimal.setText(f"(optimal: {self.optimal_steps})")
            else:
                # 移动失败，弹出撤销栈
                self.undo_stack.pop()

            self.load_board()

            if self.game.is_solved():
                self.elapsed_timer.stop()
                self._save_completed_game(source="manual")
                self._show_victory()

    def _show_victory(self):
        msg = f"🎉 Congratulations! You solved the puzzle!\n\nSteps: {self.step_count}"
        if self.optimal_steps is not None:
            ratio = self.step_count / self.optimal_steps if self.optimal_steps > 0 else 0
            msg += f"\nOptimal: {self.optimal_steps}\nEfficiency: {ratio:.0%}"
        QMessageBox.information(self, "Victory", msg)

    # ------------------------------------------------------------------
    # 撤销
    # ------------------------------------------------------------------

    def undo_move(self):
        if not self.undo_stack:
            return
        board, empty_pos = self.undo_stack.pop()
        self.game.board = board
        self.game.empty_pos = empty_pos
        self.step_count = max(0, self.step_count - 1)
        self.lbl_steps.setText(f"steps: {self.step_count}")
        self.load_board()

    # ------------------------------------------------------------------
    # 重置棋盘
    # ------------------------------------------------------------------

    def reset_board(self):
        if self.session_initial_board is None:
            return
        self.game.board = copy.deepcopy(self.session_initial_board)
        self._set_empty_position_from_board()
        self._reset_game_view_state()

    # ------------------------------------------------------------------
    # 求解
    # ------------------------------------------------------------------

    def solve_puzzle(self):
        self.solution_moves = self.game.solve()
        if not self.solution_moves:
            QMessageBox.information(self, "Solution", "No solution found or already solved.")
            return

        self.elapsed_timer.stop()
        self.optimal_steps = len(self.solution_moves)
        self.lbl_optimal.setText(f"(optimal: {self.optimal_steps})")

        # 生成所有中间状态
        temp_game = copy.deepcopy(self.game)
        self.solution_states = []
        self.solution_states.append(copy.deepcopy(temp_game.board))

        for mv in self.solution_moves:
            temp_game.move(GameLogic.directions[mv])
            self.solution_states.append(copy.deepcopy(temp_game.board))

        # 显示步骤（带方向箭头）
        steps_text = ""
        for i, mv in enumerate(self.solution_moves, start=1):
            arrow = _DIR_CN.get(mv, mv)
            steps_text += f"{i:2d}. {arrow}  {mv}\n"
        self.steps_display.setText(steps_text)

        # 重置索引
        self.current_step_index = 0
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(True)
        self.btn_play.setEnabled(True)
        self.load_state(self.solution_states[0])

    # ------------------------------------------------------------------
    # 回放控制
    # ------------------------------------------------------------------

    def show_previous_step(self):
        if self.solution_states is None:
            return
        if self.current_step_index > 0:
            self.current_step_index -= 1
            # 高亮被移动的 tile
            highlight = self._get_moved_tile_pos(self.current_step_index)
            self.load_state(self.solution_states[self.current_step_index], highlight_pos=highlight)
            self.btn_next.setEnabled(True)
        if self.current_step_index == 0:
            self.btn_prev.setEnabled(False)

    def show_next_step(self):
        if self.solution_states is None:
            return
        if self.current_step_index < len(self.solution_states) - 1:
            self.current_step_index += 1
            highlight = self._get_moved_tile_pos(self.current_step_index)
            self.load_state(self.solution_states[self.current_step_index], highlight_pos=highlight)
            self.btn_prev.setEnabled(True)
        if self.current_step_index == len(self.solution_states) - 1:
            self.btn_next.setEnabled(False)

    def _get_moved_tile_pos(self, step_index):
        """获取第 step_index 步被移动的 tile 在新状态中的位置"""
        if step_index == 0 or self.solution_states is None:
            return None
        prev = self.solution_states[step_index - 1]
        curr = self.solution_states[step_index]
        size = len(prev)
        for i in range(size):
            for j in range(size):
                if prev[i][j] != curr[i][j] and curr[i][j] != 0:
                    return (i, j)
        return None

    def toggle_playback(self):
        if self.is_playing:
            self._stop_playback()
        else:
            self._start_playback()

    def _start_playback(self):
        if self.solution_states is None:
            return
        # 如果已经在末尾，从头开始
        if self.current_step_index >= len(self.solution_states) - 1:
            self.current_step_index = 0
            self.load_state(self.solution_states[0])
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(True)
        self.is_playing = True
        self.btn_play.setText("⏸ Pause")
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.playback_timer.start(self.playback_interval)

    def _stop_playback(self):
        self.is_playing = False
        self.playback_timer.stop()
        self.btn_play.setText("▶ Play")
        # 恢复按钮状态
        if self.solution_states is not None:
            self.btn_prev.setEnabled(self.current_step_index > 0)
            self.btn_next.setEnabled(self.current_step_index < len(self.solution_states) - 1)

    def _playback_step(self):
        """定时器回调：播放下一步"""
        if self.solution_states is None:
            self._stop_playback()
            return
        if self.current_step_index >= len(self.solution_states) - 1:
            self._stop_playback()
            return
        self.current_step_index += 1
        highlight = self._get_moved_tile_pos(self.current_step_index)
        self.load_state(self.solution_states[self.current_step_index], highlight_pos=highlight)

    def _set_speed(self, ms):
        self.playback_interval = ms
        for label, btn in self.speed_buttons.items():
            btn.setChecked(btn.isChecked() and btn.sender() != btn)
        # 重置所有按钮样式
        for btn in self.speed_buttons.values():
            btn.setChecked(False)
        # 设置当前按钮
        for label, m in [("0.5x", 1000), ("1x", 500), ("2x", 250), ("4x", 125)]:
            if m == ms:
                self.speed_buttons[label].setChecked(True)
                break
        if self.is_playing:
            self.playback_timer.setInterval(ms)

    # ------------------------------------------------------------------
    # 导航
    # ------------------------------------------------------------------

    def set_size(self):
        dialog = SelectSizeDialog()
        if dialog.exec_() == QDialog.Accepted:
            size = dialog.get_selected_size()
            self.game.set_size(size)
            self.game.generate_board()
            self._reset_game_view_state()

    def go_back(self):
        self._stop_playback()
        self.stacked_widget.setCurrentIndex(0)

    def load_replay_record(self, record):
        if len(record.final_board) != record.board_size or any(len(row) != record.board_size for row in record.final_board):
            QMessageBox.warning(self, "Replay Error", "Record board size does not match replay data.")
            return
        self.game.set_size(record.board_size)
        self.game.board = copy.deepcopy(record.final_board)
        self._set_empty_position_from_board()
        self._reset_game_view_state()

    def customize(self):
        dialog = CustomizeGameDialog()
        if dialog.exec_() == QDialog.Accepted:
            board_2d = dialog.get_custom_layout()
            self.game.set_size(len(board_2d))
            self.game.board = board_2d
            self._set_empty_position_from_board()
            if not self.game.is_solvable():
                QMessageBox.information(self, "Error", "Puzzle is not solvable.")
            else:
                self._reset_game_view_state()
