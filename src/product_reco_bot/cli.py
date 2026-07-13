from __future__ import annotations

import argparse

from product_reco_bot.collectors.factory import build_collector
from product_reco_bot.config import load_app_config, load_score_config
from product_reco_bot.models import PushMessage
from product_reco_bot.services.pipeline import DailyRecommendationPipeline
from product_reco_bot.services.push import DryRunPushService
from product_reco_bot.services.recommendation import RecommendationService
from product_reco_bot.services.scoring import ScoringService


def run_demo() -> int:
    app_config = load_app_config()
    score_config = load_score_config()
    collector = build_collector(app_config)
    recommender = RecommendationService(ScoringService(score_config))
    pipeline = DailyRecommendationPipeline(app_config, collector, recommender)
    pusher = DryRunPushService()

    result = pipeline.run()
    print(
        f"Generated {len(result.recommendations)} recommendations, "
        f"rejected {len(result.rejected)}."
    )
    for item in result.recommendations:
        message = PushMessage(
            target_group="internal-test-group",
            card_image_path=item.card_image_path,
            product_link=item.product.purchase_url,
            dry_run=app_config.dry_run,
        )
        print(pusher.push(message))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run-demo")
    args = parser.parse_args()
    if args.command == "run-demo":
        return run_demo()
    raise ValueError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
