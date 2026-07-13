from __future__ import annotations

from product_reco_bot.collectors.csv_collector import CsvCollector
from product_reco_bot.config import load_app_config, load_score_config
from product_reco_bot.services.recommendation import RecommendationService
from product_reco_bot.services.scoring import ScoringService


class AstrBotProductRecoPlugin:
    """Framework boundary placeholder for the future AstrBot plugin.

    Keep business logic in services so this class can stay thin when wired into AstrBot.
    """

    def today(self) -> str:
        app_config = load_app_config()
        score_config = load_score_config()
        products = CsvCollector(app_config.data_csv).collect_keywords(limit=50)
        recommendations = RecommendationService(ScoringService(score_config)).build_recommendations(
            products, limit=app_config.recommendation_limit
        )
        return "\n".join(
            f"{idx}. {item.product.product_name} {item.score.hot_score:.0f} {item.score.hot_label}"
            for idx, item in enumerate(recommendations, start=1)
        )

