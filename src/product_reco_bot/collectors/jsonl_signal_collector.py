from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from product_reco_bot.models import ExternalSignal


class JsonlSignalCollector:
    """Imports normalized output from external open-source collectors and APIs."""

    def __init__(self, paths: list[Path]) -> None:
        self.paths = paths

    def collect(self, since_days: int | None = None) -> list[ExternalSignal]:
        cutoff = (
            datetime.now(UTC) - timedelta(days=since_days)
            if since_days is not None
            else None
        )
        signals: list[ExternalSignal] = []
        for path in self.paths:
            if not path.exists():
                continue
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if not line.strip():
                    continue
                raw = json.loads(line)
                signal = self.normalize(raw, path, line_number)
                if cutoff and signal.published_at and signal.published_at < cutoff:
                    continue
                signals.append(signal)
        return signals

    @staticmethod
    def normalize(raw: dict[str, Any], path: Path, line_number: int) -> ExternalSignal:
        metrics = raw.get("metrics") if isinstance(raw.get("metrics"), dict) else {}
        data = {
            "signal_id": raw.get("signal_id") or f"{path.stem}-{line_number}",
            "signal_type": raw.get("signal_type") or raw.get("type"),
            "source_platform": raw.get("source_platform") or raw.get("platform"),
            "source_format": raw.get("source_format", "canonical"),
            "product_id": raw.get("product_id", ""),
            "keyword": raw.get("keyword") or raw.get("hashtag") or "",
            "title": raw.get("title") or raw.get("note_title") or raw.get("desc") or "",
            "content_url": raw.get("content_url") or raw.get("post_url") or raw.get("url") or "",
            "image_url": raw.get("image_url") or raw.get("cover_url") or "",
            "published_at": raw.get("published_at") or raw.get("publish_time"),
            "views": raw.get("views", metrics.get("views", 0)),
            "likes": raw.get("likes", raw.get("liked_count", metrics.get("likes", 0))),
            "comments": raw.get(
                "comments", raw.get("comment_count", metrics.get("comments", 0))
            ),
            "shares": raw.get("shares", raw.get("share_count", metrics.get("shares", 0))),
            "sales_7d": raw.get("sales_7d", metrics.get("sales_7d", 0)),
            "sales_growth_rate_7d": raw.get(
                "sales_growth_rate_7d", metrics.get("sales_growth_rate_7d", 0)
            ),
            "rank_current": raw.get("rank_current", metrics.get("rank_current", 0)),
            "rank_previous": raw.get("rank_previous", metrics.get("rank_previous", 0)),
        }
        return ExternalSignal.model_validate(data)
