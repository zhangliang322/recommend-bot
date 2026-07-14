from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any


class SourceSyncStore:
    def __init__(self, path: Path, history_limit: int = 100) -> None:
        self.path = path
        self.history_path = path.with_name(f"{path.stem}_history.jsonl")
        self.history_limit = max(1, history_limit)
        self._lock = Lock()

    def list_latest(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def record(self, source: str, success: bool, message: str = "") -> dict[str, Any]:
        with self._lock:
            payload = self.list_latest()
            entry = {
                "source": source,
                "success": success,
                "synced_at": datetime.now(UTC).isoformat(),
                "message": message[:300],
            }
            payload[source] = entry
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            temporary.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            temporary.replace(self.path)
            self._append_history(entry)
            return entry

    def history(self, source: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        if not self.history_path.exists():
            return []
        entries: list[dict[str, Any]] = []
        for line in self.history_path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict) and (source is None or item.get("source") == source):
                entries.append(item)
        return entries[-max(1, min(limit, self.history_limit)) :][::-1]

    def _append_history(self, entry: dict[str, Any]) -> None:
        existing = (
            self.history(None, self.history_limit - 1) if self.history_limit > 1 else []
        )
        chronological = [*reversed(existing), entry]
        temporary = self.history_path.with_suffix(self.history_path.suffix + ".tmp")
        temporary.write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in chronological),
            encoding="utf-8",
        )
        temporary.replace(self.history_path)
