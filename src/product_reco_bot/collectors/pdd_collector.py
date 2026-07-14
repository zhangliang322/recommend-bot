from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from product_reco_bot.collectors.base import CollectorAdapter
from product_reco_bot.integrations.pdd import PddClient
from product_reco_bot.models import Category, ProductCandidate


class PddCollector(CollectorAdapter):
    name = "pdd-duoduo"
    platform = "pdd_duoduo"
    supported_modes = ("keywords", "product_search")

    def __init__(
        self,
        client: PddClient,
        generate_promotion_links: bool = True,
        default_keywords: list[str] | None = None,
    ) -> None:
        self.client = client
        self.generate_promotion_links = generate_promotion_links
        self.default_keywords = default_keywords or ["饰品", "玩具"]
        self._current_keyword = ""

    def collect_keywords(
        self, keywords: list[str] | None = None, since: datetime | None = None, limit: int = 50
    ) -> list[ProductCandidate]:
        del since  # The provider does not expose a stable publish timestamp for goods search.
        search_terms = keywords or self.default_keywords
        products: list[ProductCandidate] = []
        seen: set[str] = set()
        for keyword in search_terms:
            self._current_keyword = keyword
            response = self.client.search_goods(
                keyword, page=1, page_size=min(100, max(1, limit - len(products)))
            )
            goods = response.get("goods_search_response", {}).get("goods_list", [])
            for item in goods:
                if self.generate_promotion_links and item.get("goods_sign"):
                    item = {**item, "promotion_url": self._promotion_url(str(item["goods_sign"]))}
                product = self.normalize(item)
                if product.product_id in seen:
                    continue
                seen.add(product.product_id)
                products.append(product)
                if len(products) >= limit:
                    return products
        return products

    def normalize(self, raw_item: dict[str, Any]) -> ProductCandidate:
        goods_id = str(raw_item.get("goods_id") or raw_item.get("goods_sign") or "").strip()
        if not goods_id:
            raise ValueError("多多进宝商品缺少 goods_id 或 goods_sign")
        name = str(raw_item.get("goods_name") or "未命名商品").strip()
        image_url = str(
            raw_item.get("goods_image_url") or raw_item.get("goods_thumbnail_url") or ""
        ).strip()
        if not image_url:
            raise ValueError(f"多多进宝商品 {goods_id} 缺少图片")
        category = self._category(name, self._current_keyword)
        sales = self._sales_count(raw_item.get("sales_tip"))
        direct_url = f"https://mobile.yangkeduo.com/goods.html?goods_id={goods_id}"
        return ProductCandidate(
            product_id=f"PDD-{goods_id}",
            category=category,
            product_name=name,
            description=str(raw_item.get("goods_desc") or "").strip(),
            image_url=image_url,
            source_platform=self.platform,
            source_url=direct_url,
            purchase_url=str(raw_item.get("promotion_url") or direct_url),
            price=float(raw_item.get("min_group_price") or 0) / 100,
            currency="CNY",
            supplier_name=str(raw_item.get("mall_name") or "").strip(),
            social_keyword=self._current_keyword,
            sales_7d=sales,
            target_audience=["微信私域客户"],
        )

    def _promotion_url(self, goods_sign: str) -> str:
        response = self.client.promotion_url(goods_sign)
        items = response.get("goods_promotion_url_generate_response", {}).get(
            "goods_promotion_url_list", []
        )
        if not items:
            return ""
        item = items[0]
        return str(
            item.get("mobile_short_url")
            or item.get("mobile_url")
            or item.get("short_url")
            or item.get("url")
            or ""
        )

    @staticmethod
    def _category(name: str, keyword: str) -> Category:
        toy_words = ("玩具", "积木", "毛绒", "公仔", "手办", "模型", "益智")
        if keyword == "玩具" or any(word in name for word in toy_words):
            return "玩具"
        return "饰品"

    @staticmethod
    def _sales_count(value: Any) -> int:
        text = str(value or "").strip().replace(",", "")
        match = re.search(r"([\d.]+)\s*([万千]?)", text)
        if not match:
            return 0
        multiplier = {"": 1, "千": 1_000, "万": 10_000}[match.group(2)]
        return int(float(match.group(1)) * multiplier)
