from pathlib import Path

import pytest

from product_reco_bot.collectors.csv_collector import CsvCollector
from product_reco_bot.collectors.factory import build_collector
from product_reco_bot.config import AppConfig


def test_factory_uses_csv_by_default() -> None:
    collector = build_collector(
        AppConfig(data_csv=Path("data/imports/sample_products.csv")), Path(".")
    )

    # Signals wrap the source collector in normal settings only when paths are configured.
    assert isinstance(collector, CsvCollector)


def test_factory_requires_pdd_environment(monkeypatch) -> None:
    for name in ("PDD_CLIENT_ID", "PDD_CLIENT_SECRET", "PDD_PID"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="PDD_CLIENT_ID"):
        build_collector(AppConfig(product_source="pdd"), Path("."))
