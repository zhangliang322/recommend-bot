from pathlib import Path

from product_reco_bot.desktop.service import DesktopService


def test_desktop_service_lists_details_and_approves(tmp_path: Path) -> None:
    service = DesktopService(Path("."), tmp_path)

    products = service.recommendations(limit=10)
    product_id = str(products[0]["product_id"])
    detail = service.detail(product_id)
    service.approve(product_id, "桌面端审核")

    assert detail["card"].exists()
    assert "采购链接" in detail["private_detail"]
    assert service.approvals.records()[product_id]["note"] == "桌面端审核"


def test_desktop_service_lists_sources(tmp_path: Path) -> None:
    service = DesktopService(Path("."), tmp_path)

    sources = service.source_statuses()

    assert any(source["name"] == "pdd_duoduo" for source in sources)
