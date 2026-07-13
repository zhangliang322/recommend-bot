import json
from pathlib import Path

from product_reco_bot.collectors.csv_collector import CsvCollector
from product_reco_bot.collectors.enriched_collector import EnrichedCollector
from product_reco_bot.collectors.jsonl_signal_collector import JsonlSignalCollector


def test_external_signals_enrich_product_candidates() -> None:
    collector = EnrichedCollector(
        CsvCollector(Path("data/imports/sample_products.csv")),
        JsonlSignalCollector([Path("data/imports/sample_external_signals.jsonl")]),
    )

    products = {item.product_id: item for item in collector.collect_keywords(limit=100)}

    assert products["TOY-001"].social_platform == "tiktok"
    assert products["TOY-001"].social_views == 1700000
    assert products["TOY-001"].sales_growth_rate_7d == 1.85
    assert "balletcore" in products["ACC-001"].fashion_keywords


def test_enrichment_ignores_stale_social_signal(tmp_path: Path) -> None:
    path = tmp_path / "old.jsonl"
    path.write_text(
        json.dumps(
            {
                "signal_id": "old-social",
                "signal_type": "social",
                "source_platform": "tiktok",
                "product_id": "TOY-002",
                "published_at": "2020-01-01T00:00:00Z",
                "views": 99999999,
            }
        ),
        encoding="utf-8",
    )
    collector = EnrichedCollector(
        CsvCollector(Path("data/imports/sample_products.csv")),
        JsonlSignalCollector([path]),
    )

    products = {item.product_id: item for item in collector.collect_keywords(limit=100)}

    assert products["TOY-002"].social_views < 99999999
