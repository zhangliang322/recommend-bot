# Contributing

## Rules

- Keep robot adapters, business services, data access, and card rendering separate.
- Add tests for scoring, deduplication, safety checks, and card rendering changes.
- Do not hard-code group IDs, tokens, cookies, API keys, or platform credentials.
- Record every third-party dependency in `THIRD_PARTY_NOTICES.md`.

## Local Checks

```powershell
python -m pytest
python -m ruff check src tests
```

