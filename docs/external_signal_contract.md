# External Signal Import Contract

External collectors and APIs write newline-delimited JSON (`.jsonl`). Each line is one
social, ecommerce, or fashion signal. The recommendation service reads the files listed in
`config/settings.yaml` under `signal_jsonl_paths`.

Required fields:

- `signal_type`: `social`, `ecommerce`, or `fashion`.
- `source_platform`: for example `tiktok`, `xiaohongshu`, `instagram`, or an ecommerce name.

Recommended identity fields:

- `signal_id`: unique source record ID.
- `product_id`: preferred deterministic link to an imported product.
- `keyword`: fallback product matching term when `product_id` is unavailable.
- `source_format`: producer name such as `MediaCrawler`, `TikTok-Api`, or `Instaloader`.

Supported social aliases include `platform`, `hashtag`, `note_title`, `desc`, `post_url`,
`liked_count`, `comment_count`, `share_count`, `cover_url`, and `publish_time`.

Freshness windows default to three days for social signals, seven days for ecommerce signals,
and thirty days for fashion signals. They are configurable in `config/settings.yaml`.
