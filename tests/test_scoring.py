from datetime import UTC, datetime
from pathlib import Path

from product_reco_bot.collectors.csv_collector import CsvCollector
from product_reco_bot.config import load_score_config
from product_reco_bot.services.recommendation import RecommendationService
from product_reco_bot.services.scoring import ScoringService


def test_recommendations_are_sorted_by_hot_score() -> None:
    products = CsvCollector(Path("data/imports/sample_products.csv")).collect_keywords(limit=10)
    service = RecommendationService(ScoringService(load_score_config()))

    recommendations = service.build_recommendations(products, limit=4)
    scores = [item.score.hot_score for item in recommendations]

    assert scores == sorted(scores, reverse=True)
    assert recommendations[0].score.hot_score > 0


def test_hot_label_is_assigned() -> None:
    service = ScoringService(load_score_config())

    assert service.hot_label(95) == "爆款预警"
    assert service.hot_label(82) == "高热推荐"
    assert service.hot_label(72) == "潜力热款"


def test_recently_recommended_product_gets_lower_novelty_score() -> None:
    product = CsvCollector(Path("data/imports/sample_products.csv")).collect_keywords(limit=1)[0]
    now = datetime(2026, 7, 13, tzinfo=UTC)
    service = ScoringService(
        load_score_config(),
        last_recommended_at={
            product.product_id: datetime(2026, 7, 10, tzinfo=UTC)
        },
    )

    result = service.score(product, now=now)

    assert result.novelty_score == 20.0


def test_zero_growth_does_not_claim_sales_momentum() -> None:
    products = CsvCollector(Path("data/imports/sample_products.csv")).collect_keywords(
        keywords=["NeeDoh"], limit=1
    )
    service = RecommendationService(ScoringService(load_score_config()))

    recommendation = service.build_recommendations(products, limit=1)[0]

    assert all("销量增长" not in reason for reason in recommendation.reasons)
    assert any("互动量待验证" in reason for reason in recommendation.reasons)
