from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class GameRecord:
    id: str
    board_size: int
    initial_board: List[List[int]]
    final_board: List[List[int]]
    steps: int
    duration_seconds: int
    finished_at: str
    source: str

    def to_dict(self):
        return {
            "id": self.id,
            "board_size": self.board_size,
            "initial_board": self.initial_board,
            "final_board": self.final_board,
            "steps": self.steps,
            "duration_seconds": self.duration_seconds,
            "finished_at": self.finished_at,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, payload):
        return cls(
            id=payload["id"],
            board_size=payload["board_size"],
            initial_board=payload["initial_board"],
            final_board=payload["final_board"],
            steps=payload["steps"],
            duration_seconds=payload["duration_seconds"],
            finished_at=payload["finished_at"],
            source=payload["source"],
        )
