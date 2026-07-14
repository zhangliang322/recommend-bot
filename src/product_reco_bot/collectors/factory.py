from __future__ import annotations

import os
from pathlib import Path

from product_reco_bot.collectors.base import CollectorAdapter
from product_reco_bot.collectors.csv_collector import CsvCollector
from product_reco_bot.collectors.enriched_collector import EnrichedCollector
from product_reco_bot.collectors.jsonl_signal_collector import JsonlSignalCollector
from product_reco_bot.collectors.pdd_collector import PddCollector
from product_reco_bot.config import AppConfig
from product_reco_bot.integrations.pdd import PddClient, PddCredentials


def build_collector(config: AppConfig, root: Path = Path(".")) -> CollectorAdapter:
    if config.product_source == "pdd":
        required = ("PDD_CLIENT_ID", "PDD_CLIENT_SECRET", "PDD_PID")
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise RuntimeError(f"PDD 商品源缺少环境变量：{', '.join(missing)}")
        products: CollectorAdapter = PddCollector(
            PddClient(
                PddCredentials(
                    client_id=os.environ["PDD_CLIENT_ID"],
                    client_secret=os.environ["PDD_CLIENT_SECRET"],
                    pid=os.environ["PDD_PID"],
                ),
                endpoint=os.getenv(
                    "PDD_API_ENDPOINT", "https://gw-api.pinduoduo.com/api/router"
                ),
            ),
            default_keywords=config.product_keywords,
        )
    elif config.product_source == "csv":
        product_path = config.data_csv if config.data_csv.is_absolute() else root / config.data_csv
        products = CsvCollector(product_path)
    else:
        raise ValueError(f"不支持的商品源：{config.product_source}")
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
