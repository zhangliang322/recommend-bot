from pathlib import Path

from product_reco_bot.adapters.source_sync_store import SourceSyncStore


def test_source_sync_store_records_latest_status(tmp_path: Path) -> None:
    store = SourceSyncStore(tmp_path / "sync.json")

    store.record("pdd_duoduo", False, "temporary failure")
    latest = store.record("pdd_duoduo", True, "ok")

    assert latest["success"] is True
    assert store.list_latest()["pdd_duoduo"]["message"] == "ok"
