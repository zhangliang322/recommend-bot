from pathlib import Path

from product_reco_bot.collectors.csv_collector import CsvCollector


def test_csv_collector_loads_sample_products() -> None:
    products = CsvCollector(Path("data/imports/sample_products.csv")).collect_keywords(limit=10)

    product_ids = {product.product_id for product in products}
    assert {"ACC-001", "TOY-001", "ACC-002", "TOY-002"} <= product_ids
    assert {"TREND-TOY-001", "TREND-ACC-001"} <= product_ids
    assert products[0].category == "饰品"
    assert products[0].fashion_keywords


def test_csv_collector_filters_keywords() -> None:
    products = CsvCollector(Path("data/imports/sample_products.csv")).collect_keywords(
        keywords=["毛绒"], limit=10
    )

    assert len(products) == 1
    assert products[0].product_id == "TOY-001"
