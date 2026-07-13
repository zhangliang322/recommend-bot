from datetime import UTC, datetime
from pathlib import Path

from product_reco_bot.adapters.recommendation_history_store import (
    RecommendationHistoryStore,
)


def test_history_store_returns_latest_product_timestamp(tmp_path: Path) -> None:
    store = RecommendationHistoryStore(tmp_path / "history.jsonl")
    earlier = datetime(2026, 7, 1, tzinfo=UTC)
    later = datetime(2026, 7, 8, tzinfo=UTC)

    store.record(["TOY-001"], "group-1", earlier)
    store.record(["TOY-001", "ACC-001"], "group-1", later)

    assert store.last_sent_map() == {"TOY-001": later, "ACC-001": later}
