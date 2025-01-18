from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, QPushButton, QMessageBox, QSpinBox, QVBoxLayout, QDialog, \
    QHBoxLayout

from game_logic import GameLogic
from gui.select_size_dialog import SelectSizeDialog


class CustomizeGameDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customize Puzzle")
        self.size = 3
        self.inputs = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 按钮: 设置棋盘大小
        btn_set_size = QPushButton("Set Size")
        btn_set_size.clicked.connect(self.set_size)
        layout.addWidget(btn_set_size)

        self.qgrid_layout = QGridLayout()
        layout.addLayout(self.qgrid_layout)

        self.load_grid()

        qhbox_layout = QHBoxLayout()

        btn_ok = QPushButton("OK", self)
        btn_ok.clicked.connect(self.on_ok_clicked)
        qhbox_layout.addWidget(btn_ok)

        btn_cancel = QPushButton("Cancel", self)
        btn_cancel.clicked.connect(self.reject)
        qhbox_layout.addWidget(btn_cancel)
        layout.addLayout(qhbox_layout)

        self.setLayout(layout)
        self.board_2d = None

    def on_ok_clicked(self):
        # 读取QLineEdit, 拼成二维board
        temp_values = []
        for i in range(self.size):
            row_vals = []
            for j in range(self.size):
                text = self.inputs[i][j].text().strip()
                if not text:
                    QMessageBox.warning(self, "Error", "All cells must be filled.")
                    return
                if not text.isdigit():
                    QMessageBox.warning(self, "Error", "Please input a digit")
                    return
                val = int(text)
                row_vals.append(val)
            temp_values.append(row_vals)

        # 检查数字是否包含0~size^2-1且无重复
        flat = [v for row in temp_values for v in row]
        expected = list(range(self.size ** 2))
        if sorted(flat) != expected:
            QMessageBox.warning(self, "Error", f"The puzzle must contain digits 0-{self.size**2-1} exactly once!")
            return

        # 到此说明玩家输入 OK
        self.board_2d = temp_values
        self.accept()

    def get_custom_layout(self):
        return self.board_2d

    def set_size(self):
        # 选择棋盘大小
        dialog = SelectSizeDialog()
        if dialog.exec_() == QDialog.Accepted:
            size = dialog.get_selected_size()

            # 更新棋盘逻辑
            self.size = size

            # 重新加载棋盘
            self.load_grid()

    def load_grid(self):
        # 清空之前的格子
        for i in reversed(range(self.qgrid_layout.count())):
            widget = self.qgrid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        # 重置输入列表
        self.inputs = []
        # 生成网格
        for i in range(self.size):
            row_inputs = []
            for j in range(self.size):
                line_edit = QLineEdit(self)
                line_edit.setFixedWidth(30)
                # 只允许输入合法数字
                line_edit.setValidator(QIntValidator(0, self.size**2 - 1, self))
                self.qgrid_layout.addWidget(line_edit, i, j)
                row_inputs.append(line_edit)
            self.inputs.append(row_inputs)