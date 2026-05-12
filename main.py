import sys
from PyQt5.QtWidgets import QApplication, QStackedWidget

from history.store import HistoryStore
from gui.game_window import GameWindow
from gui.history_window import HistoryWindow
from gui.main_window import MainWindow


class App(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)

        self.stacked_widget = QStackedWidget()
        self.history_store = HistoryStore()

        self.main_window = MainWindow(self.stacked_widget)
        self.game_window = GameWindow(self.stacked_widget, history_store=self.history_store)
        self.history_window = HistoryWindow(
            self.stacked_widget,
            history_store=self.history_store,
            replay_callback=self.replay_history_record,
        )

        self.stacked_widget.addWidget(self.main_window)
        self.stacked_widget.addWidget(self.game_window)
        self.stacked_widget.addWidget(self.history_window)

        self.stacked_widget.setCurrentIndex(0)
        self.stacked_widget.show()

    def replay_history_record(self, record):
        self.game_window.load_replay_record(record)

if __name__ == "__main__":
    PuzzleApp = App(sys.argv)
    sys.exit(PuzzleApp.exec_())
