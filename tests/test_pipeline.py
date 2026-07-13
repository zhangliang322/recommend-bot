from pathlib import Path

from product_reco_bot.collectors.csv_collector import CsvCollector
from product_reco_bot.config import AppConfig, ScoreConfig
from product_reco_bot.services.pipeline import DailyRecommendationPipeline
from product_reco_bot.services.recommendation import RecommendationService
from product_reco_bot.services.scoring import ScoringService


def test_pipeline_renders_ranked_cards(tmp_path: Path) -> None:
    config = AppConfig(
        data_csv=Path("data/imports/sample_products.csv"),
        output_dir=tmp_path,
        recommendation_limit=2,
    )
    pipeline = DailyRecommendationPipeline(
        config,
        CsvCollector(config.data_csv),
        RecommendationService(ScoringService(ScoreConfig())),
    )

    result = pipeline.run()

    assert len(result.recommendations) == 2
    assert result.recommendations[0].score.hot_score >= result.recommendations[1].score.hot_score
    assert all(
        item.card_image_path and item.card_image_path.exists()
        for item in result.recommendations
    )


def test_pipeline_can_require_approved_products(tmp_path: Path) -> None:
    config = AppConfig(
        data_csv=Path("data/imports/sample_products.csv"), output_dir=tmp_path
    )
    pipeline = DailyRecommendationPipeline(
        config,
        CsvCollector(config.data_csv),
        RecommendationService(ScoringService(ScoreConfig())),
    )

    result = pipeline.run(approved_ids={"TOY-001"})

    assert [item.product.product_id for item in result.recommendations] == ["TOY-001"]
