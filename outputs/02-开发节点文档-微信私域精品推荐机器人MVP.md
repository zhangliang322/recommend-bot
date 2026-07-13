# 微信私域精品推荐机器人 MVP 开发节点文档

## 1. 技术目标

构建一个参考 AstrBot 插件式架构的微信机器人 MVP，用于每日向私域客户群推送饰品、玩具两个测试垂类的精品产品推荐。

核心能力：

- 每日生成推荐清单。
- 支持私域详细推荐和公域短文案。
- 支持一图流推荐卡片生成，消息内以产品主图卡片 + 产品链接为主要呈现。
- 支持微信群定时推送和关键词触发。
- 支持管理员预览、手动刷新、手动推送、反馈记录。
- 推荐评分综合社媒热点、电商销量增长、时尚趋势、采购可行性、新鲜度。

## 2. 架构原则

- 机器人层只负责消息、指令、定时任务、平台适配。
- 推荐业务层独立于 AstrBot，方便测试和迁移。
- MVP 先支持手动数据导入，再逐步接入自动采集。
- 所有推荐结果必须可解释、可追溯。
- 默认先走管理员预览，减少误发和微信风控风险。
- 优先复用 GitHub 上成熟项目和稳定库进行模块化拼接，不从头开发通用基础设施。
- 参考开源项目时只借鉴架构、目录、插件模式和工程规范；直接复用代码前必须检查许可证兼容性。

## 3. 开源项目参考与模块化拼接策略

| 模块 | 优先参考 / 复用 | 用法 |
| --- | --- | --- |
| 机器人主框架 | AstrBotDevs/AstrBot | 优先参考插件机制、多平台 IM 接入、WebUI、Docker、配置、测试和 pre-commit 结构 |
| 微信机器人备选 | wechaty/wechaty | 如果 AstrBot 的微信接入不满足需求，可评估 Wechaty 的微信生态和 Puppet 适配 |
| Python 机器人备选 | nonebot/nonebot2 | 参考异步事件、命令路由、插件化组织方式 |
| 定时任务 | APScheduler | 用于每日采集、评分、卡片生成、预览和推送任务 |
| 数据库 ORM | SQLAlchemy / SQLModel | 管理商品、信号、推荐、日志、群配置等结构化数据 |
| 数据校验 | Pydantic | 定义导入数据、推荐结果、配置文件的数据模型 |
| 图片卡片生成 | Pillow 或 Playwright HTML 截图 | 生成一图流 PNG；MVP 可用 Pillow，复杂排版再升级 HTML 模板截图 |
| 后台接口 | FastAPI | 后续需要管理后台时复用，不在 MVP 第一阶段强制实现 |
| 测试 | pytest | 覆盖评分、去重、卡片渲染、风控、数据导入 |
| 代码规范 | Ruff / Black / pre-commit | 保证格式、导入顺序、基础静态检查一致 |

参考仓库：

- AstrBot: https://github.com/AstrBotDevs/AstrBot
- Wechaty: https://github.com/wechaty/wechaty
- NoneBot2: https://github.com/nonebot/nonebot2
- APScheduler: https://github.com/agronholm/apscheduler
- TikTok-Api: https://github.com/davidteather/TikTok-Api
- Instaloader: https://github.com/instaloader/instaloader
- MediaCrawler: https://github.com/NanmiCoder/MediaCrawler
- Crawlee: https://github.com/apify/crawlee
- Scrapy: https://github.com/scrapy/scrapy
- SerpApi Python SDK: https://github.com/serpapi/google-search-results-python

许可证注意：

- AstrBot 当前仓库显示为 AGPL-3.0 许可证。若直接复制其代码或深度派生，需要单独评估开源义务。
- 本项目建议优先“参考架构和插件边界”，业务代码自行实现，避免许可证不清导致后续商业化受限。
- 每个第三方库必须在 `THIRD_PARTY_NOTICES.md` 中记录名称、用途、版本、许可证和仓库地址。

## 4. 核心模块

| 模块 | 职责 |
| --- | --- |
| 数据采集模块 | 拉取或导入社媒、电商、时尚趋势数据 |
| 商品标准化模块 | 将不同来源商品、话题、关键词统一成候选商品 |
| 热度评分模块 | 计算 SocialScore、SalesGrowthScore、FashionTrendScore、SupplyScore、NoveltyScore |
| 推荐生成模块 | 按垂类、评分、去重、黑名单生成每日推荐池 |
| 文案生成模块 | 生成私域详细卡片和公域种草文案 |
| 图片卡片生成模块 | 基于产品主图、火热指数、卖点、来源生成一图流推荐图 |
| 机器人交互模块 | 接收指令、返回结果、定时推送、记录反馈 |
| 审核与风控模块 | 白名单、限流、敏感词、黑名单、一键暂停 |

## 5. 数据源接入策略

### 5.0 数据采集复用原则

数据源接入不从零写爬虫。每个平台先做统一采集适配器接口，再按稳定性接入 GitHub 上成熟项目、官方 API、第三方 API 或人工导入。

统一接口：

```text
CollectorAdapter
  name
  platform
  supported_modes
  collect_keywords(keywords, since, limit)
  collect_product(product_url_or_id)
  normalize(raw_item)
  health_check()
```

每个采集适配器必须输出统一信号结构：

```text
source_platform
source_type
keyword
title
description
content_url
image_url
product_url
publish_time
collected_at
metrics_json
raw_json
license_or_terms_note
```

优先级：

1. 官方 API / 联盟 API。
2. 成熟第三方 API，例如 SerpApi、Apify Actor、TikHub、EnsembleData 等。
3. GitHub 成熟开源采集项目。
4. 浏览器自动化采集。
5. 人工 CSV / 表格导入兜底。

注意：

- 社媒和电商平台规则变化频繁，所有采集器必须可开关、可替换。
- MVP 必须保留 CSV 导入，不把自动采集作为唯一数据入口。
- 不采集私密内容，不绕过登录权限，不抓取个人隐私数据。
- 每个采集器都要记录来源、版本、许可证、平台条款风险。

### 5.1 社媒热点，3 日窗口

目标平台：

- TikTok
- Instagram
- 小红书

MVP 策略：

- 第一版允许人工整理 CSV / 表格导入。
- 可接第三方数据服务、官方 API、开源采集器或爬虫代理，但不把自动抓取作为 MVP 阻塞项。
- 以关键词、话题、爆款内容为主，不采集用户隐私数据。

候选复用项目：

| 平台 | 候选项目 / 接口 | 适用方式 | 注意事项 |
| --- | --- | --- | --- |
| TikTok | davidteather/TikTok-Api | Python 非官方 API，可抓取趋势、视频、用户公开信息 | 依赖 Playwright / ms_token，平台变更会导致失效 |
| TikTok | TikHub / EnsembleData / Apify Actor | 第三方 API，适合生产兜底 | 有成本，需审查数据来源和合规条款 |
| Instagram | instaloader/instaloader | 下载公开资料、图片、视频、caption、metadata | 非官方项目，注意登录态、频率和平台条款 |
| Instagram | Apify Instagram Scraper / SerpApi | 第三方 API 或搜索结果数据 | 成本较高，但稳定性通常好于自建爬虫 |
| 小红书 | NanmiCoder/MediaCrawler | 支持小红书关键词、帖子、评论等公开信息采集 | 依赖 Playwright 登录态，合规和稳定性需重点评估 |
| 多平台 | apify/crawlee | 通用 Node.js 爬虫框架，支持代理、会话和 Playwright / Puppeteer | 适合自建复杂采集器，不适合作为第一周阻塞项 |

建议字段：

```text
platform
keyword
hashtag
post_url
title
description
like_count
comment_count
share_count
view_count
publish_time
category
related_product_name
image_url
```

### 5.2 电商销量增长，7 日窗口

目标平台：

- Amazon
- TikTok Shop
- AliExpress
- Temu
- SHEIN
- 1688 / 淘宝 / 拼多多
- Shopee / Lazada，后续扩展

MVP 策略：

- 优先接入可获得采购链接的平台，如 1688、淘宝联盟、拼多多联盟、AliExpress Affiliate。
- 对无法获得真实销量的平台，用榜单排名变化、评论增长、收藏增长、进入榜单时间作为替代指标。
- 优先复用官方开放平台、联盟 API、第三方商品搜索 API 和成熟爬虫框架。

候选复用项目 / 接口：

| 平台 | 候选项目 / 接口 | 适用方式 | 注意事项 |
| --- | --- | --- | --- |
| Amazon | Amazon Product Advertising API / SerpApi Shopping | 获取商品、价格、评分、榜单或搜索结果 | PA-API 需要资质；SerpApi 有成本 |
| AliExpress | AliExpress Affiliate API / python-aliexpress-api 类 SDK | 商品搜索、联盟链接、价格 | 优先官方联盟 API |
| 1688 / 淘宝 | 阿里开放平台、淘宝联盟 API | 商品链接、价格、佣金、供应商 | 需要账号资质和签名鉴权 |
| 拼多多 | 多多进宝开放平台 | 商品、佣金、推广链接 | 需要开放平台账号 |
| Temu / SHEIN | 第三方搜索 API、榜单数据、人工导入 | MVP 先人工导入或第三方 API | 官方开放能力有限 |
| 通用电商网页 | Scrapy / Crawlee / Playwright | 自建采集器兜底 | 需要限流、代理、反封禁和合规评估 |

建议字段：

```text
platform
product_id
product_name
product_url
purchase_url
price
currency
sales_7d
sales_growth_rate_7d
rank_current
rank_previous
rating
review_count
supplier_name
min_order_quantity
shipping_region
image_url
category
```

### 5.3 国际时尚大会 / 杂志趋势

目标来源：

- Vogue
- Elle
- Harper's Bazaar
- WWD
- Fashion Week 官方报道
- Pinterest Trends
- Google Trends
- TrendHunter / WGSN，预算允许后再接

MVP 策略：

- 初期用公开网页、RSS、人工维护趋势关键词表。
- 不直接追求商品级，先落到趋势标签级。
- 抽取颜色、材质、风格、单品、场景关键词。

趋势标签示例：

```text
银色金属感
Y2K
蝴蝶结
珍珠
毛绒挂件
多巴胺配色
芭蕾风
复古玩具
```

## 6. 评分公式

综合火热指数：

```text
HotScore =
  SocialScore * 0.35
+ SalesGrowthScore * 0.30
+ FashionTrendScore * 0.20
+ SupplyScore * 0.10
+ NoveltyScore * 0.05
```

社媒热度分：

```text
SocialScore =
  normalized(view_count) * 0.35
+ normalized(like_count) * 0.25
+ normalized(comment_count) * 0.15
+ normalized(share_count) * 0.15
+ recency_score * 0.10

recency_score = max(0, 1 - hours_since_publish / 72)
```

销量增长分：

```text
SalesGrowthScore =
  normalized(sales_growth_rate_7d) * 0.50
+ normalized(sales_7d) * 0.25
+ rank_rise_score * 0.15
+ review_growth_score * 0.10
```

时尚趋势分：

```text
FashionTrendScore =
  trend_keyword_match_score * 0.50
+ source_authority_score * 0.30
+ trend_recency_score * 0.20
```

采购可行性分：

```text
SupplyScore =
  purchase_link_available * 0.30
+ price_margin_score * 0.25
+ supplier_rating_score * 0.20
+ shipping_score * 0.15
+ min_order_score * 0.10
```

新鲜度分：

```text
1.0：过去 14 天未推荐
0.6：过去 7-14 天推荐过
0.2：过去 7 天内推荐过
```

火热指数展示：

| 分数 | 标签 |
| --- | --- |
| 90-100 | 爆款预警 |
| 80-89 | 高热推荐 |
| 70-79 | 潜力热款 |
| 60-69 | 观察款 |

## 7. 存储结构

MVP 可先使用 SQLite 快速开发，表结构按 PostgreSQL 兼容设计，后续平滑迁移。

```sql
products (
  id,
  category,
  name,
  normalized_name,
  description,
  image_url,
  source_platform,
  source_url,
  purchase_url,
  card_image_url,
  price,
  currency,
  supplier_name,
  created_at,
  updated_at
);

social_signals (
  id,
  product_id,
  platform,
  keyword,
  hashtag,
  post_url,
  view_count,
  like_count,
  comment_count,
  share_count,
  publish_time,
  collected_at
);

sales_signals (
  id,
  product_id,
  platform,
  sales_7d,
  sales_growth_rate_7d,
  rank_current,
  rank_previous,
  rating,
  review_count,
  collected_at
);

trend_signals (
  id,
  trend_name,
  source,
  source_url,
  authority_score,
  keywords,
  category,
  publish_time,
  collected_at
);

recommendation_scores (
  id,
  product_id,
  category,
  social_score,
  sales_growth_score,
  fashion_trend_score,
  supply_score,
  novelty_score,
  hot_score,
  score_detail_json,
  calculated_at
);

recommendation_posts (
  id,
  product_id,
  target_type,
  group_id,
  title,
  private_content,
  public_content,
  card_image_url,
  hot_index,
  status,
  scheduled_at,
  sent_at,
  created_at
);

bot_groups (
  id,
  group_name,
  group_type,
  category_preference,
  push_time,
  enabled,
  created_at,
  updated_at
);
```

## 8. 机器人指令

管理员指令：

```text
/reco today              查看今日推荐池
/reco category 饰品       查看饰品推荐
/reco category 玩具       查看玩具推荐
/reco refresh            手动刷新推荐评分
/reco push private       向私域群推送今日推荐
/reco push public        生成公域发布文案
/reco card 商品ID         重新生成商品一图流卡片
/reco detail 商品ID       查看商品推荐依据
/reco config group       查看当前群推荐配置
/reco config category 饰品,玩具
/reco config time 10:00
/reco blacklist 商品ID
/reco feedback 商品ID 好/一般/差
/reco pause              暂停当前群自动推荐
/reco resume             恢复当前群自动推荐
```

普通用户指令：

```text
今日推荐
饰品推荐
玩具推荐
爆款榜
换一批
为什么推荐这个
```

## 9. 一图流卡片生成

最终微信消息建议采用两段式：

```text
[图片消息] 一图流推荐卡片
[文本消息] 产品链接：{purchase_url}
```

私域图片卡片内容：

```text
类目：饰品 / 玩具
产品主图
产品名称
火热指数与推荐等级
一句话卖点
推荐理由 2-3 点
来源：小红书 / TikTok / 电商平台 / 杂志趋势
风险提示短句
```

公域图片卡片内容：

```text
产品主图
产品名称
一句话卖点
适合场景
推荐标签
```

实现建议：

- MVP 可使用 Pillow 或 HTML 模板截图生成 PNG。
- 卡片比例建议优先做 3:4 或 4:5，适合微信和小红书二次使用。
- 图片宽度建议 1080px，文字区域留足边距。
- 产品主图必须先缓存或校验可访问。
- 生成后的图片地址写入 `card_image_url`。
- 如果图片生成失败，降级为“产品主图 + 文本链接 + 简短说明”。

## 10. 定时任务

MVP 建议流程：

| 时间 | 任务 |
| --- | --- |
| 02:00 | 导入 / 采集社媒热点数据 |
| 03:00 | 导入 / 采集电商销量增长数据 |
| 04:00 | 导入 / 采集趋势资讯关键词 |
| 05:00 | 商品归一化、去重、标签匹配 |
| 06:00 | 计算推荐评分 |
| 07:00 | 生成私域与公域文案 |
| 07:20 | 生成一图流推荐卡片 |
| 09:30 | 推送管理员预览 |
| 10:00 | 自动推送私域群，或等待管理员确认 |
| 10:10 | 生成公域发布素材 |

失败重试：

- 采集任务失败：重试 3 次，每次间隔 10 分钟。
- 评分任务失败：通知管理员。
- 推送任务失败：记录失败群，15 分钟后重试一次。
- 任意群发送超过阈值：自动暂停并通知管理员。

## 11. MVP 目录结构

```text
wechat-product-reco-bot/
  README.md
  CHANGELOG.md
  CONTRIBUTING.md
  THIRD_PARTY_NOTICES.md
  pyproject.toml
  requirements.txt
  .env.example
  .pre-commit-config.yaml
  config/
    config.yaml
    keywords.yaml
    source_weights.yaml
    sensitive_words.yaml
  plugins/
    product_recommender/
      __init__.py
      main.py
      commands.py
      scheduler.py
      message_templates.py
      services/
        collector_service.py
        scoring_service.py
        recommendation_service.py
        copywriting_service.py
        card_render_service.py
        push_service.py
        safety_service.py
      collectors/
        csv_collector.py
        tiktok_collector.py
        instagram_collector.py
        xiaohongshu_collector.py
        ecommerce_collector.py
        fashion_trend_collector.py
      models/
        product.py
        signal.py
        score.py
        recommendation.py
      repositories/
        product_repo.py
        signal_repo.py
        score_repo.py
        recommendation_repo.py
      utils/
        normalize.py
        deduplicate.py
        text_match.py
        logger.py
  data/
    imports/
    exports/
  migrations/
    001_init.sql
  tests/
    test_scoring.py
    test_deduplicate.py
    test_templates.py
    test_card_render.py
    test_safety.py
```

## 12. 代码和文档规范

代码规范：

- Python 代码统一使用类型注解。
- 数据结构优先用 Pydantic model 或 dataclass，不使用松散 dict 在模块之间传递核心对象。
- 业务逻辑、机器人适配、数据访问、卡片渲染分层，不把评分逻辑写进机器人指令处理函数。
- 每个模块保持单一职责，公共能力沉到 `services/` 或 `utils/`。
- 禁止在业务代码中硬编码群 ID、密钥、平台 token、路径和权重。
- 所有配置放入 `config/*.yaml` 或环境变量，并提供 `.env.example`。

测试规范：

- 新增评分、去重、模板、风控、卡片渲染逻辑时必须补单元测试。
- 涉及微信发送的逻辑必须有 mock 测试，避免真实群误发。
- 每次上线前跑完整测试和一次本地 dry-run。

文档规范：

- `README.md` 说明项目目标、快速启动、配置方式、核心指令。
- `CONTRIBUTING.md` 说明分支、提交、代码格式、测试要求。
- `CHANGELOG.md` 记录版本变化。
- `THIRD_PARTY_NOTICES.md` 记录所有第三方项目和许可证。
- `docs/architecture.md` 说明模块边界和数据流。
- `docs/data_schema.md` 说明 CSV 字段、数据库表、评分字段。
- `docs/ops_runbook.md` 说明日常运营、暂停推送、异常处理。

## 13. 开发里程碑

### 阶段 1：基础机器人与推荐框架，3-5 天

交付：

- 参考 AstrBot 插件机制搭建项目骨架。
- 微信群消息收发。
- 管理员指令。
- 配置文件。
- 本地数据库结构。
- 手动录入商品后可生成推荐内容。
- `README.md`、`.env.example`、`THIRD_PARTY_NOTICES.md` 初版。

### 阶段 2：评分系统 MVP，4-6 天

交付：

- 商品表、信号表、评分表。
- 火热指数评分公式。
- 饰品 / 玩具垂类标签。
- 去重逻辑。
- 推荐池生成。
- `/reco today`、`/reco detail` 指令。

### 阶段 3：数据源接入 MVP，7-10 天

优先级：

1. CSV / 表格导入。
2. 电商数据源。
3. 小红书 / TikTok 热点数据。
4. 时尚趋势关键词源。

交付：

- 电商商品采集。
- 社媒关键词热度采集。
- 趋势关键词采集。
- 采集失败重试。
- 数据源权重配置。

### 阶段 4：文案与推送，4-6 天

交付：

- 私域详细推荐模板。
- 公域种草文案模板。
- 一图流卡片模板与图片生成。
- 定时推送任务。
- 管理员预览。
- 手动推送。
- 群配置和限流。

### 阶段 5：灰度测试与调参，7 天

交付：

- 连续 7 天推荐日志。
- 人工反馈入口。
- 商品屏蔽机制。
- 评分权重调整。
- 热门商品重复控制。
- 异常推送告警。

## 14. 技术风险

| 风险 | 应对 |
| --- | --- |
| TikTok、Instagram、小红书反爬严格 | MVP 先用人工导入或第三方数据服务，数据源插件化 |
| 社媒热词难映射商品 | 建立 normalized_name、标签、人工确认推荐池 |
| 高互动不等于高转化 | 引入 SupplyScore 和人工反馈 |
| 微信风控 | 控制频率、管理员预览、白名单、暂停机制 |
| 采购链接失效 | 推送前校验链接，记录最后可用时间 |
| 公域文案合规 | 敏感词、绝对化词、夸大承诺拦截 |
| AstrBot 适配变化 | 业务逻辑与机器人框架解耦 |
| 图片卡片生成失败 | 降级发送产品主图、链接和短文本 |
| 开源许可证不兼容 | 只参考架构，直接复用前做许可证审查 |
| 模块拼接失控 | 统一接口模型、统一配置、统一日志和测试入口 |
