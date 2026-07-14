from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ApprovalStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def list_ids(self) -> set[str]:
        if not self.path.exists():
            return set()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        values = data.get("approved_product_ids", []) if isinstance(data, dict) else []
        return {str(value) for value in values}

    def records(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        records = data.get("approval_records", {}) if isinstance(data, dict) else {}
        return records if isinstance(records, dict) else {}

    def approve(self, product_id: str, note: str = "") -> None:
        values = self.list_ids()
        values.add(product_id)
        records = self.records()
        records[product_id] = {
            "product_id": product_id,
            "note": note[:500],
            "approved_at": datetime.now(UTC).isoformat(),
        }
        self._write(values, records)

    def revoke(self, product_id: str) -> None:
        values = self.list_ids()
        values.discard(product_id)
        records = self.records()
        records.pop(product_id, None)
        self._write(values, records)

    def _write(self, values: set[str], records: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                {"approved_product_ids": sorted(values), "approval_records": records},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.path)
