from __future__ import annotations

import json
from pathlib import Path


class PushTargetStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def save(self, unified_msg_origin: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"unified_msg_origin": unified_msg_origin}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self) -> str | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        value = data.get("unified_msg_origin")
        return str(value) if value else None
