from pathlib import Path

from fastapi.testclient import TestClient

from product_reco_bot.management.app import create_app


def test_management_api_lists_recommendations_and_updates_approval(tmp_path: Path) -> None:
    client = TestClient(create_app(Path("."), tmp_path))

    health = client.get("/health")
    recommendations = client.get("/api/recommendations", params={"limit": 2})
    approval = client.post("/api/approvals", json={"product_id": "TOY-001"})
    dashboard = client.get("/")
    card = client.get("/api/cards/TOY-001")

    assert health.json() == {"status": "ok"}
    assert "精品推荐运营台" in dashboard.text
    assert recommendations.status_code == 200
    assert len(recommendations.json()) == 2
    assert card.headers["content-type"] == "image/png"
    assert approval.json()["status"] == "approved"
    assert client.get("/api/approvals").json() == {"product_ids": ["TOY-001"]}


def test_management_api_requires_configured_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRODUCT_RECO_ADMIN_API_KEY", "secret-key")
    client = TestClient(create_app(Path("."), tmp_path))

    assert client.get("/health").status_code == 401
    assert client.get("/health", headers={"X-API-Key": "secret-key"}).status_code == 200
