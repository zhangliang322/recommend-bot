# 每日精品产品推荐 AstrBot 插件

本插件是 MVP 的机器人接入层，业务逻辑位于项目根目录的 `src/product_reco_bot`。

## 本地接入

1. 在 AstrBot 使用的 Python 环境中执行 `pip install -e <项目根目录>`。
2. 将本目录复制到 AstrBot 的 `data/plugins/astrbot_plugin_product_reco`。
3. 设置环境变量 `PRODUCT_RECO_PROJECT_ROOT=<项目根目录>` 后启动 AstrBot。
4. 在测试群中由管理员发送 `/登记推荐群`，然后发送 `/今日精品`。
5. 用 `/待审商品` 查看候选，使用 `/批准商品 商品ID` 批准自动推送商品。

其他管理员指令：

- `/商品详情 商品ID`：查看完整私域推荐依据。
- `/公域文案 商品ID`：生成精简公域发布文案。
- `/分类推荐 饰品` 或 `/分类推荐 玩具`：按垂类发送最多 3 个推荐。
- `/反馈商品 商品ID 好|一般|差 [备注]`：记录运营反馈。

自动推送启用前，同时把项目 `config/settings.yaml` 中的 `auto_push_enabled` 改为
`true`、`dry_run` 改为 `false`。可通过 `/自动推荐状态` 检查最终状态。

插件会按“产品卡片图片 + 产品链接”的顺序发送。当前数据源为示例 CSV，后续数据采集器无需改动插件代码即可替换。
