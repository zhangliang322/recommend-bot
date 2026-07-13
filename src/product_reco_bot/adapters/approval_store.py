from __future__ import annotations

import json
from pathlib import Path


class ApprovalStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def list_ids(self) -> set[str]:
        if not self.path.exists():
            return set()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        values = data.get("approved_product_ids", []) if isinstance(data, dict) else []
        return {str(value) for value in values}

    def approve(self, product_id: str) -> None:
        values = self.list_ids()
        values.add(product_id)
        self._write(values)

    def revoke(self, product_id: str) -> None:
        values = self.list_ids()
        values.discard(product_id)
        self._write(values)

    def _write(self, values: set[str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {"approved_product_ids": sorted(values)}, ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )
