from datetime import date
from pathlib import Path

from product_reco_bot.services.schedule import DeliveryLedger


def test_delivery_ledger_prevents_duplicate_day(tmp_path: Path) -> None:
    ledger = DeliveryLedger(tmp_path / "ledger.json")
    day = date(2026, 7, 13)

    assert not ledger.was_sent("wecom:group:123", day)
    ledger.mark_sent("wecom:group:123", day)

    assert ledger.was_sent("wecom:group:123", day)
    assert not ledger.was_sent("wecom:group:123", date(2026, 7, 14))
