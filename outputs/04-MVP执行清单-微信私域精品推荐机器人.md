# 微信私域精品推荐机器人 MVP 执行清单

## 1. 最快跑通路线

第一版不要把主要时间花在全自动采集。建议按下面顺序跑通：

1. 参考 AstrBot 插件结构搭项目骨架。
2. 复用成熟库完成配置、调度、数据校验、测试和图片生成。
3. 用 CSV / 表格人工导入商品和趋势数据。
4. 建立评分公式，生成每日推荐池。
5. 生成一图流产品推荐卡片。
6. 在测试微信群中发送“产品主图卡片 + 产品链接”。
7. 补充公域文案、定时任务和管理员预览。
8. 连续跑 7 天，记录反馈并调权。
9. 再接入自动数据源。

## 2. 模块化拼接清单

| 能力 | 参考 / 复用 |
| --- | --- |
| 插件和机器人框架 | AstrBotDevs/AstrBot |
| 微信适配备选 | wechaty/wechaty |
| Python 机器人事件模型备选 | nonebot/nonebot2 |
| 定时任务 | APScheduler |
| 数据模型和配置校验 | Pydantic |
| 数据库访问 | SQLAlchemy / SQLModel |
| 图片卡片 | Pillow，复杂排版再考虑 Playwright 截图 |
| 测试 | pytest |
| 代码格式和检查 | Ruff / Black / pre-commit |
| TikTok 数据 | TikTok-Api、TikHub、EnsembleData、Apify Actor |
| Instagram 数据 | Instaloader、Apify Actor、SerpApi |
| 小红书数据 | MediaCrawler |
| 电商数据 | 官方联盟 API、SerpApi Shopping、Scrapy、Crawlee |

要求：

- 不从零开发调度器、ORM、配置校验、测试框架、图片基础渲染能力。
- 不从零开发 TikTok、Instagram、小红书和电商平台采集能力；优先接已有项目、API 或人工导入。
- 不直接复制开源项目代码，除非确认许可证兼容并记录来源。
- 每个外部依赖都写入 `THIRD_PARTY_NOTICES.md`。
- 项目启动时必须同时建立 `README.md`、`.env.example`、`CONTRIBUTING.md`、`CHANGELOG.md`。

## 3. 数据源复用优先级

| 数据源 | 第一选择 | 第二选择 | MVP 兜底 |
| --- | --- | --- | --- |
| TikTok | TikTok-Api 或第三方 API | Apify / Crawlee 自建采集器 | CSV 导入热点视频和话题 |
| Instagram | Instaloader 或第三方 API | Apify / SerpApi | CSV 导入帖子和标签 |
| 小红书 | MediaCrawler | Playwright 定制采集器 | CSV 导入笔记和关键词 |
| Amazon / Google Shopping | 官方 API / SerpApi Shopping | Scrapy / Crawlee | CSV 导入榜单和商品 |
| 1688 / 淘宝 / 拼多多 | 官方开放平台 / 联盟 API | 第三方商品 API | CSV 导入采购链接 |
| AliExpress | Affiliate API | 第三方 API | CSV 导入商品和链接 |
| Temu / SHEIN | 第三方 API 或榜单源 | 通用采集框架 | CSV 导入 |

统一要求：

- 每个数据源都实现同一套 `CollectorAdapter` 接口。
- 每条数据保存 `raw_json`，方便回溯。
- 自动采集失败时，不影响手动 CSV 导入和每日推荐。
- 采集器必须有开关、限流、错误日志和健康检查。

## 4. MVP 第一周任务

| 天数 | 目标 | 交付物 |
| --- | --- | --- |
| D1 | 项目骨架和配置 | 参考 AstrBot 的插件目录、配置文件、数据表结构、README、依赖说明 |
| D2 | 商品导入和评分 | CSV 导入、CollectorAdapter 接口、商品标准化、HotScore 计算 |
| D3 | 推荐池和卡片模板 | 一图流卡片、Top N 推荐 |
| D4 | 机器人指令 | 今日推荐、饰品推荐、玩具推荐、详情、刷新、卡片重生成 |
| D5 | 图片发送、定时和风控 | 图片卡片 + 链接发送、定时预览、白名单、限流、暂停、日志 |
| D6 | 测试数据跑通 | 饰品和玩具各 10-20 条样本，完整生成推荐 |
| D7 | 灰度试运行 | 测试群每日推送，人工反馈，修正权重 |

## 5. 第一版样本数据字段

建议先准备一个 `products.csv`：

```text
product_id
category
product_name
description
image_url
card_image_url
source_platform
source_url
purchase_url
price
currency
supplier_name
social_platform
social_keyword
social_views
social_likes
social_comments
social_shares
social_publish_time
sales_7d
sales_growth_rate_7d
rank_current
rank_previous
fashion_keywords
fashion_source
fashion_publish_time
target_audience
risk_note
```

## 6. 第一版推荐模板

### 一图流卡片模板

```text
顶部：{category}｜火热指数 {hot_score}｜{hot_label}

主体：{product_image}

标题：{product_name}

卖点：{one_line_selling_point}

推荐理由：
1. {reason_1}
2. {reason_2}
3. {reason_3}

来源：{source_summary}

风险提示：{risk_note}
```

### 微信发送模板

```text
[图片] {card_image_url}

产品链接：
{purchase_url}
```

### 公域模板

```text
{product_name} 最近很适合关注。

{public_copy}

推荐标签：
{hashtags}
```

## 7. 最小指令集

必须先实现：

```text
/reco today
/reco category 饰品
/reco category 玩具
/reco detail 商品ID
/reco card 商品ID
/reco refresh
/reco push private
/reco push public
/reco pause
/reco resume
```

可后置：

```text
/reco config
/reco blacklist
/reco feedback
换一批
为什么推荐这个
```

## 8. 第一版判定规则

商品进入推荐池必须满足：

- 类目为饰品或玩具。
- 至少有一个有效趋势来源。
- 采购链接可用或可人工补充。
- 产品主图可用，或者能使用备用主图。
- 不在黑名单中。
- 不含敏感词、侵权风险词。
- 同一群 3 天内未推送过同款商品。

排序规则：

1. HotScore 高的优先。
2. 多来源命中的优先。
3. 采购可行性高的优先。
4. 过去 14 天未推荐的优先。
5. 管理员人工置顶优先。

## 9. 灰度测试安排

测试群建议：

- 1 个内部运营群。
- 1 个小范围私域客户群。
- 先关闭自动大范围群发。
- 前 7 天使用管理员预览确认后发送。

每日观察：

- 今日是否按时生成推荐。
- 是否有错类商品。
- 是否有无效链接。
- 一图流卡片是否清晰、美观、手机端可读。
- 产品主图是否准确、无严重裁切。
- 文案是否夸大或不自然。
- 群成员是否有负反馈。
- 运营是否愿意采纳推荐。

## 10. 下一阶段升级

MVP 稳定后再做：

- 自动接入小红书 / TikTok / Instagram 热点。
- 自动接入 1688、拼多多、AliExpress 等商品数据。
- 建立 Web 管理后台。
- 加入客户画像和群画像。
- 统计点击、咨询、成交反馈。
- 用真实反馈动态调整评分权重。
