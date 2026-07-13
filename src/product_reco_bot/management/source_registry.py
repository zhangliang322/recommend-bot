from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class DataSourceDefinition(BaseModel):
    display_name: str
    enabled: bool = False
    adapter: str
    capabilities: list[str] = Field(default_factory=list)
    credential_env: dict[str, str] = Field(default_factory=dict)


class DataSourceStatus(BaseModel):
    name: str
    display_name: str
    enabled: bool
    adapter: str
    capabilities: list[str]
    configured: bool
    missing_credentials: list[str]


class DataSourceRegistry:
    def __init__(self, path: Path) -> None:
        self.path = path

    def definitions(self) -> dict[str, DataSourceDefinition]:
        if not self.path.exists():
            return {}
        data = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        sources = data.get("sources", {})
        return {
            str(name): DataSourceDefinition.model_validate(value)
            for name, value in sources.items()
        }

    def statuses(self) -> list[DataSourceStatus]:
        return [self.status(name, definition) for name, definition in self.definitions().items()]

    def status(
        self, name: str, definition: DataSourceDefinition | None = None
    ) -> DataSourceStatus:
        source = definition or self.definitions().get(name)
        if source is None:
            raise KeyError(name)
        missing = [
            field_name
            for field_name, env_name in source.credential_env.items()
            if not os.getenv(env_name)
        ]
        return DataSourceStatus(
            name=name,
            display_name=source.display_name,
            enabled=source.enabled,
            adapter=source.adapter,
            capabilities=source.capabilities,
            configured=not missing,
            missing_credentials=missing,
        )

    def set_enabled(self, name: str, enabled: bool) -> DataSourceStatus:
        definitions = self.definitions()
        if name not in definitions:
            raise KeyError(name)
        definitions[name].enabled = enabled
        payload = {
            "sources": {
                source_name: definition.model_dump(mode="json")
                for source_name, definition in definitions.items()
            }
        }
        self.path.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        return self.status(name, definitions[name])
