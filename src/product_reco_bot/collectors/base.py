from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from product_reco_bot.models import ProductCandidate


class CollectorAdapter(ABC):
    name: str
    platform: str
    supported_modes: tuple[str, ...]

    @abstractmethod
    def collect_keywords(
        self, keywords: list[str] | None = None, since: datetime | None = None, limit: int = 50
    ) -> list[ProductCandidate]:
        raise NotImplementedError

    def collect_product(self, product_url_or_id: str) -> ProductCandidate:
        raise NotImplementedError(f"{self.name} does not implement product lookup")

    @abstractmethod
    def normalize(self, raw_item: dict[str, Any]) -> ProductCandidate:
        raise NotImplementedError

    def health_check(self) -> bool:
        return True

