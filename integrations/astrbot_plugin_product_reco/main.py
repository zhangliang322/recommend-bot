from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import astrbot.api.message_components as Comp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.star import Context, Star

from product_reco_bot.adapters.approval_store import ApprovalStore
from product_reco_bot.adapters.feedback_store import FeedbackStore
from product_reco_bot.adapters.recommendation_history_store import RecommendationHistoryStore
from product_reco_bot.adapters.target_store import PushTargetStore
from product_reco_bot.collectors.factory import build_collector
from product_reco_bot.config import load_app_config, load_score_config
from product_reco_bot.models import ProductFeedback, Recommendation
from product_reco_bot.services.copywriting import CopywritingService
from product_reco_bot.services.pipeline import DailyRecommendationPipeline
from product_reco_bot.services.recommendation import RecommendationService
from product_reco_bot.services.schedule import DeliveryLedger
from product_reco_bot.services.scoring import ScoringService

PLUGIN_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(os.getenv("PRODUCT_RECO_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
STATE_DIR = Path(os.getenv("PRODUCT_RECO_STATE_DIR", PLUGIN_DIR / "data"))


class ProductRecommendationPlugin(Star):
    def __init__(self, context: Context) -> None:
        super().__init__(context)
        self.target_store = PushTargetStore(STATE_DIR / "push_target.json")
        self.approval_store = ApprovalStore(STATE_DIR / "approvals.json")
        self.delivery_ledger = DeliveryLedger(STATE_DIR / "delivery_ledger.json")
        self.feedback_store = FeedbackStore(STATE_DIR / "feedback.jsonl")
        self.history_store = RecommendationHistoryStore(
            STATE_DIR / "recommendation_history.jsonl"
        )
        self.copywriter = CopywritingService()
        self.scheduler = self._start_scheduler()

    def _pipeline(self) -> DailyRecommendationPipeline:
        app_config = load_app_config(PROJECT_ROOT / "config" / "settings.yaml")
        score_config = load_score_config(PROJECT_ROOT / "config" / "source_weights.yaml")
        collector = build_collector(app_config, PROJECT_ROOT)
        app_config.output_dir = PROJECT_ROOT / app_config.output_dir
        recommender = RecommendationService(
            ScoringService(score_config, self.history_store.last_sent_map())
        )
        return DailyRecommendationPipeline(app_config, collector, recommender)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("今日精品")
    async def recommend_today(self, event: AstrMessageEvent):
        """生成并发送今日精品产品卡片与采购链接。"""
        try:
            result = self._pipeline().run()
        except Exception as exc:
            logger.exception("Product recommendation pipeline failed")
            yield event.plain_result(f"生成失败：{exc}")
            return

        if not result.recommendations:
            yield event.plain_result("今天没有通过安全检查的候选产品。")
            return

        for item in result.recommendations:
            chain = [
                Comp.Image.fromFileSystem(str(item.card_image_path)),
                Comp.Plain(f"产品链接：{item.product.purchase_url}"),
            ]
            yield event.chain_result(chain)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("登记推荐群")
    async def register_group(self, event: AstrMessageEvent):
        """把当前会话登记为每日精品推荐目标。"""
        self.target_store.save(event.unified_msg_origin)
        yield event.plain_result("当前会话已登记为每日推荐测试群。")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("推荐群状态")
    async def group_status(self, event: AstrMessageEvent):
        """查看每日推荐目标是否已经登记。"""
        target = self.target_store.load()
        message = f"已登记：{target}" if target else "尚未登记推荐群。"
        yield event.plain_result(message)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("自动推荐状态")
    async def auto_push_status(self, event: AstrMessageEvent):
        """查看自动推荐时间、开关和目标群。"""
        config = load_app_config(PROJECT_ROOT / "config" / "settings.yaml")
        enabled = config.auto_push_enabled and not config.dry_run
        target = self.target_store.load() or "未登记"
        status = "已启用" if enabled else "未启用"
        yield event.plain_result(
            f"自动推荐：{status}\n推送时间：{config.daily_push_time} "
            f"({config.timezone})\n目标：{target}\n"
            f"已批准商品：{len(self.approval_store.list_ids())} 个"
        )

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("待审商品")
    async def pending_products(self, event: AstrMessageEvent):
        """列出今日候选商品及批准状态。"""
        result = self._pipeline().run(limit=20)
        approved = self.approval_store.list_ids()
        if not result.recommendations:
            yield event.plain_result("当前没有待审核商品。")
            return
        lines = [
            f"{'[已批准]' if item.product.product_id in approved else '[待审核]'} "
            f"{item.product.product_id} | {item.product.product_name} | "
            f"{item.score.hot_score:.0f}"
            for item in result.recommendations
        ]
        yield event.plain_result("\n".join(lines))

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("批准商品")
    async def approve_product(self, event: AstrMessageEvent, product_id: str):
        """允许指定商品进入自动推送。"""
        self.approval_store.approve(product_id.strip())
        yield event.plain_result(f"已批准商品：{product_id.strip()}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("撤销批准")
    async def revoke_product(self, event: AstrMessageEvent, product_id: str):
        """撤销指定商品的自动推送资格。"""
        self.approval_store.revoke(product_id.strip())
        yield event.plain_result(f"已撤销批准：{product_id.strip()}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("商品详情")
    async def product_detail(self, event: AstrMessageEvent, product_id: str):
        """查看商品来源、评分依据、采购链接和风险提示。"""
        recommendation = self._find_recommendation(product_id)
        if recommendation is None:
            yield event.plain_result(f"未找到商品：{product_id}")
            return
        yield event.plain_result(self.copywriter.private_detail(recommendation))

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("公域文案")
    async def public_copy(self, event: AstrMessageEvent, product_id: str):
        """生成可发布到公域渠道的精简产品文案。"""
        recommendation = self._find_recommendation(product_id)
        if recommendation is None:
            yield event.plain_result(f"未找到商品：{product_id}")
            return
        yield event.plain_result(self.copywriter.public_post(recommendation))

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("分类推荐")
    async def category_recommendation(self, event: AstrMessageEvent, category: str):
        """按饰品或玩具类目生成推荐卡片。"""
        if category not in {"饰品", "玩具"}:
            yield event.plain_result("类目仅支持：饰品、玩具。")
            return
        result = self._pipeline().run(limit=20)
        selected = [item for item in result.recommendations if item.product.category == category][
            :3
        ]
        if not selected:
            yield event.plain_result(f"当前没有可推荐的{category}商品。")
            return
        for item in selected:
            yield event.chain_result(
                [
                    Comp.Image.fromFileSystem(str(item.card_image_path)),
                    Comp.Plain(f"产品链接：{item.product.purchase_url}"),
                ]
            )

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("反馈商品")
    async def product_feedback(
        self, event: AstrMessageEvent, product_id: str, rating: str, note: str = ""
    ):
        """记录商品反馈，评价仅支持好、一般、差。"""
        if rating not in {"好", "一般", "差"}:
            yield event.plain_result("评价仅支持：好、一般、差。")
            return
        if self._find_recommendation(product_id) is None:
            yield event.plain_result(f"未找到商品：{product_id}")
            return
        feedback = ProductFeedback(
            product_id=product_id,
            rating=rating,
            operator_id=event.get_sender_id(),
            target_group=event.unified_msg_origin,
            note=note,
        )
        self.feedback_store.append(feedback)
        yield event.plain_result(f"已记录 {product_id} 的评价：{rating}")

    def _find_recommendation(self, product_id: str) -> Recommendation | None:
        normalized_id = product_id.strip().upper()
        result = self._pipeline().run(limit=100)
        return next(
            (
                item
                for item in result.recommendations
                if item.product.product_id.upper() == normalized_id
            ),
            None,
        )

    def _start_scheduler(self) -> AsyncIOScheduler:
        config = load_app_config(PROJECT_ROOT / "config" / "settings.yaml")
        hour, minute = (int(value) for value in config.daily_push_time.split(":", maxsplit=1))
        scheduler = AsyncIOScheduler(timezone=config.timezone)
        scheduler.add_job(
            self._auto_push,
            CronTrigger(hour=hour, minute=minute, timezone=config.timezone),
            id="daily-product-recommendation",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=900,
        )
        scheduler.start()
        return scheduler

    async def _auto_push(self) -> None:
        config = load_app_config(PROJECT_ROOT / "config" / "settings.yaml")
        if not config.auto_push_enabled or config.dry_run:
            logger.info("Automatic recommendation skipped: disabled or dry-run")
            return

        target = self.target_store.load()
        if not target:
            logger.warning("Automatic recommendation skipped: no target group")
            return

        day = datetime.now(ZoneInfo(config.timezone)).date()
        if self.delivery_ledger.was_sent(target, day):
            logger.info("Automatic recommendation skipped: already sent today")
            return

        approved_ids = self.approval_store.list_ids()
        result = self._pipeline().run(approved_ids=approved_ids)
        if not result.recommendations:
            logger.warning("Automatic recommendation skipped: no approved products")
            return

        for item in result.recommendations:
            chain = (
                MessageChain()
                .file_image(str(item.card_image_path))
                .message(f"产品链接：{item.product.purchase_url}")
            )
            await self.context.send_message(target, chain)
        self.history_store.record(
            [item.product.product_id for item in result.recommendations], target
        )
        self.delivery_ledger.mark_sent(target, day)
        logger.info("Automatic recommendation delivered to %s", target)

    async def terminate(self) -> None:
        self.scheduler.shutdown(wait=False)
        logger.info("Product recommendation plugin terminated")
