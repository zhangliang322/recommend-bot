# Management API

The local management API is the backend for a future operator interface. It binds to
`127.0.0.1:8765` by default.

Start it with:

```powershell
reco-admin
```

Set `PRODUCT_RECO_ADMIN_API_KEY` to require the `X-API-Key` request header. Keep the service on
localhost until authentication, TLS, and deployment policy are configured.

Main routes:

- `GET /api/sources`: source status and missing credential field names.
- `PATCH /api/sources/{name}`: enable or disable a configured source.
- `POST /api/sources/{name}/test`: readiness check without returning secret values.
- `GET /api/recommendations`: ranked candidates with approval state.
- `GET/POST/DELETE /api/approvals`: approval operations.
- `GET /api/feedback` and `/api/feedback/summary`: operator feedback.
- `GET /api/deliveries/latest`: latest successful delivery per product.

Credential values are read from environment variables named in `config/data_sources.yaml`.
They are never persisted in that YAML file or returned by the API.
