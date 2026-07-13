from pathlib import Path

from product_reco_bot.collectors.csv_collector import CsvCollector
from product_reco_bot.services.safety import SafetyService


def test_safety_accepts_sample_product() -> None:
    product = CsvCollector(Path("data/imports/sample_products.csv")).collect_keywords(limit=1)[0]

    ok, reason = SafetyService().is_pushable(product)

    assert ok is True
    assert reason == "ok"


def test_safety_rejects_missing_link() -> None:
    product = CsvCollector(Path("data/imports/sample_products.csv")).collect_keywords(limit=1)[0]
    product.purchase_url = ""

    ok, reason = SafetyService().is_pushable(product)

    assert ok is False
    assert "purchase_url" in reason

