from history.models import GameRecord
from history.store import HistoryStore


def build_record(record_id, finished_at, steps=10, duration_seconds=60, source="manual"):
    return GameRecord(
        id=record_id,
        board_size=3,
        initial_board=[[1, 2, 3], [4, 5, 6], [7, 0, 8]],
        final_board=[[1, 2, 3], [4, 5, 6], [7, 8, 0]],
        steps=steps,
        duration_seconds=duration_seconds,
        finished_at=finished_at,
        source=source,
    )


def test_load_records_returns_empty_when_file_not_exists(tmp_path):
    store = HistoryStore(tmp_path / "history.json")

    records = store.load_records()

    assert records == []


def test_append_record_persists_record_to_json(tmp_path):
    store = HistoryStore(tmp_path / "history.json")
    record = build_record("r1", "2026-05-12T09:00:00")

    store.append_record(record)
    loaded = store.load_records()

    assert len(loaded) == 1
    assert loaded[0].id == "r1"
    assert loaded[0].steps == 10
    assert loaded[0].final_board == [[1, 2, 3], [4, 5, 6], [7, 8, 0]]


def test_list_records_returns_newest_first(tmp_path):
    store = HistoryStore(tmp_path / "history.json")
    older = build_record("older", "2026-05-12T09:00:00")
    newer = build_record("newer", "2026-05-12T09:10:00")

    store.append_record(older)
    store.append_record(newer)

    records = store.list_records()

    assert [record.id for record in records] == ["newer", "older"]
