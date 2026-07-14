from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any


class SourceSyncStore:
    def __init__(self, path: Path) -> None:
        self.path = path
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
            return entry
