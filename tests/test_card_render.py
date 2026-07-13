from pathlib import Path

from PIL import Image

from product_reco_bot.collectors.csv_collector import CsvCollector
from product_reco_bot.config import load_score_config
from product_reco_bot.services.card_render import CardRenderService
from product_reco_bot.services.recommendation import RecommendationService
from product_reco_bot.services.scoring import ScoringService


def test_card_render_creates_png(tmp_path: Path) -> None:
    products = CsvCollector(Path("data/imports/sample_products.csv")).collect_keywords(limit=1)
    recommendation = RecommendationService(
        ScoringService(load_score_config())
    ).build_recommendations(products, limit=1)[0]

    output = CardRenderService(tmp_path).render(recommendation)

    assert output.exists()
    with Image.open(output) as image:
        assert image.size == (1080, 1440)
