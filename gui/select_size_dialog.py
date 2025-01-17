from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QSpinBox, QPushButton


class SelectSizeDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Board Size")

        layout = QVBoxLayout()

        label = QLabel("Choose the board size:")
        layout.addWidget(label)

        self.size_selector = QSpinBox()
        self.size_selector.setRange(3, 5)
        self.size_selector.setValue(3)
        layout.addWidget(self.size_selector)

        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(self.accept)
        layout.addWidget(confirm_button)

        self.setLayout(layout)

    def get_selected_size(self):
        return self.size_selector.value()
