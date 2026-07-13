from pathlib import Path

from product_reco_bot.adapters.feedback_store import FeedbackStore
from product_reco_bot.models import ProductFeedback


def test_feedback_store_appends_records(tmp_path: Path) -> None:
    store = FeedbackStore(tmp_path / "feedback.jsonl")
    feedback = ProductFeedback(
        product_id="TOY-001",
        rating="好",
        operator_id="admin-1",
        target_group="wecom:group:123",
        note="客户询问较多",
    )

    store.append(feedback)

    assert store.list_all() == [feedback]
