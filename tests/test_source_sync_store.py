from pathlib import Path

from product_reco_bot.adapters.source_sync_store import SourceSyncStore


def test_source_sync_store_records_latest_status(tmp_path: Path) -> None:
    store = SourceSyncStore(tmp_path / "sync.json", history_limit=2)

    store.record("pdd_duoduo", False, "temporary failure")
    latest = store.record("pdd_duoduo", True, "ok")

    assert latest["success"] is True
    assert store.list_latest()["pdd_duoduo"]["message"] == "ok"
    assert [item["success"] for item in store.history("pdd_duoduo")] == [True, False]


def test_source_sync_history_is_bounded(tmp_path: Path) -> None:
    store = SourceSyncStore(tmp_path / "sync.json", history_limit=2)

    for index in range(3):
        store.record("pdd_duoduo", True, str(index))

    assert [item["message"] for item in store.history()] == ["2", "1"]
