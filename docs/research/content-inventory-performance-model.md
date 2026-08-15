# Content Inventory 与发布后表现模型

- 日期：2026-08-12
- Wayfinder 节点：定义 Content Inventory 与发布后表现模型
- 当前优先级：Heyup-first；REDMAGIC 只作为后续 DTC 对照切片和兼容约束
- 结论性质：领域与数据契约研究，不是最终 Drizzle schema，也不表示 Heyup/REDMAGIC 的 Shopify、GSC 或 GA4 property 已接通

## 摘要

Content Inventory 不能只是一个 URL 列表，也不能由 GSC 或 GA4 反向代替。建议把它设计为站内内容的**身份与版本主档**，负责回答“站内有什么、哪个 URL 属于同一页面、现在展示的是哪个内容版本、是否可由本项目管理”；Publication Record 负责记录“某个内容版本何时、以什么外部 CMS 身份交付或被确认发布”；GSC 与 GA4 Performance Snapshot 分别记录“Google Search 如何展示该页面”与“访问者落地后发生了什么”。四者通过稳定 `content_asset_id`、URL alias/canonical 关系和明确的时间窗口连接，而不是直接按当前 URL 字符串强行 join。

```text
Content Asset（稳定内容身份）
  ├─ Content Revision（不可变内容版本）
  ├─ URL Alias / Canonical Decision（URL 与页面身份）
  ├─ Publication Record（CMS 外部事实回传，不是 CMS 写入）
  ├─ GSC Performance Snapshot（query × Google canonical page）
  └─ GA4 Performance Snapshot（landing page × session/behavior/outcome）
                ↓
       Source Observation → Atomic Signal
                ↓
       Signal Cluster → SEO Opportunity
                ↓
  create / update / expand / merge / redirect / link / monitor / retire
```

本期应优先验证 Heyup。Heyup 不是单一 Buying Guide 站，而是包含 Tech News、Hunts、Product Reviews、Buyer’s Guide、Brand Buzz、Trend & Insight Lab、Feature Stories、Creator Program 等频道的媒体型 Newsroom（`codex_knowledge_base/07_content_and_newsroom_architecture.md:22-62`）。在内容人力有限、目标偏向高度自动化/agentic 的背景下，Inventory 的首要价值是让 Agent 在生成内容前先理解已有频道和页面、避免重复、选择新建/更新/内链/观察动作，并在 CMS 外部发布后持续读取表现。REDMAGIC 的新品、活动、月度排期和发布后一个月复盘是后续 DTC 模式的兼容要求，但不应被固化为共同底座默认节奏。

## 研究范围与证据口径

本报告使用三类证据：

1. **项目内一手资产**：当前上下文、领域语言、ADR、Heyup 知识库、旧 Python 工作流、迁移运行资产和此前已确认的 Signal 模型。
2. **本地参考实现**：`/Users/russell/Desktop/04_product/DTC+/day/day-demo/` 中的 GSC、GA4、Drizzle connection/cache 与同步代码；只读参考，不复制凭据或业务数据。
3. **官方资料**：Google Search Console Search Analytics 与 URL Inspection API、GA4 Data API 与数据处理说明、Shopify Admin GraphQL Article 语义、Google canonical/redirect 文档。

外部平台规则、字段和延迟会变化，实施时应重新检查官方文档。本报告没有调用 Heyup 或 REDMAGIC 的真实 CMS、GSC、GA4，也没有读取任何真实 property 数据；所有 property、时区、事件和页面映射仍需真实只读验证。

## 本地事实与迁移约束

### Heyup 的内容面远大于旧自动化范围

Heyup 知识库把内容定义为产品理解、趋势叙事、活动放大、评测可信度、购买指导和品牌曝光的共同载体（`codex_knowledge_base/07_content_and_newsroom_architecture.md:12-20`），并记录了多种内容频道和作者层（同文件 `:22-71`）。平台本身还包含产品、Tryout、社区、品牌与商业层；内容是解释和发现机制，而不是孤立博客（`codex_knowledge_base/04_platform_information_architecture.md:33-61`）。

因此第一版 Inventory 应能表达：

- Newsroom 频道和内容类型，而非只识别 Buying Guide；
- 产品、品牌、Tryout、主题或事件等内容实体关联；
- 市场、语言和本地化版本；
- 可自动管理、需人工审批、仅可观测三种治理边界；
- 已有内容是否能承接一个 Signal Cluster，而不是看到机会后默认新写文章。

### 旧 Heyup 工作流没有真实 Content Inventory

旧 `GeneratedArticle` 保存 title、slug、excerpt、SEO 字段、正文结构、source manifest 和 risk flags（`heyup_buying_guides/schemas.py:108-129`），但没有稳定 Content Asset、内容 revision、canonical、旧 URL、目标 query/topic、内链或发布后表现。

它用 `topic_key` 查找近期 `article_runs` 来追加 `duplicate_topic_risk`（`heyup_buying_guides/orchestrator.py:97-102`），而 SQLite 把大部分状态压在 JSON blob 中；`article_runs` 和 `publication_attempts` 也没有页面身份、URL 历史或表现关联（`heyup_buying_guides/storage.py:23-64,111-155`）。这只能检测“同 topic_key 是否曾跑过”，不能判断站内真实覆盖、URL 合并、关键词蚕食或已发布页面更新。

旧 Shopify 路径在通过校验后调用 publisher（`heyup_buying_guides/orchestrator.py:116-124`），REST/GraphQL 都创建未公开草稿（`heyup_buying_guides/shopify.py:30-74,118-180`）。但项目现有边界明确不执行 Shopify 发布；旧代码只能帮助理解 Shopify-ready 字段和外部 ID，不能作为新系统默认发布路径。

### Day demo 证明连接和查询形态存在，但缓存粒度不足

本地 Day demo 的 GSC 客户端已经表达 `date/query/page/country/device/searchAppearance`、filter、aggregation、`rowLimit/startRow`，并把 API row 的 key 映射到具名字段（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/marketing/clients/google-search-console-client.ts:16-59,127-187`）。它也能按 page 精确过滤 query（同文件 `:318-347`）。

但是定时同步只拉 `date` 维度的站点日汇总（同文件 `:369-421`）。虽然 Drizzle 的 `mkt_search_console_cache` 预留了 query/page/country/device 字段（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/db/schema.ts:984-1023`），当前定时路径不能支撑 page×query 的覆盖和蚕食判断。

GA4 客户端支持任意 dimensions/metrics 的 `runReport`，也有 pagePath/pageTitle 页面查询（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/marketing/clients/google-analytics-client.ts:233-276,364-520`）。但代码明确只缓存带 date 的日序列，页面和来源拆分按需返回而不写 cache（同文件 `:116-142`）；`mkt_analytics_cache` 的固定 metric-type 行也不是 Content Asset 级表现模型（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/db/schema.ts:897-944`）。

可复用的是：品牌到外部 property 的 connection、只读 OAuth、通用报告、分页和同步运行思想。不能直接复用的是现有日汇总 cache schema 和“页面数据只按需看、不持久化”的行为。

## 外部平台的一手事实

### Shopify Article 不是我们的 Content Asset 身份

Shopify Admin GraphQL 的 Article 有全局 ID、blog、handle、title、body、tags、`isPublished`、`publishedAt` 和 `updatedAt`；Article ID 是 CMS 身份，handle 用于 URL，`publishedAt` 为 null 时文章不可见。[Shopify Article](https://shopify.dev/docs/api/admin-graphql/latest/objects/article)

Shopify 还允许修改 handle，并通过 `redirectNewHandle=true` 自动创建旧 handle 到新 handle 的跳转。[ArticleUpdateInput](https://shopify.dev/docs/api/admin-graphql/latest/input-objects/articleupdateinput) 这说明 CMS ID、当前 URL 和 URL 历史是三个不同概念：Article ID 可以不变而 handle 改变，旧 URL 可能仍通过 redirect 存在。

因此 `shopify_article_id` 只能是 Publication Record 的外部引用，不能充当跨 CMS、跨迁移的 Content Asset 主键。反过来，项目也不能因为收到 CMS ID 就声称内容已经公开；还需要状态、公开 URL 与外部确认时间。

### GSC page 是 Google 归因的 canonical URL

Search Analytics API 可按 date、query、page、country、device 等维度聚合，但官方明确 API 只保证 top rows，不保证返回所有数据；结果通常按 click 排序，单页 `rowLimit` 最大 25,000，并支持 `startRow` 分页。[Search Analytics query](https://developers.google.com/webmaster-tools/v1/searchanalytics/query) 官方还说明每天每 search type 最多暴露 50K 行，想超过 Search Console 大约 16 个月的历史需自行定期拉取并保存。[Getting all your performance data](https://developers.google.com/webmaster-tools/v1/how-tos/all-your-data) [Debugging Search traffic drops](https://developers.google.com/search/docs/monitor-debug/debugging-search-traffic-drops)

Performance report 的 page 数据大多归到 Google 选择的 canonical URL；即使用户点击了 duplicate URL，数据也可能计给 canonical。[Performance dimensions and groupings](https://support.google.com/webmasters/answer/17011259) Search Analytics 在 page 分组/过滤时使用 page aggregation，因此 page 行不能直接视为用户最终访问 URL。

GSC 还有三项重要限制：

- 隐私保护会省略匿名 query，chart/property totals 可高于 query 行之和；
- daily date 以 Pacific Time 解释，通常与 GA4 property timezone 不同；
- finalized 数据有延迟，fresh/all 数据可能继续变化；报告通常需 2–3 天才稳定。[About Search Console data](https://support.google.com/webmasters/answer/96568) [Search Analytics query](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)

URL Inspection API 可只读返回 `coverageState`、`lastCrawlTime`、`googleCanonical` 和 `userCanonical`，但当前 API 检查的是 Google 索引中的版本，不是实时页面测试。[URL Inspection inspect](https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect) [UrlInspectionResult](https://developers.google.com/webmaster-tools/v1/urlInspection.index/UrlInspectionResult) 它适合对高价值页面、canonical 冲突和合并候选做按需核验，不应作为每天全站抓取的唯一 Inventory 来源。

### GA4 landing page 是 session 入口，不是 canonical

GA4 Data API `runReport` 用 property ID、date ranges、dimensions、metrics、filters 和分页返回聚合表；响应 `rowCount` 与本次 limit 无关，可据此继续分页。[Create a report](https://developers.google.com/analytics/devguides/reporting/data/v1/basics)

官方 schema 中：

- `landingPage` 是一次 session 首个 pageview 对应的 page path；
- `pagePath` 是 hostname 与 query string 之间的路径；
- `pageLocation` 是包含 protocol、hostname、path 和 query string 的完整 URL；
- `sessions`、`engagedSessions`、`engagementRate`、`keyEvents`、`sessionKeyEventRate`、`totalRevenue` 等指标可用于流量、参与和业务结果，但字段是否可用及含义需按具体 property metadata 核验。[GA4 dimensions and metrics](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema)

GA4 不是 CMS 页面的权威身份源。它可能出现 query string、locale path、trailing slash、hostname、历史路径和 `(not set)` 差异。它还可能受 thresholding、`(other)` 高基数行、报告身份、近 24–48 小时处理和 key event 定义变化影响；应保存 response metadata 和请求契约，不能把缺行直接解释为 0。[Reporting data expectations](https://developers.google.com/analytics/devguides/reporting/data/v1/reporting-data-expectations) [GA4 data freshness](https://support.google.com/analytics/answer/11198161)

GSC clicks 和 GA4 organic sessions 也不应该相等：两者计算对象、隐私过滤、机器人处理、JavaScript/Consent 覆盖和时区均不同。它们应作为互补证据，而不是彼此对账到完全一致。

## 推荐领域模型

本节定义逻辑对象及职责，暂不锁定 Drizzle 表名、列类型和索引。

### 1. Content Asset：稳定内容身份

一条 Content Asset 表示“同一个可被经营的内容页面”，不随着 title、正文、handle 或 canonical 变化而更换身份。最低语义：

| 字段组 | 建议语义 |
| --- | --- |
| 身份 | `content_asset_id`、project、operating mode |
| 分类 | surface/channel、content type、editorial/commercial purpose |
| 边界 | market、language、locale、ownership mode |
| 主题 | primary topic、target query intent、brand/product/event entities |
| 生命周期 | planned/draft/handed_off/published/unpublished/redirected/retired/unknown |
| 治理 | automation eligibility、required review tier、owner、source of truth |

`ownership_mode` 建议固定为：

- `managed`：可由本系统生成修订、建议更新并进入 CMS handoff；仍遵守人工/LLM gate；
- `approval_required`：可生成建议和内容包，但必须由明确 owner 审批；
- `observed_only`：只进入盘点、覆盖与表现分析，不能自动建议覆盖原文或发起 handoff；
- `unknown`：来源/归属未确认，只允许观测，默认 fail closed。

Heyup-first 并不表示所有旧文章都能自动改写。高度 agentic 的闭环必须建立在 Content Asset 的治理边界上；“自动发现与准备变更”可以高自动化，“是否允许更新/交付”由资产策略决定。

### 2. URL Alias 与 Canonical Decision：不要把 URL 当主键

每个 observed URL 独立记录：

- 原始 URL 与规范化 URL；
- host、path、locale、query-string policy、首次/最后观测时间；
- 来源：CMS、sitemap/crawl、GSC、GA4、人工导入；
- HTTP status、redirect target（可得时）；
- page-declared canonical（可得时）；
- Google-selected canonical（按需 URL Inspection）；
- 归属的 `content_asset_id`、关系类型和判断依据/置信度。

关系至少区分：

- `current_public_url`；
- `historical_url`；
- `redirect_source`；
- `declared_canonical_alias`；
- `google_canonical_alias`；
- `analytics_variant`；
- `unresolved`。

规范化只处理明确无语义的差异，例如受控 host/scheme、已确认的 trailing slash 策略和可丢弃 tracking parameters。**不能**仅凭去掉语言目录、查询参数或标题相似就合并页面；多语言版本、筛选页和活动页可能是独立资产。

Google 把 redirect 与 `rel=canonical` 都视为 canonical 信号，其中 redirect 是强信号，但 Google 仍会综合其他信号选择 canonical。[Canonical methods](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls) 因此本系统需同时保存“站点声明”“跳转事实”“Google 选择”，不能把三者覆盖成一个字段。

### 3. Content Revision：内容变化的不可变快照

Content Revision 是某个 Content Asset 在一个时间点的内容与 SEO 字段版本。建议保存：

- revision ID、asset ID、来源、created/observed time；
- title、SEO title、meta description、handle、excerpt、tags；
- 结构化 heading/section 摘要、正文 fingerprint、字数和语言；
- 目标 query/topic、实体、内链/出链快照；
- source manifest / evidence revision（本系统生成时）；
- revision cause：new、editorial update、SEO update、localization、merge、policy、unknown；
- CMS `updatedAt` 和抓取时间，但两者都不能单独作为 revision ID。

内容 hash 相同的重复读取不生成新 revision；hash 或治理字段变化时生成新 revision，不覆盖旧版本。对于只读 CMS，可保存允许字段与 hash，不必复制完整 HTML；是否保留正文由权限、版权和运行需要决定。

仅靠 Shopify `updatedAt` 无法知道是正文、标签、模板还是系统触碰，也无法证明页面实际线上内容已改变。内容前后效果归因必须指向明确 revision 或至少“未分类的外部变更事件”，不能把所有 `updatedAt` 都标成 SEO 更新。

### 4. CMS Handoff 与 Publication Record：交付和发布是两个事件

建议拆开：

- **CMS Handoff**：本项目将某一 Content Revision 的结构化包交给运营/CMS owner；记录目标系统、包版本、交付时间和审核状态，不表示已写入 CMS。
- **Publication Record**：由外部 CMS/运营回传或只读同步得到的事实；记录 external CMS type/ID、blog/channel、public URL、published state、published/unpublished time、external revision/update time、对应 content revision 和确认来源。

Publication Record 不等于本项目执行发布。一个 handoff 可以没有 publication；一个外部人工发布也可以没有本项目 handoff。只有二者都存在时才可计算“从推荐/交付到上线”的流程效率。

对于 Shopify，Article ID、blog ID、handle、isPublished、publishedAt、updatedAt 是合适的外部字段；本项目不保存 access token，不调用 mutation，不把草稿创建成功写成 `published`。

### 5. GSC Performance Snapshot：搜索可见性证据

MVP 建议至少持久化两种报告，避免一次高维请求承担所有目标：

1. `date × page × query × country × device × search_type` 的 page-query 明细，按短窗口和 25K 页码分页；
2. `date × page` 与 property totals 的对账快照，保留匿名 query/top-row 限制造成的覆盖差。

每个 snapshot 必须保存：property/site URL、request dimensions/filter/aggregation/dataState、日期窗口与 PT 时区、clicks、impressions、CTR、average position、retrieved_at、final/incomplete 状态、row count、pagination completion、request/contract version。CTR 与 position 是官方聚合指标，跨行合并必须按原始分子/权重重新计算，不能简单平均。

GSC row 先连接 `URL Alias`，再连接 Content Asset。无法解析的 page 进入 `unresolved` 队列，而不是被删除或自动创造资产。

### 6. GA4 Performance Snapshot：落地、参与和结果证据

MVP 至少分三类报告：

1. **Landing-page acquisition**：`date × landingPage × sessionPrimaryChannelGroup`（或 property 验证后的等价 organic 口径），指标 sessions、active users、engaged sessions、engagement rate；
2. **Content engagement**：按 pagePath/pageLocation 读取 screenPageViews、user engagement、scroll/相关事件（仅在真实埋点可用时）；
3. **Outcome**：按 landing page 读取已确认的 key events、session key-event rate；DTC 可选 transaction/revenue，Heyup 则应按其真实业务事件定义，不假定 purchase 是唯一成功。

每个 snapshot 保存 property、property timezone/currency、request dimensions/metrics/filter/date ranges、channel definition、event/key-event definition version、retrieved_at、response metadata、`subjectToThresholding`/`dataLossFromOtherRow`、pagination completion 和 contract version。

GA4 row 以 `hostName + landingPage/pagePath` 生成 observed URL，再通过 URL Alias 连接 Content Asset。query string 的保留/剥离必须来自项目 URL policy；不要把 `landingPage` 当 canonical。

## 时间、版本与比较窗口

### 平台时间不能裸 join

- GSC 日数据使用 Pacific Time；
- GA4 date/相对日期使用 property reporting timezone；
- CMS timestamps 通常为带 offset 的 ISO 8601；
- Operational DB 建议统一存 UTC timestamp，同时保留 source-local date 和 timezone。

日粒度比较应在各自来源内先计算，再按分析窗口解释；不要把 GSC 的 `2026-08-01` 和 GA4 的 `2026-08-01` 假设成完全相同的 24 小时。跨源 join 以 Content Asset + 逻辑 period 为主，报告中明确 source timezone。

### 刷新建议

延续已确认的采集契约：GSC 主分析使用 finalized D-3，并回补最近 7 天；GA4 主分析使用 D-2，并回补最近 12 天，以吸收处理和 attribution 变化。Content Inventory 从只读 CMS/站点每日或每次分析前增量同步；publication 回传可事件触发加每日 reconciliation。

Heyup 自动化不等于必须实时重写内容。建议把数据采集与动作频率分开：

- 每日：Inventory 差异、GSC/GA4 snapshot、URL 解析和明显异常；
- 每周：形成衰退、蚕食、覆盖与更新候选；
- 每月：内容组合、频道平衡和自动化 backlog 回顾；
- 事件触发：新品、趋势爆发、外部发布回传、handle/redirect 变化。

REDMAGIC 后续可在相同底座上配置月度内容 calendar、产品/活动优先级和上线约一个月后的复盘窗口；这属于 DTC Profile/Operating Mode 参数，不是 Heyup 默认节奏。

### 变更前后基线

不能只比较“最近 28 天 vs 前 28 天”就归因给内容 revision。推荐每个显著 Publication/Revision Event 建立版本化评估：

- `pre_window`：变更前最后 28 个完整日；
- `washout/indexing_window`：上线后 7–14 天，只观察不下结论；
- `post_window`：随后 28 个完整日；
- 若已有 12 个月数据，再加去年同期 28 日作为季节性参照；
- 新页面没有自身 pre-window，应使用上线后成熟曲线、同类型/频道基线和 Opportunity 预期，不制造“增长率”。

28/7–14/28 是 MVP 建议，不是固定统计真理。新闻内容寿命短，Buying Guide/evergreen 内容更长；最终由 Content Type policy 配置。所有比较都排除未 finalized tail，并记录期间发生的其他 revision、redirect、活动、跟踪变更和已知数据异常。

## 四类判断如何形成证据

这些判断应先形成 Performance/Inventory Source Observation 和 Atomic Signal，再进入 Cluster/Opportunity；不能让一个 SQL flag 直接变成更新任务。

### 覆盖缺口（Coverage Gap）

候选条件：一个合格 Signal Cluster / query-intent cluster 在目标市场与语言有需求证据，但 Inventory 中没有可索引、可管理且意图匹配的 Content Asset。

至少需要：

- 外部需求/趋势/社区或 GSC query 证据；
- Inventory 的 topic/entity/intent 检索结果；
- GSC page-query 检查没有强匹配承接页，或只有明显不匹配页面；
- unresolved URL 和 observed-only 资产已排查。

“GSC 没返回 query”不能单独证明缺口，因为 top-row 与匿名 query 限制会造成缺失。Coverage Gap 只说明值得评估新建/扩展，不自动决定写新文章。

### 关键词蚕食（Cannibalization）

候选条件：同一规范化 query-intent cluster 在同一市场/语言和重叠时间窗内，持续由两个或更多可索引 Content Asset 获得显著 impressions/clicks，且页面意图高度重叠或排名/点击在页面之间反复切换。

必要保护：

- 先解析 GSC canonical、redirect 和 URL alias，避免把同一资产的 URL 变体当两篇文章；
- 至少观察 28 个完整日，并要求多个周级窗口重复出现；
- 记录各页的 impressions share、clicks、position trend 和 query family，而不是只看“两个 URL 出现过”；
- 允许合理多页面占位：品牌页、产品页、新闻与指南可能对应不同 intent，不应仅因 query 相同自动合并。

检测结果是 Signal Cluster，后续动作可能是重新定位、内链、合并+redirect、更新或接受共存。

### 内容衰退（Content Decay）

候选条件：已成熟的 Content Asset 在同口径 query/page 上出现持续下降，且超出日波动与季节性，并有 Inventory/内容时效证据支持。

建议证据组合：

- GSC 28 日完整窗口对前一窗口和去年同期：clicks、impressions、CTR、position trend；
- GA4 organic landing sessions 与 engagement/outcome 同期变化；
- 最新 content revision 年龄、产品/年份/价格或事件时效；
- SERP/竞争页面变化、站点 redirect/canonical/追踪变化和 Google 已知 anomaly 作为背景/反向证据。

只出现 GA4 sessions 下跌、GSC impressions 不变，可能是 tracking/consent/channel 问题；只出现 impressions 下跌而 position 稳定，可能是需求季节性；position 单独波动也不足以下结论。衰退判断必须保留支持、反向和背景证据。

### 更新机会（Refresh / Expansion Opportunity）

候选条件不只包括衰退，还包括：

- impressions 高、CTR 相对自身历史恶化，可能需要 title/meta/intent 对齐；
- position 处于可推进区间且 query family 与现有页面匹配，适合扩写而非新建；
- 内容过时但仍有流量/内链价值；
- 新 Signal Cluster 可被已有资产自然承接；
- 内链孤岛或同频道内容可通过 hub/link 获益；
- 发布后一个月/内容类型成熟窗口到达，需要复盘是否扩展、观察或调整。

动作建议必须指向明确 Content Asset 和 current revision，说明 proposed scope、证据、预期 query/intent、canonical/redirect 风险和审核级别。

## Heyup-first 的最小闭环

Heyup 的第一版不应先建设一个面向 DTC 人工排期的后台，而应验证 Agent 是否能在有限人工治理下完成下列循环：

1. 从 Shopify 只读 Article、sitemap/crawl 和必要人工导入建立 Newsroom Content Inventory；
2. 识别频道、类型、市场/语言、主题实体、current URL/canonical 与治理边界；
3. 每日采集 GSC page-query 与 GA4 landing-page snapshots；
4. 将 Inventory/Performance 变化转为 Source Observation 和 Atomic Signal；
5. 与 News、Reddit、Trends、关键词/SERP 等 Signal 聚类；
6. 先判断站内承接：create、update、expand、merge/redirect、link/reposition、monitor、retire；
7. 对可管理资产自动形成 Brief、内容 revision、SEO 字段和 CMS handoff package；
8. 通过 LLM 初审和少量人工治理后，由外部流程发布；
9. 只读回传 Publication Record，并建立版本前后表现；
10. 结果回流为新的 Signal，而不是直接让表现差自动覆盖线上内容。

Heyup 第一轮 Inventory 至少应覆盖知识库已记录的多个 Newsroom 频道，而不是只导入旧自动化生成过的文章。旧运行资产可帮助关联部分 `topic_key`、slug 与生成内容，但不能当作线上 CMS/URL 事实来源。

## REDMAGIC 对照切片的兼容约束

近期内容运营输入表明，REDMAGIC 更接近“新品/活动优先、月度 calendar、周更、专属文案与群审、人工 Shopify 发布、上线约一个月后复盘”的 DTC 模式；SEO 是输入之一，并非当前唯一或首要运营痛点。该信息在本报告只抽象为约束，不保存访谈原文或任何截图。

共同底座需要允许 REDMAGIC Profile 配置：

- 产品 launch、campaign 与 calendar slot 对 Content Asset/Opportunity 的优先级；
- `managed / approval_required / observed_only`，避免假设旧博客都可自动更新；
- 发布后约 30 日 review checkpoint；
- 社媒/VOC 用于主题角度和用户教育，但不把负面评论原文直接写入品牌文章；
- 多站点/多 locale 资产的独立身份、本地化 revision 和 publication record；
- 外部人工发布回传，不要求本系统写 Shopify。

这些是 DTC 模式配置，不应降低 Heyup 的自动化程度，也不应让共同模型围绕“每月人工调一次关键词”设计。

## Supabase + Drizzle 的持久化边界

当前默认方向仍是 Supabase/PostgreSQL + Drizzle。建议关系能力至少能表达：

- project/site/CMS/GSC/GA4 connection 的非密钥配置；
- content asset、content revision、content-entity/topic/target-query 关联；
- URL alias、redirect/canonical decision 与 unresolved queue；
- CMS handoff 与 publication record；
- GSC request/run/snapshot 及 page-query metrics；
- GA4 request/run/snapshot 及 landing/page metrics；
- revision evaluation window、comparison result 和质量 flags；
- 从 performance/inventory observation 到 Signal/Evidence Reference 的血缘。

不建议把全部模型压成 `content_assets.payload_json`，也不建议为每种 metric 建一个宽表列。高基数 page-query/landing-page snapshot 应有可分页、可 upsert、可保留 request grain 的事实记录；低频 metadata 可用 JSONB 承载 provider-specific 字段，但核心 identity、date、URL、query、metric 和 lineage 应为可索引字段。

Drizzle 只管理 SEO Operational DB 的 schema/migration；不管理 Shopify、GSC、GA4 或 BigQuery。API raw response 的保存范围按现有 raw-first 契约与平台政策决定，但不能将 token、cookie、客户数据或未脱敏内容写入 Git。

## 来源 ready 与真实验证清单

### Content Inventory ready

1. 获得 Heyup CMS/Shopify 只读访问，确认 Article、Blog、handle、publishedAt、updatedAt 和分页；
2. 从 sitemap/站点读取当前公开 URL，与 CMS 记录对账；
3. 抽样确认频道、内容类型、market/language 和 ownership policy；
4. 验证 URL normalize、locale、query-string、canonical 和 redirect 规则；
5. 重跑不重复创建 Asset/Revision，handle 改动能保留旧 URL；
6. 无法匹配的页面进入 unresolved，不能静默丢弃；
7. 标明 Inventory 的覆盖率和最后同步时间。

### GSC ready

1. 只读 property 与 Heyup project 绑定已确认；
2. 近 180 天 page、query、page×query 的分页 smoke 成功；
3. 保存 request grain、PT timezone、data state 与 incomplete metadata；
4. page 行能映射到 Inventory，无法解析项可审计；
5. property/page totals 与 query rows 的覆盖差被记录；
6. D-3 + 7 日回补连续运行两个周期；
7. 不把缺行解释为 0。

### GA4 ready

1. 只读 property、property timezone/currency 和 web stream/hostname 已确认；
2. 通过 Metadata API/真实报告验证 landingPage、channel、engagement、key-event 字段兼容；
3. organic channel 与 Heyup 业务 key events 由 owner 确认并版本化；
4. pagination、thresholding、`(other)` 和 response metadata 被保存；
5. URL policy 能把 landing path 安全映射到 Inventory；
6. D-2 + 12 日回补连续运行两个周期；
7. 近 48 小时变化和 key-event 定义变化不会被误判成内容变化。

### Publication Record ready

1. 外部 CMS ID、public URL、state、publishedAt/updatedAt 可只读回传或由运营确认；
2. handoff、draft、scheduled、published、unpublished 明确区分；
3. 一个 external article 可以关联多个 revision event，但只有当前 revision 标记 active；
4. handle/redirect 变化保留 URL 历史；
5. 系统没有 CMS mutation/write permission，也没有把交付当成发布。

## 已确认、建议与待验证

### 已确认的项目约束

- 使用 `Source Observation → Atomic Signal → Signal Cluster → SEO Opportunity`；Content Asset 和 Performance Snapshot 有独立领域身份。
- Publication Record 是 CMS 外部事实连接，不表示本项目执行发布。
- BigQuery 继续只读；本模型不修改 BQ schema/storage。
- Supabase/PostgreSQL + Drizzle 是当前默认后端方向。
- 当前优先验证 Heyup 媒体/Newsroom 的高自动化闭环；REDMAGIC 暂为 DTC 对照和兼容约束。

### 本报告建议、尚待用户确认

- 稳定 Content Asset 与可变 URL、Content Revision、Publication Record 分离；
- URL alias/canonical/redirect 作为显式关系，不按 URL 字符串直接 join；
- GSC page-query 与 GA4 landing-page snapshot 分源保存，通过 Asset 连接；
- Heyup 资产分 managed / approval_required / observed_only / unknown；
- 默认以 28 日基线、7–14 日 washout、28 日 post window 作为 evergreen MVP 评估模板，按内容类型覆盖；
- performance 只生成 Observation/Signal，不直接触发线上修改。

### 待真实只读验证

- Heyup Shopify Blog/Article 的真实数量、频道映射、语言/市场、URL、发布状态和可读取字段；
- Heyup GSC property、API 权限、行量、canonical 分布、时区延迟和 180 天覆盖；
- Heyup GA4 property、hostname、timezone、organic 口径、事件/key-event、thresholding 和 landing path 质量；
- CMS 与 public sitemap 的差异、redirect/canonical 策略；
- 哪些旧内容可自动管理、哪些必须审批或只能观测；
- REDMAGIC 后续切片的多站点、内容治理和 30 日复盘口径。

## 集中确认决策包

建议一轮确认以下八项：

1. **Heyup-first**：本期先以 Heyup 多频道 Newsroom、高度自动化内容生产、有限人工治理和表现闭环验证模型；REDMAGIC 只保留后续 DTC 对照约束。
2. **分离四个身份**：Content Asset 是稳定页面身份；Content Revision 是不可变内容版本；CMS Handoff 是交付；Publication Record 是外部发布事实，四者不得合并成一张“文章表”。
3. **URL 不是主键**：GSC canonical page、GA4 landing/page URL、Shopify handle/public URL 先进入 URL Alias/Canonical 关系，再连接 Content Asset；redirect 和多语言 URL 保留历史。
4. **资产治理分级**：Heyup Inventory 使用 `managed / approval_required / observed_only / unknown`；unknown 默认只观测，Agent 不得自动覆盖线上内容。
5. **GSC 与 GA4 分工**：GSC 保存 page×query 搜索可见性；GA4 保存 landing-page acquisition、engagement 和已验证 outcome；两者不强求数值相等，也不把缺行当成 0。
6. **版本化表现评估**：重要 revision/publication 建立前后窗口；evergreen 默认 28 日 pre + 7–14 日 washout + 28 日 post，新闻/活动等由内容类型改写；数据尾部排除未 finalized 日期。
7. **诊断不是动作**：覆盖缺口、蚕食、衰退、更新候选先成为可追溯 Signal/Cluster，再由 Opportunity 决定 create/update/expand/merge/redirect/link/monitor/retire；任何单一阈值不直接修改或交付内容。
8. **Supabase + Drizzle 持久化**：Operational DB 保存 Asset、Revision、URL 关系、Handoff、Publication、GSC/GA4 snapshot 与 Signal 血缘；BigQuery、Shopify、GSC、GA4 均保持外部只读来源，最终表名/索引留到规格阶段。

## 本报告不包含

- 最终 Drizzle schema、migration 或实现代码；
- Heyup/REDMAGIC 真实 URL、property ID、事件、流量、凭据或业务数据；
- Shopify 写入、发布、redirect mutation 或站点运维；
- Opportunity 准入/多维评分标准；
- 内容生成 Prompt、质量模板或最终 CMS 字段规格；
- 用户访谈原文、会议纪要或截图。
