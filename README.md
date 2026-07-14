# 微信私域精品推荐机器人 MVP

这是第一版可运行骨架：从 CSV 导入饰品 / 玩具商品与趋势信号，计算火热指数，生成推荐池，渲染一图流卡片，并用 dry-run 模拟微信群推送。

## 快速运行

```powershell
$env:PYTHONPATH="src"
python -m product_reco_bot.cli run-demo
```

输出会生成到：

```text
work/generated_cards/
```

## 测试

```powershell
python -m pytest
python -m ruff check .
```

## 当前能力

- CSV 商品与趋势数据导入。
- 统一 `CollectorAdapter` 采集器接口。
- 规则评分 `HotScore`。
- 推荐池 Top N。
- 一图流 PNG 卡片生成。
- 产品链接 dry-run 推送。
- AstrBot 插件入口，支持 `/今日精品` 生成图片与链接消息链。
- 测试群登记与状态查询，为定时主动推送保存会话目标。
- APScheduler 每日自动推送、每日防重复发送。
- 商品人工批准与撤销，自动推送只发送已批准商品。
- JSONL 外部信号桥接，兼容社媒、电商和时尚趋势导入。
- 社媒 3 天、电商 7 天、时尚 30 天有效窗口。
- 私域商品详情、公域精简文案和按类目推荐。
- 好、一般、差运营反馈记录和正式推送历史。
- 近 14 天推荐新鲜度控制，降低商品重复推送概率。
- 本地管理 API，统一提供数据源、候选、审核、反馈和推送记录。
- 数据源凭证只通过环境变量引用，接口不会返回密钥实际值。
- 多多进宝商品搜索、推广链接生成、连接测试和商品预览适配器。
- 数据源最近同步状态与脱敏错误记录。
- 商品详情与公域/私域文案预览、审核备注和批量批准。

## 本地管理接口

安装项目后执行 `reco-admin`，然后打开 `http://127.0.0.1:8765/` 使用中文运营界面。
接口调试页位于 `http://127.0.0.1:8765/docs`。
建议设置 `PRODUCT_RECO_ADMIN_API_KEY`，管理服务默认只监听本机。

多多进宝联调前，在本机进程环境中设置 `PDD_CLIENT_ID`、`PDD_CLIENT_SECRET` 和
`PDD_PID`，先在“数据源”页面执行连接测试和商品预览。确认结果后再将
`config/settings.yaml` 中的 `product_source` 从 `csv` 改为 `pdd`。不要将真实值写入
`.env.example`、YAML、源码或 Git 提交。

## 目录

```text
src/product_reco_bot/
  adapters/          机器人框架适配层
  collectors/        CSV 和后续平台采集器
  services/          评分、推荐、卡片、推送、风控
  cli.py             本地演示入口
integrations/
  astrbot_plugin_product_reco/  AstrBot 插件入口
```

AstrBot 安装与测试步骤见 `integrations/astrbot_plugin_product_reco/README.md`，详细需求和开发文档在 `outputs/`。
