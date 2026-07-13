from __future__ import annotations

from product_reco_bot.models import ProductCandidate, Recommendation
from product_reco_bot.services.scoring import ScoringService


class RecommendationService:
    def __init__(self, scoring_service: ScoringService) -> None:
        self.scoring_service = scoring_service

    def build_recommendations(
        self, products: list[ProductCandidate], limit: int = 5
    ) -> list[Recommendation]:
        deduped = self._deduplicate(products)
        recommendations = [self._build(product) for product in deduped]
        recommendations.sort(key=lambda item: item.score.hot_score, reverse=True)
        return recommendations[:limit]

    def _build(self, product: ProductCandidate) -> Recommendation:
        score = self.scoring_service.score(product)
        reasons = [
            (
                f"{product.social_platform or product.source_platform} "
                f"近期关键词“{product.social_keyword}”热度较高"
            ),
            f"近 7 日销量增长约 {product.sales_growth_rate_7d:.0%}，具备短期跟进价值",
            f"匹配趋势标签：{'、'.join(product.fashion_keywords[:3]) or '暂无'}",
        ]
        one_line = product.description or f"{product.product_name}适合做今日精品推荐"
        return Recommendation(
            product=product,
            score=score,
            reasons=reasons,
            one_line_selling_point=one_line,
        )

    @staticmethod
    def _deduplicate(products: list[ProductCandidate]) -> list[ProductCandidate]:
        seen: set[str] = set()
        deduped: list[ProductCandidate] = []
        for product in products:
            key = product.product_name.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(product)
        return deduped
