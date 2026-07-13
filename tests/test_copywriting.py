from pathlib import Path

from product_reco_bot.collectors.csv_collector import CsvCollector
from product_reco_bot.config import load_score_config
from product_reco_bot.services.copywriting import CopywritingService
from product_reco_bot.services.recommendation import RecommendationService
from product_reco_bot.services.scoring import ScoringService


def _recommendation():
    product = CsvCollector(Path("data/imports/sample_products.csv")).collect_keywords(limit=1)
    return RecommendationService(ScoringService(load_score_config())).build_recommendations(
        product, limit=1
    )[0]


def test_private_detail_contains_traceable_fields() -> None:
    text = CopywritingService().private_detail(_recommendation())

    assert "火热指数" in text
    assert "商品来源" in text
    assert "来源链接" in text
    assert "采购链接" in text
    assert "风险提示" in text


def test_public_post_is_short_and_contains_product_link() -> None:
    text = CopywritingService().public_post(_recommendation())

    assert text.startswith("今日推荐｜")
    assert "产品链接：https://" in text
    assert "推荐理由" not in text
