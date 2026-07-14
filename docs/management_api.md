# Management API

The local management API is the backend for a future operator interface. It binds to
`127.0.0.1:8765` by default.

Start it with:

```powershell
reco-admin
```

Set `PRODUCT_RECO_ADMIN_API_KEY` to require the `X-API-Key` request header. Keep the service on
localhost until authentication, TLS, and deployment policy are configured.
The dashboard and static assets remain loadable so the browser can request the key; `/health`
and all `/api/` routes require it. The browser stores the entered key in `sessionStorage` only,
so closing the tab clears it.

Main routes:

- `GET /api/sources`: source status and missing credential field names.
- `PATCH /api/sources/{name}`: enable or disable a configured source.
- `POST /api/sources/{name}/test`: readiness or live connectivity check without returning secret values.
- `GET /api/sources/pdd_duoduo/preview`: normalize a small keyword search result for review.
- `GET /api/sources/{name}/sync-status`: latest local success or sanitized failure record.
- `GET /api/sources/{name}/sync-history`: newest bounded local synchronization records.
- `GET /api/recommendations`: ranked candidates with approval state.
- `GET/POST/DELETE /api/approvals`: approval operations.
- `POST /api/approvals/batch`: approve up to 100 known products with a shared note.
- `GET /api/recommendations/{product_id}`: detail plus private/public copywriting previews.
- `GET /api/feedback` and `/api/feedback/summary`: operator feedback.
- `GET /api/deliveries/latest`: latest successful delivery per product.

Credential values are read from environment variables named in `config/data_sources.yaml`.
They are never persisted in that YAML file or returned by the API.

For `pdd_duoduo`, configure `PDD_CLIENT_ID`, `PDD_CLIENT_SECRET`, and `PDD_PID` in the
process environment. The optional `PDD_API_ENDPOINT` defaults to the Pinduoduo API gateway.
The test route sends a one-item product-search request and returns only connection state or a
sanitized error. Keep the source disabled until this test succeeds.
Synchronization status is stored under the local runtime data directory and is not committed.
