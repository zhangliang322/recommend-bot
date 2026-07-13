# Data Schema

The MVP CSV schema is defined by `ProductCandidate` in `src/product_reco_bot/models.py`.

Required fields:

- `product_id`
- `category`
- `product_name`
- `image_url`
- `purchase_url`
- `source_platform`

Signal fields can be blank and default to zero where safe.

Runtime JSONL stores in the AstrBot plugin data directory:

- `feedback.jsonl`: product ID, rating, operator, group, note, and timestamp.
- `recommendation_history.jsonl`: product ID, target group, and successful send time.
- `delivery_ledger.json`: last completed automatic delivery date per target.
- `approvals.json`: product IDs approved for automatic delivery.
