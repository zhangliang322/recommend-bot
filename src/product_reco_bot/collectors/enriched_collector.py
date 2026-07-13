from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from product_reco_bot.collectors.base import CollectorAdapter
from product_reco_bot.collectors.jsonl_signal_collector import JsonlSignalCollector
from product_reco_bot.models import ExternalSignal, ProductCandidate


class EnrichedCollector(CollectorAdapter):
    name = "enriched-collector"
    platform = "multi-source"
    supported_modes = ("keywords",)

    def __init__(
        self,
        products: CollectorAdapter,
        signals: JsonlSignalCollector,
        windows: dict[str, int] | None = None,
    ) -> None:
        self.products = products
        self.signals = signals
        self.windows = windows or {"social": 3, "ecommerce": 7, "fashion": 30}

    def collect_keywords(
        self, keywords: list[str] | None = None, since: datetime | None = None, limit: int = 50
    ) -> list[ProductCandidate]:
        source_products = self.products.collect_keywords(keywords, since, limit)
        products = [item.model_copy(deep=True) for item in source_products]
        signals = self.signals.collect()
        for product in products:
            for signal in signals:
                if self._is_fresh(signal) and self._matches(product, signal):
                    self._apply(product, signal)
        return products

    def normalize(self, raw_item: dict[str, Any]) -> ProductCandidate:
        return self.products.normalize(raw_item)

    def health_check(self) -> bool:
        return self.products.health_check()

    def _is_fresh(self, signal: ExternalSignal) -> bool:
        if signal.published_at is None:
            return True
        cutoff = datetime.now(UTC) - timedelta(
            days=self.windows.get(signal.signal_type, 0)
        )
        return signal.published_at.astimezone(UTC) >= cutoff

    @staticmethod
    def _matches(product: ProductCandidate, signal: ExternalSignal) -> bool:
        if signal.product_id:
            return signal.product_id == product.product_id
        needle = signal.keyword.strip().lower()
        if not needle:
            return False
        haystack = " ".join(
            [
                product.product_name,
                product.description,
                product.social_keyword,
                *product.fashion_keywords,
            ]
        ).lower()
        return needle in haystack

    @staticmethod
    def _apply(product: ProductCandidate, signal: ExternalSignal) -> None:
        if signal.signal_type == "social":
            product.social_platform = signal.source_platform
            product.social_keyword = signal.keyword or product.social_keyword
            product.social_views = max(product.social_views, signal.views)
            product.social_likes = max(product.social_likes, signal.likes)
            product.social_comments = max(product.social_comments, signal.comments)
            product.social_shares = max(product.social_shares, signal.shares)
            product.social_publish_time = signal.published_at or product.social_publish_time
        elif signal.signal_type == "ecommerce":
            product.sales_7d = max(product.sales_7d, signal.sales_7d)
            product.sales_growth_rate_7d = max(
                product.sales_growth_rate_7d, signal.sales_growth_rate_7d
            )
            product.rank_current = signal.rank_current or product.rank_current
            product.rank_previous = signal.rank_previous or product.rank_previous
        elif signal.signal_type == "fashion":
            if signal.keyword and signal.keyword not in product.fashion_keywords:
                product.fashion_keywords.append(signal.keyword)
            product.fashion_source = signal.source_platform
            product.fashion_publish_time = signal.published_at or product.fashion_publish_time
