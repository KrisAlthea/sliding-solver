import json
from pathlib import Path

from history.models import GameRecord


class HistoryStore:
    def __init__(self, file_path: Path | str = Path("data/history.json")):
        self.file_path = Path(file_path)

    def load_records(self):
        if not self.file_path.exists():
            return []

        raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        return [GameRecord.from_dict(item) for item in raw]

    def append_record(self, record: GameRecord):
        records = self.load_records()
        records.append(record)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.to_dict() for item in records]
        self.file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_records(self):
        records = self.load_records()
        return sorted(records, key=lambda item: item.finished_at, reverse=True)
