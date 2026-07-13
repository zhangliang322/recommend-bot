import json
from pathlib import Path

from product_reco_bot.collectors.jsonl_signal_collector import JsonlSignalCollector


def test_jsonl_collector_normalizes_external_aliases(tmp_path: Path) -> None:
    path = tmp_path / "signals.jsonl"
    path.write_text(
        json.dumps(
            {
                "type": "social",
                "platform": "xiaohongshu",
                "source_format": "MediaCrawler",
                "product_id": "ACC-001",
                "hashtag": "蝴蝶结",
                "note_title": "热门发饰",
                "publish_time": "2026-07-12T08:00:00+08:00",
                "liked_count": "12000",
                "comment_count": "850",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    signals = JsonlSignalCollector([path]).collect()

    assert len(signals) == 1
    assert signals[0].source_platform == "xiaohongshu"
    assert signals[0].keyword == "蝴蝶结"
    assert signals[0].likes == 12000
    assert signals[0].comments == 850


def test_jsonl_collector_filters_old_signals(tmp_path: Path) -> None:
    path = tmp_path / "signals.jsonl"
    path.write_text(
        json.dumps(
            {
                "signal_id": "old",
                "signal_type": "fashion",
                "source_platform": "editorial",
                "published_at": "2020-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    signals = JsonlSignalCollector([path]).collect(since_days=3)

    assert signals == []
