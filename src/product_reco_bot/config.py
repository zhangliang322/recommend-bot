from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    dry_run: bool = True
    data_csv: Path = Path("data/imports/sample_products.csv")
    output_dir: Path = Path("work/generated_cards")
    recommendation_limit: int = 5
    allowed_categories: list[str] = ["饰品", "玩具"]
    auto_push_enabled: bool = False
    daily_push_time: str = "10:00"
    timezone: str = "Asia/Shanghai"
    signal_jsonl_paths: list[Path] = Field(default_factory=list)
    social_window_days: int = 3
    ecommerce_window_days: int = 7
    fashion_window_days: int = 30


class ScoreWeights(BaseModel):
    social: float = 0.35
    sales_growth: float = 0.30
    fashion_trend: float = 0.20
    supply: float = 0.10
    novelty: float = 0.05


class ScoreConfig(BaseModel):
    hot_score: ScoreWeights = ScoreWeights()
    thresholds: dict[str, int] = {
        "burst": 90,
        "high": 80,
        "potential": 70,
        "watch": 60,
    }


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_app_config(path: Path = Path("config/settings.yaml")) -> AppConfig:
    return AppConfig.model_validate(load_yaml(path))


def load_score_config(path: Path = Path("config/source_weights.yaml")) -> ScoreConfig:
    return ScoreConfig.model_validate(load_yaml(path))
