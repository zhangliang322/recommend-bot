from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


class RecommendationHistoryStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def record(
        self,
        product_ids: list[str],
        target_group: str,
        sent_at: datetime | None = None,
    ) -> None:
        timestamp = sent_at or datetime.now(UTC)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            for product_id in product_ids:
                record = {
                    "product_id": product_id,
                    "target_group": target_group,
                    "sent_at": timestamp.isoformat(),
                }
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def last_sent_map(self) -> dict[str, datetime]:
        if not self.path.exists():
            return {}
        result: dict[str, datetime] = {}
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            product_id = str(record["product_id"])
            sent_at = datetime.fromisoformat(str(record["sent_at"]))
            current = result.get(product_id)
            if current is None or sent_at > current:
                result[product_id] = sent_at
        return result
