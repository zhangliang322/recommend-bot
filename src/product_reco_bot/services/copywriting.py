from __future__ import annotations

from product_reco_bot.models import Recommendation


class CopywritingService:
    def private_detail(self, recommendation: Recommendation) -> str:
        product = recommendation.product
        score = recommendation.score
        reasons = "\n".join(f"{index}. {reason}" for index, reason in enumerate(
            recommendation.reasons, start=1
        ))
        audience = "、".join(product.target_audience) or "待确认"
        return (
            f"【{product.product_name}】\n"
            f"类目：{product.category}\n"
            f"火热指数：{score.hot_score:.0f} / 100（{score.hot_label}）\n"
            f"参考价格：{product.currency} {product.price:.2f}\n"
            f"目标客户：{audience}\n\n"
            f"推荐理由：\n{reasons}\n\n"
            f"商品来源：{product.source_platform}\n"
            f"来源链接：{product.source_url or '待补充'}\n"
            f"采购链接：{product.purchase_url}\n"
            f"风险提示：{product.risk_note or '发送前确认价格、库存与链接'}"
        )

    def public_post(self, recommendation: Recommendation) -> str:
        product = recommendation.product
        tags = [product.category, *product.fashion_keywords[:3]]
        hashtags = " ".join(f"#{tag.replace(' ', '')}" for tag in tags if tag)
        audience = "、".join(product.target_audience[:2])
        audience_line = f"适合：{audience}\n" if audience else ""
        return (
            f"今日推荐｜{product.product_name}\n\n"
            f"{recommendation.one_line_selling_point}\n"
            f"{audience_line}"
            f"参考价：{product.currency} {product.price:.2f}\n"
            f"产品链接：{product.purchase_url}\n\n"
            f"{hashtags}"
        )
