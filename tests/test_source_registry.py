from pathlib import Path

from product_reco_bot.management.source_registry import DataSourceRegistry


def test_registry_masks_secrets_and_reports_missing_credentials(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "sources.yaml"
    path.write_text(
        """
sources:
  commerce:
    display_name: Commerce
    enabled: false
    adapter: commerce_api
    capabilities: [product_search]
    credential_env:
      client_id: TEST_CLIENT_ID
      client_secret: TEST_CLIENT_SECRET
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("TEST_CLIENT_ID", "visible-only-to-process")

    status = DataSourceRegistry(path).statuses()[0]

    assert not status.configured
    assert status.missing_credentials == ["client_secret"]
    assert "visible-only-to-process" not in status.model_dump_json()


def test_registry_can_toggle_source(tmp_path: Path) -> None:
    path = tmp_path / "sources.yaml"
    path.write_text(
        """
sources:
  file:
    display_name: File
    enabled: true
    adapter: jsonl
    credential_env: {}
""".strip(),
        encoding="utf-8",
    )
    registry = DataSourceRegistry(path)

    status = registry.set_enabled("file", False)

    assert not status.enabled
    assert not registry.definitions()["file"].enabled
