from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QTextEdit, QLabel, QMessageBox


class HistoryWindow(QWidget):
    def __init__(self, stacked_widget, history_store, replay_callback):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.history_store = history_store
        self.replay_callback = replay_callback
        self.records = []
        self.init_ui()
        self.load_records()

    def init_ui(self):
        self.setWindowTitle("History")
        layout = QVBoxLayout()

        top_bar = QHBoxLayout()
        btn_back = QPushButton("Main")
        btn_back.clicked.connect(self.go_back)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_records)
        top_bar.addWidget(btn_back)
        top_bar.addWidget(btn_refresh)
        layout.addLayout(top_bar)

        layout.addWidget(QLabel("History Records"))
        self.records_list = QListWidget()
        self.records_list.currentRowChanged.connect(self.on_record_selected)
        layout.addWidget(self.records_list)

        layout.addWidget(QLabel("Record Details"))
        self.details_view = QTextEdit()
        self.details_view.setReadOnly(True)
        layout.addWidget(self.details_view)

        self.btn_replay = QPushButton("Replay")
        self.btn_replay.setEnabled(False)
        self.btn_replay.clicked.connect(self.replay_selected_record)
        layout.addWidget(self.btn_replay)

        self.setLayout(layout)

    def go_back(self):
        self.stacked_widget.setCurrentIndex(0)

    def load_records(self):
        try:
            self.records = self.history_store.list_records()
        except (OSError, ValueError, TypeError) as exc:
            self.records = []
            QMessageBox.warning(self, "History Error", f"Failed to load history: {exc}")

        self.records_list.clear()
        for record in self.records:
            summary = (
                f"{record.finished_at} | {record.board_size}x{record.board_size} | "
                f"steps: {record.steps} | time: {record.duration_seconds}s | {record.source}"
            )
            self.records_list.addItem(summary)

        self.details_view.clear()
        self.btn_replay.setEnabled(False)

    def on_record_selected(self, row):
        if row < 0 or row >= len(self.records):
            self.details_view.clear()
            self.btn_replay.setEnabled(False)
            return

        record = self.records[row]
        detail_text = (
            f"ID: {record.id}\n"
            f"Finished At: {record.finished_at}\n"
            f"Board Size: {record.board_size}\n"
            f"Source: {record.source}\n"
            f"Steps: {record.steps}\n"
            f"Duration: {record.duration_seconds}s\n\n"
            f"Final Board:\n{self._format_board(record.final_board)}"
        )
        self.details_view.setText(detail_text)
        self.btn_replay.setEnabled(True)

    def replay_selected_record(self):
        row = self.records_list.currentRow()
        if row < 0 or row >= len(self.records):
            return

        self.replay_callback(self.records[row])
        self.stacked_widget.setCurrentIndex(1)

    def _format_board(self, board):
        return "\n".join(" ".join(f"{value:2d}" for value in row) for row in board)
