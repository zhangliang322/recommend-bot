from __future__ import annotations

from product_reco_bot.models import ProductCandidate

BLOCKED_TERMS = ("全网第一", "稳赚", "100%安全", "治疗", "仿牌", "盗版")


class SafetyService:
    def is_pushable(self, product: ProductCandidate) -> tuple[bool, str]:
        if not product.purchase_url:
            return False, "missing purchase_url"
        if not product.image_url:
            return False, "missing image_url"
        text = " ".join([product.product_name, product.description, product.risk_note])
        for term in BLOCKED_TERMS:
            if term in text:
                return False, f"blocked term: {term}"
        return True, "ok"

