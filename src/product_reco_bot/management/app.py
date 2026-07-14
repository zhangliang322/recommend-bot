from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel
from starlette.responses import FileResponse, JSONResponse
from starlette.staticfiles import StaticFiles

from product_reco_bot.adapters.approval_store import ApprovalStore
from product_reco_bot.adapters.feedback_store import FeedbackStore
from product_reco_bot.adapters.recommendation_history_store import RecommendationHistoryStore
from product_reco_bot.adapters.source_sync_store import SourceSyncStore
from product_reco_bot.collectors.factory import build_collector
from product_reco_bot.collectors.pdd_collector import PddCollector
from product_reco_bot.config import load_app_config, load_score_config
from product_reco_bot.integrations.pdd import PddClient, PddConnectionError, PddCredentials
from product_reco_bot.management.source_registry import DataSourceRegistry
from product_reco_bot.models import ProductFeedback
from product_reco_bot.services.card_render import CardRenderService
from product_reco_bot.services.copywriting import CopywritingService
from product_reco_bot.services.recommendation import RecommendationService
from product_reco_bot.services.safety import SafetyService
from product_reco_bot.services.scoring import ScoringService


class EnableSourceRequest(BaseModel):
    enabled: bool


class ApprovalRequest(BaseModel):
    product_id: str
    note: str = ""


class BatchApprovalRequest(BaseModel):
    product_ids: list[str]
    note: str = ""


def create_app(
    project_root: Path | None = None,
    state_dir: Path | None = None,
) -> FastAPI:
    root = (project_root or Path(os.getenv("PRODUCT_RECO_PROJECT_ROOT", "."))).resolve()
    runtime_dir = (
        state_dir or Path(os.getenv("PRODUCT_RECO_STATE_DIR", root / "work" / "runtime_data"))
    ).resolve()
    sources = DataSourceRegistry(root / "config" / "data_sources.yaml")
    approvals = ApprovalStore(runtime_dir / "approvals.json")
    feedback = FeedbackStore(runtime_dir / "feedback.jsonl")
    history = RecommendationHistoryStore(runtime_dir / "recommendation_history.jsonl")
    source_sync = SourceSyncStore(runtime_dir / "source_sync_status.json")

    app = FastAPI(
        title="Product Recommendation Management API",
        version="0.1.0",
    )
    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.middleware("http")
    async def protect_management_api(request: Request, call_next):
        expected = os.getenv("PRODUCT_RECO_ADMIN_API_KEY")
        protected = request.url.path == "/health" or request.url.path.startswith("/api/")
        if expected and protected and request.headers.get("X-API-Key") != expected:
            return JSONResponse(status_code=401, content={"detail": "管理密钥无效"})
        return await call_next(request)

    def ranked_recommendations(limit: int, category: str | None = None):
        config = load_app_config(root / "config" / "settings.yaml")
        score_config = load_score_config(root / "config" / "source_weights.yaml")
        products = build_collector(config, root).collect_keywords(limit=100)
        if category:
            products = [product for product in products if product.category == category]
        recommender = RecommendationService(
            ScoringService(score_config, history.last_sent_map())
        )
        return recommender.build_recommendations(products, limit=limit)

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/sources")
    def list_sources():
        latest = source_sync.list_latest()
        return [
            {**status.model_dump(), "last_sync": latest.get(status.name)}
            for status in sources.statuses()
        ]

    @app.patch("/api/sources/{name}")
    def update_source(name: str, request: EnableSourceRequest):
        try:
            current = sources.status(name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="未知数据源") from exc
        if request.enabled and not current.configured:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "凭证未配置完整",
                    "missing": current.missing_credentials,
                },
            )
        return sources.set_enabled(name, request.enabled)

    @app.post("/api/sources/{name}/test")
    def test_source(name: str):
        try:
            status = sources.status(name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="未知数据源") from exc
        result = {
            "name": name,
            "ready": status.enabled and status.configured,
            "configured": status.configured,
            "missing_credentials": status.missing_credentials,
        }
        if name != "pdd_duoduo" or not status.configured:
            return result
        credentials = PddCredentials(
            client_id=os.environ["PDD_CLIENT_ID"],
            client_secret=os.environ["PDD_CLIENT_SECRET"],
            pid=os.environ["PDD_PID"],
        )
        try:
            PddClient(
                credentials,
                endpoint=os.getenv("PDD_API_ENDPOINT", "https://gw-api.pinduoduo.com/api/router"),
            ).test_connection()
        except PddConnectionError as exc:
            source_sync.record(name, False, str(exc))
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        sync = source_sync.record(name, True, "连接测试成功")
        return {**result, "connected": True, "last_sync": sync}

    @app.get("/api/sources/pdd_duoduo/preview")
    def preview_pdd_goods(
        keyword: str = Query(default="饰品", min_length=1, max_length=40),
        limit: int = Query(default=10, ge=1, le=50),
    ):
        status = sources.status("pdd_duoduo")
        if not status.configured:
            raise HTTPException(
                status_code=409,
                detail={"message": "多多进宝凭证未配置完整", "missing": status.missing_credentials},
            )
        credentials = PddCredentials(
            client_id=os.environ["PDD_CLIENT_ID"],
            client_secret=os.environ["PDD_CLIENT_SECRET"],
            pid=os.environ["PDD_PID"],
        )
        client = PddClient(
            credentials,
            endpoint=os.getenv("PDD_API_ENDPOINT", "https://gw-api.pinduoduo.com/api/router"),
        )
        try:
            products = PddCollector(client).collect_keywords([keyword], limit=limit)
        except PddConnectionError as exc:
            source_sync.record("pdd_duoduo", False, str(exc))
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        source_sync.record("pdd_duoduo", True, f"预览同步成功，共 {len(products)} 个商品")
        return products

    @app.get("/api/sources/{name}/sync-status")
    def source_sync_status(name: str):
        try:
            sources.status(name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="未知数据源") from exc
        return source_sync.list_latest().get(name)

    @app.get("/api/recommendations")
    def list_recommendations(
        limit: int = Query(default=20, ge=1, le=100),
        category: str | None = Query(default=None),
    ):
        if category and category not in {"饰品", "玩具"}:
            raise HTTPException(status_code=422, detail="类目仅支持饰品或玩具")
        approved = approvals.list_ids()
        return [
            {
                "product_id": item.product.product_id,
                "category": item.product.category,
                "product_name": item.product.product_name,
                "image_url": item.product.image_url,
                "purchase_url": item.product.purchase_url,
                "price": item.product.price,
                "currency": item.product.currency,
                "hot_score": item.score.hot_score,
                "hot_label": item.score.hot_label,
                "approved": item.product.product_id in approved,
                "reasons": item.reasons,
                "card_url": f"/api/cards/{item.product.product_id}",
            }
            for item in ranked_recommendations(limit, category)
        ]

    @app.get("/api/cards/{product_id}")
    def product_card(product_id: str) -> FileResponse:
        normalized_id = product_id.strip().upper()
        recommendation = next(
            (
                item
                for item in ranked_recommendations(100)
                if item.product.product_id.upper() == normalized_id
            ),
            None,
        )
        if recommendation is None:
            raise HTTPException(status_code=404, detail="未知商品")
        ok, reason = SafetyService().is_pushable(recommendation.product)
        if not ok:
            raise HTTPException(status_code=422, detail=reason)
        config = load_app_config(root / "config" / "settings.yaml")
        output_dir = (
            config.output_dir
            if config.output_dir.is_absolute()
            else root / config.output_dir
        )
        card_path = CardRenderService(output_dir).render(recommendation)
        return FileResponse(card_path, media_type="image/png")

    @app.get("/api/approvals")
    def list_approvals():
        return {"product_ids": sorted(approvals.list_ids()), "records": approvals.records()}

    @app.post("/api/approvals")
    def approve(request: ApprovalRequest) -> dict[str, str]:
        approvals.approve(request.product_id.strip(), request.note.strip())
        return {"product_id": request.product_id.strip(), "status": "approved"}

    @app.post("/api/approvals/batch")
    def approve_batch(request: BatchApprovalRequest):
        product_ids = list(
            dict.fromkeys(item.strip() for item in request.product_ids if item.strip())
        )
        if not product_ids or len(product_ids) > 100:
            raise HTTPException(status_code=422, detail="批量批准数量必须为 1 到 100")
        known_ids = {item.product.product_id for item in ranked_recommendations(100)}
        unknown = [item for item in product_ids if item not in known_ids]
        if unknown:
            raise HTTPException(
                status_code=404, detail={"message": "包含未知商品", "items": unknown}
            )
        for product_id in product_ids:
            approvals.approve(product_id, request.note.strip())
        return {"product_ids": product_ids, "status": "approved", "count": len(product_ids)}

    @app.delete("/api/approvals/{product_id}")
    def revoke(product_id: str) -> dict[str, str]:
        approvals.revoke(product_id.strip())
        return {"product_id": product_id.strip(), "status": "revoked"}

    @app.get("/api/recommendations/{product_id}")
    def recommendation_detail(product_id: str):
        recommendation = next(
            (
                item
                for item in ranked_recommendations(100)
                if item.product.product_id.upper() == product_id.strip().upper()
            ),
            None,
        )
        if recommendation is None:
            raise HTTPException(status_code=404, detail="未知商品")
        copywriting = CopywritingService()
        return {
            "recommendation": recommendation,
            "private_detail": copywriting.private_detail(recommendation),
            "public_post": copywriting.public_post(recommendation),
            "approval": approvals.records().get(recommendation.product.product_id),
        }

    @app.get("/api/feedback")
    def list_feedback() -> list[ProductFeedback]:
        return feedback.list_all()

    @app.get("/api/feedback/summary")
    def feedback_summary() -> dict[str, int]:
        counts = Counter(item.rating for item in feedback.list_all())
        return {rating: counts.get(rating, 0) for rating in ("好", "一般", "差")}

    @app.get("/api/deliveries/latest")
    def latest_deliveries():
        return {
            product_id: sent_at.isoformat()
            for product_id, sent_at in history.last_sent_map().items()
        }

    return app


app = create_app()
