from __future__ import annotations

from datetime import UTC, datetime

from product_reco_bot.config import ScoreConfig
from product_reco_bot.models import ProductCandidate, ScoreBreakdown


def clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def log_norm(value: int | float, scale: float) -> float:
    if value <= 0:
        return 0.0
    return clamp((value / scale) * 100)


class ScoringService:
    def __init__(
        self,
        config: ScoreConfig,
        last_recommended_at: dict[str, datetime] | None = None,
    ) -> None:
        self.config = config
        self.last_recommended_at = last_recommended_at or {}

    def score(self, product: ProductCandidate, now: datetime | None = None) -> ScoreBreakdown:
        now = now or datetime.now(UTC)
        social = self._social_score(product, now)
        sales = self._sales_growth_score(product)
        fashion = self._fashion_trend_score(product, now)
        supply = self._supply_score(product)
        novelty = self._novelty_score(product, now)
        weights = self.config.hot_score
        hot_score = (
            social * weights.social
            + sales * weights.sales_growth
            + fashion * weights.fashion_trend
            + supply * weights.supply
            + novelty * weights.novelty
        )
        hot_score = round(clamp(hot_score), 2)
        return ScoreBreakdown(
            social_score=round(social, 2),
            sales_growth_score=round(sales, 2),
            fashion_trend_score=round(fashion, 2),
            supply_score=round(supply, 2),
            novelty_score=novelty,
            hot_score=hot_score,
            hot_label=self.hot_label(hot_score),
        )

    def hot_label(self, score: float) -> str:
        thresholds = self.config.thresholds
        if score >= thresholds["burst"]:
            return "爆款预警"
        if score >= thresholds["high"]:
            return "高热推荐"
        if score >= thresholds["potential"]:
            return "潜力热款"
        if score >= thresholds["watch"]:
            return "观察款"
        return "低热观察"

    def _social_score(self, product: ProductCandidate, now: datetime) -> float:
        recency = 0.0
        if product.social_publish_time:
            hours = max(0.0, (now - product.social_publish_time).total_seconds() / 3600)
            recency = clamp((1 - hours / 72) * 100)
        return clamp(
            log_norm(product.social_views, 250000) * 0.35
            + log_norm(product.social_likes, 30000) * 0.25
            + log_norm(product.social_comments, 2500) * 0.15
            + log_norm(product.social_shares, 4000) * 0.15
            + recency * 0.10
        )

    def _sales_growth_score(self, product: ProductCandidate) -> float:
        rank_rise = 0.0
        if (
            product.rank_current
            and product.rank_previous
            and product.rank_previous > product.rank_current
        ):
            rank_change = (product.rank_previous - product.rank_current) / product.rank_previous
            rank_rise = clamp(rank_change * 100)
        return clamp(
            clamp(product.sales_growth_rate_7d * 100) * 0.50
            + log_norm(product.sales_7d, 5000) * 0.25
            + rank_rise * 0.15
            + log_norm(product.social_comments, 2000) * 0.10
        )

    def _fashion_trend_score(self, product: ProductCandidate, now: datetime) -> float:
        keyword_score = clamp(len(product.fashion_keywords) * 25)
        authority = {
            "vogue": 100,
            "wwd": 100,
            "elle": 80,
            "harper": 80,
            "trendhunter": 70,
            "pinterest": 70,
        }
        source_lower = product.fashion_source.lower()
        authority_score = next(
            (score for key, score in authority.items() if key in source_lower), 50
        )
        recency = 50.0
        if product.fashion_publish_time:
            days = max(0.0, (now - product.fashion_publish_time).total_seconds() / 86400)
            recency = clamp((1 - days / 30) * 100)
        return clamp(keyword_score * 0.50 + authority_score * 0.30 + recency * 0.20)

    def _supply_score(self, product: ProductCandidate) -> float:
        link_score = 100.0 if product.purchase_url else 0.0
        price_score = 100.0 if 5 <= product.price <= 50 else 60.0 if product.price else 0.0
        supplier_score = 80.0 if product.supplier_name else 40.0
        return clamp(link_score * 0.30 + price_score * 0.25 + supplier_score * 0.20 + 80 * 0.25)

    def _novelty_score(self, product: ProductCandidate, now: datetime) -> float:
        last_sent = self.last_recommended_at.get(product.product_id)
        if last_sent is None:
            return 100.0
        days = max(0.0, (now - last_sent).total_seconds() / 86400)
        if days < 7:
            return 20.0
        if days < 14:
            return 60.0
        return 100.0
