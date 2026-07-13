from __future__ import annotations

from pathlib import Path

from product_reco_bot.collectors.base import CollectorAdapter
from product_reco_bot.collectors.csv_collector import CsvCollector
from product_reco_bot.collectors.enriched_collector import EnrichedCollector
from product_reco_bot.collectors.jsonl_signal_collector import JsonlSignalCollector
from product_reco_bot.config import AppConfig


def build_collector(config: AppConfig, root: Path = Path(".")) -> CollectorAdapter:
    product_path = config.data_csv if config.data_csv.is_absolute() else root / config.data_csv
    products = CsvCollector(product_path)
    signal_paths = [
        path if path.is_absolute() else root / path for path in config.signal_jsonl_paths
    ]
    if not signal_paths:
        return products
    return EnrichedCollector(
        products,
        JsonlSignalCollector(signal_paths),
        windows={
            "social": config.social_window_days,
            "ecommerce": config.ecommerce_window_days,
            "fashion": config.fashion_window_days,
        },
    )
