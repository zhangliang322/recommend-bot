from pathlib import Path

from product_reco_bot.adapters.target_store import PushTargetStore


def test_target_store_round_trip(tmp_path: Path) -> None:
    store = PushTargetStore(tmp_path / "target.json")

    assert store.load() is None
    store.save("wecom:group:123")

    assert store.load() == "wecom:group:123"
