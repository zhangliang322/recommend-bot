from __future__ import annotations

import os
from pathlib import Path

from product_reco_bot.adapters.approval_store import ApprovalStore
from product_reco_bot.adapters.recommendation_history_store import RecommendationHistoryStore
from product_reco_bot.adapters.source_sync_store import SourceSyncStore
from product_reco_bot.collectors.factory import build_collector
from product_reco_bot.config import load_app_config, load_score_config
from product_reco_bot.integrations.pdd import PddClient, PddCredentials
from product_reco_bot.management.source_registry import DataSourceRegistry
from product_reco_bot.models import Recommendation
from product_reco_bot.services.card_render import CardRenderService
from product_reco_bot.services.copywriting import CopywritingService
from product_reco_bot.services.recommendation import RecommendationService
from product_reco_bot.services.scoring import ScoringService


class DesktopService:
    def __init__(self, project_root: Path, state_dir: Path | None = None) -> None:
        self.root = project_root.resolve()
        self.state_dir = (
            state_dir
            or Path(os.getenv("PRODUCT_RECO_STATE_DIR", self.root / "work" / "runtime_data"))
        ).resolve()
        self.approvals = ApprovalStore(self.state_dir / "approvals.json")
        self.history = RecommendationHistoryStore(
            self.state_dir / "recommendation_history.jsonl"
        )
        self.sources = DataSourceRegistry(self.root / "config" / "data_sources.yaml")
        self.source_sync = SourceSyncStore(self.state_dir / "source_sync_status.json")
        self._recommendations: dict[str, Recommendation] = {}

    def recommendations(self, limit: int = 100) -> list[dict[str, object]]:
        config = load_app_config(self.root / "config" / "settings.yaml")
        collector = build_collector(config, self.root)
        products = collector.collect_keywords(limit=limit)
        recommender = RecommendationService(
            ScoringService(
                load_score_config(self.root / "config" / "source_weights.yaml"),
                self.history.last_sent_map(),
            )
        )
        recommendations = recommender.build_recommendations(products, limit=limit)
        self._recommendations = {
            item.product.product_id: item for item in recommendations
        }
        approved = self.approvals.list_ids()
        return [
            {
                "product_id": item.product.product_id,
                "name": item.product.product_name,
                "category": item.product.category,
                "price": item.product.price,
                "currency": item.product.currency,
                "score": item.score.hot_score,
                "label": item.score.hot_label,
                "approved": item.product.product_id in approved,
            }
            for item in recommendations
        ]

    def detail(self, product_id: str) -> dict[str, object]:
        item = self._recommendations.get(product_id)
        if item is None:
            self.recommendations()
            item = self._recommendations.get(product_id)
        if item is None:
            raise KeyError(product_id)
        copywriting = CopywritingService()
        config = load_app_config(self.root / "config" / "settings.yaml")
        output_dir = (
            config.output_dir
            if config.output_dir.is_absolute()
            else self.root / config.output_dir
        )
        card = CardRenderService(output_dir).render(item).resolve()
        return {
            "recommendation": item,
            "private_detail": copywriting.private_detail(item),
            "public_post": copywriting.public_post(item),
            "card": card,
            "approval": self.approvals.records().get(product_id),
        }

    def approve(self, product_id: str, note: str = "") -> None:
        self.approvals.approve(product_id, note)

    def revoke(self, product_id: str) -> None:
        self.approvals.revoke(product_id)

    def approve_many(self, product_ids: list[str], note: str = "") -> int:
        known = set(self._recommendations)
        selected = list(dict.fromkeys(item for item in product_ids if item in known))
        for product_id in selected:
            self.approve(product_id, note)
        return len(selected)

    def source_statuses(self) -> list[dict[str, object]]:
        latest = self.source_sync.list_latest()
        return [
            {**status.model_dump(), "last_sync": latest.get(status.name)}
            for status in self.sources.statuses()
        ]

    def set_source_enabled(self, name: str, enabled: bool) -> dict[str, object]:
        status = self.sources.status(name)
        if enabled and not status.configured:
            missing = "、".join(status.missing_credentials)
            raise ValueError(f"凭证未配置完整：{missing}")
        return self.sources.set_enabled(name, enabled).model_dump()

    def test_pdd(self) -> dict[str, object]:
        status = self.sources.status("pdd_duoduo")
        if not status.configured:
            missing = "、".join(status.missing_credentials)
            raise ValueError(f"多多进宝凭证未配置完整：{missing}")
        client = PddClient(
            PddCredentials(
                os.environ["PDD_CLIENT_ID"],
                os.environ["PDD_CLIENT_SECRET"],
                os.environ["PDD_PID"],
            ),
            endpoint=os.getenv(
                "PDD_API_ENDPOINT", "https://gw-api.pinduoduo.com/api/router"
            ),
        )
        try:
            client.test_connection()
        except Exception as exc:
            self.source_sync.record("pdd_duoduo", False, str(exc))
            raise
        return self.source_sync.record("pdd_duoduo", True, "桌面端连接测试成功")

    def sync_history(self, source: str | None = None) -> list[dict[str, object]]:
        return self.source_sync.history(source, 100)
