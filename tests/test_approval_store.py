from pathlib import Path

from product_reco_bot.adapters.approval_store import ApprovalStore


def test_approval_store_approve_and_revoke(tmp_path: Path) -> None:
    store = ApprovalStore(tmp_path / "approvals.json")

    store.approve("TOY-001")
    store.approve("ACC-001")
    assert store.list_ids() == {"TOY-001", "ACC-001"}

    store.revoke("TOY-001")
    assert store.list_ids() == {"ACC-001"}
