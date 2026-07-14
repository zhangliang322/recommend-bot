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
    approvals = client.get("/api/approvals").json()
    assert approvals["product_ids"] == ["TOY-001"]
    assert approvals["records"]["TOY-001"]["note"] == ""


def test_management_api_detail_and_batch_approval(tmp_path: Path) -> None:
    client = TestClient(create_app(Path("."), tmp_path))

    detail = client.get("/api/recommendations/TOY-001")
    batch = client.post(
        "/api/approvals/batch",
        json={"product_ids": ["TOY-001", "ACC-001"], "note": "批量初审通过"},
    )

    assert detail.status_code == 200
    assert "产品链接" in detail.json()["public_post"]
    assert batch.json()["count"] == 2
    assert client.get("/api/approvals").json()["records"]["ACC-001"]["note"] == "批量初审通过"


def test_management_api_requires_configured_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRODUCT_RECO_ADMIN_API_KEY", "secret-key")
    client = TestClient(create_app(Path("."), tmp_path))

    assert client.get("/health").status_code == 401
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/api/sources").status_code == 401
    assert client.get("/health", headers={"X-API-Key": "secret-key"}).status_code == 200


def test_pdd_test_reports_missing_credentials(tmp_path: Path, monkeypatch) -> None:
    for name in ("PDD_CLIENT_ID", "PDD_CLIENT_SECRET", "PDD_PID"):
        monkeypatch.delenv(name, raising=False)
    client = TestClient(create_app(Path("."), tmp_path))

    response = client.post("/api/sources/pdd_duoduo/test")

    assert response.status_code == 200
    assert response.json()["configured"] is False
    assert response.json()["missing_credentials"] == ["client_id", "client_secret", "pid"]


def test_pdd_test_connects_without_exposing_credentials(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PDD_CLIENT_ID", "client-id")
    monkeypatch.setenv("PDD_CLIENT_SECRET", "super-secret")
    monkeypatch.setenv("PDD_PID", "pid")
    monkeypatch.setattr(
        "product_reco_bot.management.app.PddClient.test_connection",
        lambda self: {"goods_search_response": {"total_count": 0}},
    )
    client = TestClient(create_app(Path("."), tmp_path))

    response = client.post("/api/sources/pdd_duoduo/test")

    assert response.status_code == 200
    assert response.json()["connected"] is True
    assert "super-secret" not in response.text


def test_pdd_preview_returns_normalized_products(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PDD_CLIENT_ID", "client-id")
    monkeypatch.setenv("PDD_CLIENT_SECRET", "super-secret")
    monkeypatch.setenv("PDD_PID", "pid")
    monkeypatch.setattr(
        "product_reco_bot.management.app.PddCollector.collect_keywords",
        lambda self, keywords, limit: [],
    )
    client = TestClient(create_app(Path("."), tmp_path))

    response = client.get(
        "/api/sources/pdd_duoduo/preview", params={"keyword": "玩具", "limit": 3}
    )

    assert response.status_code == 200
    assert response.json() == []
