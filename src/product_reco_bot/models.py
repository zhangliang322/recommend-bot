from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

Category = Literal["饰品", "玩具"]
SignalType = Literal["social", "ecommerce", "fashion"]
FeedbackRating = Literal["好", "一般", "差"]


def parse_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return float(value)


def parse_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    return int(float(value))


class ProductCandidate(BaseModel):
    product_id: str
    category: Category
    product_name: str
    description: str = ""
    image_url: str
    source_platform: str
    source_url: str = ""
    purchase_url: str
    price: float = 0.0
    currency: str = "CNY"
    supplier_name: str = ""
    social_platform: str = ""
    social_keyword: str = ""
    social_views: int = 0
    social_likes: int = 0
    social_comments: int = 0
    social_shares: int = 0
    social_publish_time: datetime | None = None
    sales_7d: int = 0
    sales_growth_rate_7d: float = 0.0
    rank_current: int = 0
    rank_previous: int = 0
    fashion_keywords: list[str] = Field(default_factory=list)
    fashion_source: str = ""
    fashion_publish_time: datetime | None = None
    target_audience: list[str] = Field(default_factory=list)
    risk_note: str = ""

    @field_validator("price", "sales_growth_rate_7d", mode="before")
    @classmethod
    def _coerce_float(cls, value: Any) -> float:
        return parse_float(value)

    @field_validator(
        "social_views",
        "social_likes",
        "social_comments",
        "social_shares",
        "sales_7d",
        "rank_current",
        "rank_previous",
        mode="before",
    )
    @classmethod
    def _coerce_int(cls, value: Any) -> int:
        return parse_int(value)

    @field_validator("fashion_keywords", "target_audience", mode="before")
    @classmethod
    def _split_list(cls, value: Any) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return value
        return [item.strip() for item in str(value).replace(",", ";").split(";") if item.strip()]

    @field_validator("social_publish_time", "fashion_publish_time", mode="before")
    @classmethod
    def _parse_datetime(cls, value: Any) -> datetime | None:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt


class ScoreBreakdown(BaseModel):
    social_score: float
    sales_growth_score: float
    fashion_trend_score: float
    supply_score: float
    novelty_score: float
    hot_score: float
    hot_label: str


class Recommendation(BaseModel):
    product: ProductCandidate
    score: ScoreBreakdown
    reasons: list[str]
    one_line_selling_point: str
    card_image_path: Path | None = None


class PushMessage(BaseModel):
    target_group: str
    card_image_path: Path
    product_link: HttpUrl | str
    dry_run: bool = True


class ExternalSignal(BaseModel):
    signal_id: str
    signal_type: SignalType
    source_platform: str
    source_format: str = "canonical"
    product_id: str = ""
    keyword: str = ""
    title: str = ""
    content_url: str = ""
    image_url: str = ""
    published_at: datetime | None = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    sales_7d: int = 0
    sales_growth_rate_7d: float = 0.0
    rank_current: int = 0
    rank_previous: int = 0

    @field_validator(
        "views",
        "likes",
        "comments",
        "shares",
        "sales_7d",
        "rank_current",
        "rank_previous",
        mode="before",
    )
    @classmethod
    def _coerce_signal_int(cls, value: Any) -> int:
        return parse_int(value)

    @field_validator("sales_growth_rate_7d", mode="before")
    @classmethod
    def _coerce_signal_float(cls, value: Any) -> float:
        return parse_float(value)

    @field_validator("published_at", mode="before")
    @classmethod
    def _parse_signal_datetime(cls, value: Any) -> datetime | None:
        return ProductCandidate._parse_datetime(value)


class ProductFeedback(BaseModel):
    product_id: str
    rating: FeedbackRating
    operator_id: str
    target_group: str
    note: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
