from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from product_reco_bot.collectors.base import CollectorAdapter
from product_reco_bot.config import AppConfig
from product_reco_bot.models import Recommendation
from product_reco_bot.services.card_render import CardRenderService
from product_reco_bot.services.recommendation import RecommendationService
from product_reco_bot.services.safety import SafetyService


@dataclass(frozen=True)
class PipelineResult:
    recommendations: list[Recommendation]
    rejected: list[tuple[str, str]]


class DailyRecommendationPipeline:
    """Runs collection, ranking, safety checks, and card rendering."""

    def __init__(
        self,
        config: AppConfig,
        collector: CollectorAdapter,
        recommender: RecommendationService,
        safety: SafetyService | None = None,
        renderer: CardRenderService | None = None,
    ) -> None:
        self.config = config
        self.collector = collector
        self.recommender = recommender
        self.safety = safety or SafetyService()
        self.renderer = renderer or CardRenderService(config.output_dir)

    def run(
        self, limit: int | None = None, approved_ids: set[str] | None = None
    ) -> PipelineResult:
        candidates = self.collector.collect_keywords(limit=100)
        allowed = [item for item in candidates if item.category in self.config.allowed_categories]
        if approved_ids is not None:
            allowed = [item for item in allowed if item.product_id in approved_ids]
        ranked = self.recommender.build_recommendations(
            allowed, limit=limit or self.config.recommendation_limit
        )

        accepted: list[Recommendation] = []
        rejected: list[tuple[str, str]] = []
        for item in ranked:
            ok, reason = self.safety.is_pushable(item.product)
            if not ok:
                rejected.append((item.product.product_id, reason))
                continue
            item.card_image_path = Path(self.renderer.render(item)).resolve()
            accepted.append(item)
        return PipelineResult(recommendations=accepted, rejected=rejected)
