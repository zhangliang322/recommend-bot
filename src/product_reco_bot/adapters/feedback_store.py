from __future__ import annotations

import json
from pathlib import Path

from product_reco_bot.models import ProductFeedback


class FeedbackStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, feedback: ProductFeedback) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(feedback.model_dump(mode="json"), ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def list_all(self) -> list[ProductFeedback]:
        if not self.path.exists():
            return []
        return [
            ProductFeedback.model_validate_json(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
