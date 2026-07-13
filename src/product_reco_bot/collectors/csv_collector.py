from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from product_reco_bot.collectors.base import CollectorAdapter
from product_reco_bot.models import ProductCandidate


class CsvCollector(CollectorAdapter):
    name = "csv"
    platform = "manual_import"
    supported_modes = ("csv",)

    def __init__(self, csv_path: Path) -> None:
        self.csv_path = csv_path

    def collect_keywords(
        self, keywords: list[str] | None = None, since: datetime | None = None, limit: int = 50
    ) -> list[ProductCandidate]:
        products: list[ProductCandidate] = []
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                product = self.normalize(row)
                if keywords and not self._matches_keywords(product, keywords):
                    continue
                if since and product.social_publish_time and product.social_publish_time < since:
                    continue
                products.append(product)
                if len(products) >= limit:
                    break
        return products

    def normalize(self, raw_item: dict[str, Any]) -> ProductCandidate:
        return ProductCandidate.model_validate(raw_item)

    @staticmethod
    def _matches_keywords(product: ProductCandidate, keywords: list[str]) -> bool:
        haystack = " ".join(
            [
                product.product_name,
                product.description,
                product.social_keyword,
                " ".join(product.fashion_keywords),
            ]
        ).lower()
        return any(keyword.lower() in haystack for keyword in keywords)

