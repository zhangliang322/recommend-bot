# Ops Runbook

## Dry Run

Run the demo locally before sending any real message:

```powershell
python -m product_reco_bot.cli run-demo
```

## Safety

- Keep `dry_run=true` until the target group whitelist is verified.
- Keep `auto_push_enabled=false` until the AstrBot test group is registered.
- Automatic delivery requires both `auto_push_enabled=true` and `dry_run=false`.
- Automatic delivery sends only product IDs explicitly approved with `/批准商品`.
- Reload the plugin after changing `daily_push_time` or `timezone`.
- If card rendering fails, send product image, product link, and short text only.
- If a product link is missing or invalid, do not auto-push.

## Gray Release

1. Run `/登记推荐群` in the internal test group.
2. Run `/今日精品` and verify every image and purchase link.
3. Run `/待审商品`, then approve selected IDs with `/批准商品 商品ID`.
4. Check `/自动推荐状态`.
5. Set `auto_push_enabled=true` and `dry_run=false`, then reload the plugin.
6. After the scheduled delivery, verify `data/delivery_ledger.json` was updated.
