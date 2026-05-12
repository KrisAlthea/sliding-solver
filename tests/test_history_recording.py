from history.recording import build_game_record


def test_build_game_record_uses_explicit_id_and_timestamp():
    record = build_game_record(
        board_size=3,
        initial_board=[[1, 2, 3], [4, 5, 6], [7, 0, 8]],
        final_board=[[1, 2, 3], [4, 5, 6], [7, 8, 0]],
        steps=12,
        duration_seconds=45,
        source="manual",
        record_id="custom-id",
        finished_at="2026-05-12T10:00:00",
    )

    assert record.id == "custom-id"
    assert record.board_size == 3
    assert record.steps == 12
    assert record.duration_seconds == 45
    assert record.finished_at == "2026-05-12T10:00:00"
    assert record.source == "manual"
