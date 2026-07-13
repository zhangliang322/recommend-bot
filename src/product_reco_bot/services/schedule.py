from __future__ import annotations

import json
from datetime import date
from pathlib import Path


class DeliveryLedger:
    """Stores the last successful automatic delivery date per target."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def was_sent(self, target: str, day: date) -> bool:
        return self._read().get(target) == day.isoformat()

    def mark_sent(self, target: str, day: date) -> None:
        data = self._read()
        data[target] = day.isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
        )

    def _read(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return {str(key): str(value) for key, value in data.items()}
