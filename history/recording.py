from datetime import datetime
from uuid import uuid4

from history.models import GameRecord


def build_game_record(
    board_size,
    initial_board,
    final_board,
    steps,
    duration_seconds,
    source,
    record_id=None,
    finished_at=None,
):
    return GameRecord(
        id=record_id or str(uuid4()),
        board_size=board_size,
        initial_board=initial_board,
        final_board=final_board,
        steps=steps,
        duration_seconds=duration_seconds,
        finished_at=finished_at or datetime.now().isoformat(timespec="seconds"),
        source=source,
    )
