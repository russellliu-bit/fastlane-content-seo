# SEO MVP 信号源与渐进采集契约

- 日期：2026-08-12
- Wayfinder 节点：确定 SEO MVP 信号源与渐进采集契约
- 结论性质：本地一手代码与官方接口文档研究；不是实现规格，也不表示生产凭据已就绪

## 摘要

双验证切片不需要等待完整 Marketing Listening，但也不能在关键数据源尚未接通时开始 Opportunity 验证。建议把 SEO MVP 的最低数据面固定为**七个采集来源族加内容资产清单**：GSC、GA4、关键词指标、SERP、Google Trends、News、Reddit，以及 Content Inventory；其中内容资产属于另一个 Wayfinder 节点，本报告定义其连接边界但不展开模型。REDMAGIC 还需要独立接入 BQ 第一方 VOC View，该契约由 VOC 专项节点定义。

推荐的 MVP 来源组合是：

| 来源族 | MVP 首选 | 备用或未来替换 | 建议刷新 |
| --- | --- | --- | --- |
| GSC | Search Console Search Analytics API | 中台/BQ 标准表 | 每日，主窗口截至 D-3 |
| GA4 | GA4 Data API `runReport` | GA4 BigQuery Export / 中台标准表 | 每日，主窗口截至 D-2，并回补近 12 天 |
| 关键词指标 | DataForSEO（通过小样本 spike 后） | Ahrefs；Google Ads 用于口径校准 | 月度指标刷新；新 seed 按需查 |
| SERP | DataForSEO Live（通过小样本 spike 后） | Serper `/search` 连续性 fallback | 核心词每日，其余每周；事件触发可加跑 |
| Google Trends | Apify `apify/google-trends-scraper` | Google Trends 官方 Alpha（获得准入后） | 每日；保留原请求范围与相对标度 |
| News | Serper `/news` + Google News RSS 日期校正；独立 RSS feed 后续补充 | Day/Marketing Listening DWD | 4 小时；低频品牌可每日 |
| Reddit | 官方 OAuth Data API | 经合规确认的授权供应商；不要把无 OAuth 公共 JSON 当正式 fallback | 6 小时；低频词每日 |

这套组合是“薄而完整”的：GSC/GA4回答站内真实表现，关键词指标和 SERP 回答需求与竞争形态，Trends 回答变化速度，News/Reddit 回答事件与用户讨论。商业 SEO provider 只负责供应商估算信号，不能替代 GSC、GA4 和 Google Ads 等第一方或平台事实。它不包含 YouTube、X、TikTok、Hacker News 等完整 Listening 扩源；这些来源以后通过同一标准 Observation/Run 契约渐进接入，不改变下游 Signal 和 Opportunity。

`day` 资产可以学习，但不能整套复制。`day-demo` 已实现 provider adapter、fallback、市场本地化、News/Reddit/GSC/GA4 等代码模式；`day-pipeline` 只有管道规划，没有实现代码。应继承两者的接口思想、raw-first 数据布局和运行日志设计，按本项目栈重写适配器。尤其不能继承 demo 的“LLM 分析失败即丢弃原始结果”、只存摘要不存原始证据、GSC/GA4 只缓存日汇总等行为。

## 研究范围与证据口径

本报告读取了当前项目上下文、迁移清单、领域词汇、持久化 ADR、双验证切片决策以及旧 Heyup connector 与测试。

用户所说的 `day` 实际对应三类本地资产：

1. `/Users/russell/Desktop/04_product/DTC+/day/`：本地产品资料容器；没有可用于本研究的 Git remote 或已提交历史。
2. `/Users/russell/Desktop/04_product/DTC+/day/day-demo/`：实际存在 TypeScript/Drizzle/Neon 代码的应用原型，是本报告的代码参考。
3. `/Users/russell/Desktop/02_agent_dev/day-pipeline/`：27 个文档组成的管道规划包，没有 `.py`、`.sql`、`.ts` 或 `.js` 实现文件，也没有独立 Git 仓库。其状态仍是准备实施 News 标杆链路（`/Users/russell/Desktop/02_agent_dev/day-pipeline/STATUS.md:8-22`）。

GitHub 上同名个人仓库当前为空，不能作为代码证据。本报告只引用本地真实文件；这些仓库外文件仅作只读参考，不能把其内容、凭据或数据复制进本仓库。

外部事实只使用接口所有者的官方文档。供应商价格、配额和平台政策会变化，实施前必须按当时官方页面重验。

## Day 资产的可复用边界

### `day-pipeline`：可复用设计，不存在可复用代码

`day-pipeline` 把范围定义为公开市场信号的采集、ODS 和 DWD，不做信号评级与应用侧功能（`/Users/russell/Desktop/02_agent_dev/day-pipeline/CLAUDE.md:8-16`）。其中值得继承的设计是：

- 原始响应完整保存，不以当前解析字段替代 raw payload（`/Users/russell/Desktop/02_agent_dev/day-pipeline/CLAUDE.md:28-32`）。
- ODS 将主体内容、评论/回复和运行日志分开；运行日志记录规模、成本与错误（`/Users/russell/Desktop/02_agent_dev/day-pipeline/docs/BQ_LAYOUT.md:8-14,24-35`）。
- 评论采用首次快照、top-N 和冷门内容阈值三道成本闸门（`/Users/russell/Desktop/02_agent_dev/day-pipeline/docs/SCOPE_AND_BOUNDARIES.md:21-41`）。
- 先用 News 打通窄链路，再逐源扩展（`/Users/russell/Desktop/02_agent_dev/day-pipeline/CLAUDE.md:43-48`）。

但其增量策略存在文档冲突：早期材料写成“采集层无状态 append、dbt 以自然键去重”（`/Users/russell/Desktop/02_agent_dev/day-pipeline/docs/SOURCES.md:21-24`），后续读过中台代码的计划则采用采集端 max-date 回看 + MERGE、DWD 再 incremental merge（`/Users/russell/Desktop/02_agent_dev/day-pipeline/plans/2026-06-26-news-narrow-link.md:28-34,94-97`）。因此本项目不继承其中任一方案为既定事实；只继承“幂等、可回补、保留运行血缘”的结果契约。

### `day-demo`：可复用接口模式，具体实现需改写

可以借鉴：

- `SyncModule` 把纯 fetch 与 analyze/map/persist 两阶段分开（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/intelligence/sync-engine/types.ts:10-25`）；默认市场和本地市场分别采集再合并，fetch 阶段不写 DB、不调 AI（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/intelligence/sync-engine/pipeline.ts:16-25,34-81`）。
- 通用 social provider 支持 `search`、可选 `searchBatch`、可选 `fetchComments`，并接受 `since/limit/language/region`（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/social/sources/types.ts:4-37`）。
- provider chain 可按平台配置首选与 fallback；批量优先、关键词有限并发、全部失败才切备用（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/social/sync-module.ts:36-67,77-138`）。
- 监测配置能从品牌、产品、竞品、品类派生关键词，并叠加 exclude/custom 与市场本地化（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/intelligence/subscription/monitoring-config.ts:30-67,106-156`）。这可改造成 SEO MVP 的查询计划生成器。
- News 已有 Serper 批量请求、RSS 并发和 source ID 去重（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/news/sync-module.ts:20-117`）。

必须改写：

- demo 在采集后立即做 LLM 分析；分析失败的 mention/article 会被丢弃并等待下轮重抓（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/social/sync-module.ts:256-285`；`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/news/sync-module.ts:172-206`）。SEO MVP 必须先 raw-first 持久化，再异步标准化；LLM 失败不能造成证据丢失。
- `social_mention` 只存 snippet、metadata 和评论分析，没有完整 raw payload 或评论明细（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/db/schema.ts:1318-1350`），不满足 Opportunity 可追溯要求。
- RSS 在 demo 中仅用于校正 Serper 日期，RSS-only 文章会被丢弃（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/news/reconciler.ts:5-32`）；它不能当作已完成的独立 feed collector。
- GSC 客户端虽然支持 date/query/page/country/device、过滤和分页（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/marketing/clients/google-search-console-client.ts:21-59,127-187`），实际定时路径只取 date 日汇总；GA4 页面拆分只按需查询且明确不缓存（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/marketing/clients/google-analytics-client.ts:116-142,233-276`）。SEO MVP 必须持久化 page/query 级证据。
- demo 没有 Google Trends collector，也没有通用 SERP 快照模型。

最终复用判断：**继承接口和失败处理思想，不复制整个应用层；把未来 Day/Marketing Listening 当一个可替换的 External Listening Provider，而不是 SEO 系统数据库或完整数据面。**

## 统一采集契约

### 1. 查询计划（Collection Plan）

每次采集必须先生成可审计计划，至少包含：

- `project_id`、`validation_slice_id`、`profile_version`；
- `source_family`、`provider`、`provider_version`；
- brand/product/competitor/category/problem/use-case 等 query group 与原始 query；
- market=`US`、language=`en`，以及 provider 使用的实际 locale 参数；
- 请求时间范围、页数/条数上限、刷新策略、预算上限；
- 计划版本和创建时间。

关键词不是一个没有语义的字符串池。MVP 可以从 Brand SEO Profile 派生一批显式 query group，并允许人工添加/排除；动态扩展词必须保留 `parent_query`、扩展来源和生成版本，才能判断新词来自 Trends、SERP related searches、News 还是人工输入。

### 2. 原始观测（Raw Observation）

任意 provider 先映射到共同最小包，不要求在采集层统一所有业务字段：

| 字段组 | 最低字段 |
| --- | --- |
| 身份 | `observation_id`、`project_id`、`source_family`、`provider`、`provider_record_id`、`source_url` |
| 查询血缘 | `collection_run_id`、`query_id`、`matched_queries[]`、`market`、`language` |
| 时间 | `published_at`（可空）、`observed_at`、`retrieved_at`、`provider_time_zone` |
| 内容/指标 | provider-specific parsed fields + `raw_payload_ref`、`raw_payload_hash`、`schema_version` |
| 品质 | `parse_status`、`completeness_flags[]`、`is_partial`、`provider_warnings[]` |
| 安全 | `retention_class`、`contains_user_content`、`pii_scan_status` |

真实 raw payload 存在受控后端/BQ 对象中；GitHub 只允许 schema、合成 fixture、脱敏摘要和 hash/reference。Reddit 等用户内容还必须遵守来源删除与留存政策，不能因为“公开可见”就无限期复制原文。

### 3. 采集运行（Collection Run）

必须把“空结果”和“采集失败”拆开。建议统一状态：

- `not_configured`：该切片未启用来源；
- `credential_missing` / `access_pending`：能力尚未 ready；
- `running`；
- `succeeded_with_data`；
- `succeeded_empty`：请求成功且明确无结果；
- `partial`：部分 query/page 成功；
- `rate_limited`；
- `auth_failed`；
- `provider_error`；
- `schema_error`；
- `timed_out`；
- `stale`：最后成功观测超出 SLA。

运行日志至少保存 request count、record count、new/updated count、重试次数、HTTP/provider 错误码、quota/cost（可取得时）、started/finished、cursor/回看窗口、原始结果位置和代码版本。重试只针对 429、5xx、超时等可恢复错误，采用带 jitter 的指数退避并设最大尝试；401/403、schema mismatch 和非法请求不盲重试。

### 4. 来源适配与替换

下游 Signal 只能依赖共同 Observation 与 Run，不得读取 Serper、Apify 或 Day 的私有字段。切换 provider 时必须保留：

- 稳定的 `source_family`，同时记录新的 `provider/provider_version`；
- market/language/query/time 的同等语义；
- source URL 或稳定 provider ID；
- 原始证据引用、观测时间、采集时间和运行状态；
- 并行重叠窗口，用同一 query set 对比覆盖率、重复率、日期准确率和关键字段缺失率；
- 不回写或覆盖旧 Observation，Signal/Opportunity 指向其实际使用的记录。

未来 Marketing Listening 到位时，只替换 News/Reddit 等外部市场信号 provider；GSC、GA4、Content Inventory、关键词指标和 SERP 仍是 SEO 专属或相邻数据面，不能假设由 Listening 自动覆盖。

### 5. 来源 ready 的最低标准

某来源只有同时满足以下条件才算 ready：

1. 两个验证切片所需配置、权限和凭据已在受控环境中可用；
2. 至少一次真实只读 smoke run 成功，并保留运行日志；
3. `succeeded_empty` 能与失败状态明确区分；
4. 原始结果先于 LLM/规则分析持久化，且能从标准记录回到原始证据；
5. market/language/time 参数经过样本核验；
6. 幂等重跑不制造无法解释的重复；
7. 429/5xx/timeout 有界重试，401/403/schema error 可见；
8. freshness SLA、成本/配额和数据保留规则有监控；
9. 有合成或脱敏 contract fixture，schema 演进有版本。

“代码类存在”“本地有 connector”或“能手工打开网页”都不算 ready。

## 分来源研究与 MVP 契约

### GSC：搜索可见性事实源

Search Analytics API 支持按 date、query、page、country、device 等维度和过滤条件查询，但官方明确结果按 clicks 排序且不保证返回所有行；API 暴露的是 top rows，不应把未返回 query 解释为零需求。[Search Analytics query](https://developers.google.com/webmaster-tools/v1/searchanalytics/query) 官方还说明每天每 search type 最多暴露 50K 行，单页最多 25K，需要 `startRow` 分页。[获取全部可用数据](https://developers.google.com/webmaster-tools/v1/how-tos/all-your-data)

MVP 合约：

- 每日拉取 finalized 数据，主分析截止 D-3；这是基于官方说明 Search Console 通常有 2–3 天延迟的保守工程窗口。[Search Console 数据说明](https://support.google.com/webmasters/answer/96568)
- 每切片至少持久化 `date × page × query × country × device × search_type` 能力；实际可按多种低维查询拆批，避免一次 page+query 长窗口造成高 load。
- 每日增量拉 D-3，并回补最近 7 天；首次准备近 180 天时按日或短窗分页，不反复重拉整段。官方指出 page/query 分组过滤和长日期范围更耗 load，且有 1,200 QPM/site 与 load quota。[Search Console 配额](https://developers.google.com/webmaster-tools/limits)
- 保存 property、search type、aggregation type、dimensions、filters、data state 和完整请求 hash；`final` 与 fresh/partial 数据不得混为同一口径。
- 这是趋势和覆盖证据，不是绝对完整 query inventory；Opportunity 解释需注明隐私过滤与 top-row 限制。

已验证：本地 Day 客户端的 OAuth/API 调用和维度映射代码存在。待验证：Heyup/REDMAGIC property、权限、180 天行数、实际分页成本和共同完整日期；未使用真实凭据做 smoke test。

### GA4：内容参与与业务结果事实源

GA4 Data API 的 `runReport` 支持页面、来源、会话、参与、key event、收入等维度/指标；可用字段以官方 schema 为准。[GA4 API schema](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema) Standard property 的 Core quota 包括每 property 每日 200,000 tokens、每小时 40,000 tokens、每 project/property 每小时 14,000 tokens和 10 个并发请求；复杂过滤、长日期范围和高基数维度会提高 token 消耗，并可通过 `returnPropertyQuota` 观察实际用量。[GA4 配额](https://developers.google.com/analytics/devguides/reporting/data/v1/quotas)

MVP 合约：

- 每日拉取已完整的 D-2 页面级数据，并回补近 12 天。D-2 是保守建议；官方说明 standard intraday 常为 2–6 小时、日数据约 12 小时，但处理可能持续 24–48 小时，且 key event attribution 最长可在 12 天内变化。[GA4 freshness](https://support.google.com/analytics/answer/11198161)
- 最低页面粒度：`date × landingPage(+queryString 或项目确认的 canonical key) × sessionDefaultChannelGroup`，指标至少包括 organic sessions、active users、engaged sessions/engagement rate、key events；DTC 可加 purchase revenue，但不得把 revenue 缺失解释为 SEO 无价值。
- 保存 property timezone、currency、request dimensions/metrics/filter、quota consumption 和 `(other)`/thresholding 风险；与 GSC 的 Pacific Time 日界不能直接按日期裸 join。
- 初次 180 天 backfill 分段执行；高基数页面查询限制并发，保留总量 query 做对账。

已验证：Day 有通用 `runReport` 代码和按需页面查询。待验证：两个 property 的实际权限、事件命名、organic channel 口径、key event/revenue 可用性、时区和 token 消耗。

### 关键词指标：需求规模与商业竞争代理

Google Ads `KeywordPlanIdeaService` 可用 keyword、URL 或组合 seed 生成 ideas，并按 location/language/network 返回历史指标；历史指标包括近 12 个月平均和逐月搜索量、广告竞争与 bid ranges。[Keyword ideas](https://developers.google.com/google-ads/api/docs/keyword-planning/generate-keyword-ideas) [Historical metrics](https://developers.google.com/google-ads/api/docs/keyword-planning/generate-historical-metrics)

它不能被当作自然搜索难度：competition 是广告位竞争。官方建议缓存结果，因为历史指标按月刷新；Planning service 限 1 QPS/CID。[Keyword Planning 概览](https://developers.google.com/google-ads/api/docs/keyword-planning/overview) [API 配额](https://developers.google.com/google-ads/api/docs/best-practices/quotas) 此外 KeywordPlanIdeaService 在 Explorer Access 下受限，需要 Basic 或 Standard 权限。[Access levels](https://developers.google.com/google-ads/api/docs/api-policy/access-levels) 因此 Google Ads 适合作为广告需求/CPC 的校准源，但它单独不能提供自然 KD、intent、竞品排名词、content gap 与反链，不是本报告推荐的唯一综合 SEO provider。

MVP 合约：

- 把关键词“发现”和“指标快照”分开：seed/related query 可以来自多源；volume/competition/CPC 是带 provider、market、language、month 的快照。
- US/English 固定传真实 geo/language constant；保存 close variants，不把 provider 合并后的词误当精确匹配量。
- 新 query 首次按需取指标；同 market/language 的已有词最多月度更新，不随每次 Opportunity 重查。
- 综合 provider 的 volume/KD/intent 与 Google Ads volume/CPC 分别保存；校准时比较覆盖和排序，不把不同口径求平均。任一来源未 ready 都不可用 LLM 伪造指标。

已验证：Google Ads 官方能力、权限门槛和限速，以及下文四个商业 provider 的公开 API 能力。待验证：Fastlane 是否已有可复用的 Google Ads developer token/manager account、可允许的 keyword research 用途，以及 DataForSEO/Ahrefs 的真实账户、合同和固定样本表现。任何来源当前都不能只凭文档标记 ready。

### SERP：搜索意图、竞争页面与版式快照

Google 没有提供用于通用自然结果抓取的第一方 SEO SERP API。MVP 在 DataForSEO spike 通过后优先用其 Google Organic Live SERP，使 keyword/domain 数据和 SERP 使用同一综合 provider；旧 Heyup 的 Serper `/search` 适配器雏形（`heyup_buying_guides/discovery/serper.py:8-24`）保留为连续性 fallback。无论 provider，输出都要从 organic list 扩展为不可变快照：query、location/language/device、requested_at、organic results、rank、title、URL/domain、snippet、SERP features、related searches/PAA（可得时）、raw reference。

DataForSEO SERP API 支持 Google、location、language、device、深度以及 Standard/Priority/Live 模式；Live 适合立即取得快照，Standard 适合可排队的批量任务。[DataForSEO SERP API](https://docs.dataforseo.com/v3/serp-overview/) Serper 官方页面声明 Search/News 等实时端点、可定制 location；当前 Starter 标价为 $1/1K queries、50 QPS，价格和套餐实施前需重验。[Serper 官方页面](https://serper.dev/) 费用应按“唯一 query × locale × cadence × depth/priority”预算，而不是只看返回结果条数。

MVP 合约：

- 核心已发布/候选词每日快照；长尾池每周；新闻或趋势事件可触发额外快照。
- 同一 query 每日默认一个 canonical snapshot，人工重跑另存 run，不覆盖旧排名。
- 429/5xx 有界重试；credit exhausted 独立状态；响应缺字段触发 schema warning。
- SERP 是抽样环境，不宣称代表所有用户；必须保存 location、language、device（若 provider 支持）和采集时间。

已验证：旧 Heyup adapter、Serper 官方能力以及 DataForSEO 官方 SERP 契约。待验证：DataForSEO 与现有 Serper 账户额度、同一 US/en 样本的 top-10 overlap/feature coverage、真实响应字段、批量成本和失败语义。

### Google Trends：变化速度与相关查询

Google 已发布官方 Trends API Alpha，但仍只对有限测试者开放；它提供约 5 年滚动窗口、日/周/月/年聚合、region/subregion，以及跨请求一致标度的数据，最新到约两天前。[Google Trends API Alpha](https://developers.google.com/search/apis/trends) [官方发布说明](https://developers.google.com/search/blog/2025/07/trends-api) 在没有确认 Alpha 权限前，不能把它列为 MVP 可用接口。

本项目旧代码已经实现 Apify `apify/google-trends-scraper` 的 run → poll → dataset 流程、3 个月 US 查询输入和失败 fallback（`heyup_buying_guides/seed_query_generator.py:128-225`），测试也覆盖成功结构（`tests/test_workflow.py:493-517`）。Actor 官方页当前说明可输出 interest over time、地区、top/rising queries/topics，价格从 $0.30/1K results 起；Actor 价格和 schema 可由作者变更，必须记录 actor build/version。[Apify Trends Actor](https://apify.com/apify/google-trends-scraper)

MVP 合约：

- 首选 Apify Actor，每日查询 Listening/Profile 中活跃 seed；保存 input、actor/build/run/dataset ID、时间窗、geo、原始相对值、partial 标识和 related queries。
- 相对指数只在相同请求归一化上下文中解释；不要把 0–100 当绝对搜索量，也不要把不同批次的数直接相加。
- 旧 `trending/rss` 解析器（`heyup_buying_guides/discovery/google_trends.py:9-32`）只适合产生“当前热门 seed”辅助观测，不能替代某关键词的 interest-over-time。
- timeout、actor failed、empty dataset、empty trend fields 分开记录；Apify 官方 API 支持 run 状态和 default dataset ID。[Apify API](https://docs.apify.com/api/v2)
- 一旦官方 Alpha 权限 ready，以并行重叠窗口校准后替换 Apify，历史 Observation 保留 provider 标识。

已验证：旧代码与测试、Actor 当前能力和官方 Alpha 状态。待验证：真实 Apify token、Actor schema/build、两个切片的单次费用和成功率，以及 Fastlane 是否已有 Trends Alpha 资格。

### News：事件、新品与媒体覆盖

`day-demo` 的 Serper News adapter 支持 `/news`、hl/gl 和批量关键词（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/news/sources/serper-source.ts:7-69`）；Google News RSS adapter 能提供精确 pubDate（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/news/sources/rss-source.ts:3-31`）。这验证了“Serper 负责内容覆盖、RSS 辅助日期”的模式，但 RSS 不是 Google 承诺的正式开发 API，不能假设稳定 SLA。

MVP 合约：

- 每 4 小时按 brand/product/competitor/category/event query group 拉 Serper News；低频项目可每日。
- 保存标题、URL、outlet/domain、snippet、provider date 原值、标准化 published_at、matched query、rank/image（可得时）和 raw reference。
- URL canonicalization + provider ID + normalized title 用于候选去重，但保留多 query 命中关系；不要只靠标题覆盖不同报道。
- Google News RSS 仅作补充和日期校正；后续对官方 newsroom/垂直媒体应建立独立 RSS feed adapter，RSS-only 项不能像 demo 一样丢弃。
- 将 Day/Marketing Listening 的 `dwd_news_article` 接入作为未来 provider；切换前验证字段、freshness、query lineage 和覆盖率。

已验证：Day demo 代码实现。待验证：Serper key、批量请求真实计费/响应、Google News RSS 长期可用性、应监测的具体媒体 feed；`day-pipeline` 的 BQ News 链路仍未实现。

### Reddit：社区问题、比较语言与使用场景

`day-demo` 已有 client-credentials OAuth、keyword new search、帖子字段和评论树代码（`/Users/russell/Desktop/04_product/DTC+/day/day-demo/apps/web/lib/services/social/sources/reddit-source.ts:9-28,66-158`）。但其中无 OAuth 时退回公共 `.json` 的做法不应继承：Reddit 当前官方说明必须使用注册 OAuth token 和具名 User-Agent，未认证流量会被阻止；免费合格使用限 100 QPM/OAuth client，并要求监控 rate-limit headers。[Reddit Data API Wiki](https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki)

Reddit 还要求删除已删除的用户内容/作者标识，并建议在 48 小时内例行删除所存用户数据；商业用途或超限研究可能需要单独协议。[Reddit Data API Terms](https://redditinc.com/policies/data-api-terms) 因此 Reddit 不只是工程接入问题，还存在用途与留存合规门槛。

MVP 合约：

- 只用获准 OAuth client；每 6 小时搜索高价值 query，低频词每日；优先帖子发现，评论只对高互动候选做有上限快照。
- 记录 subreddit、post ID/permalink、title/selftext 摘要、published_at、score/comment count/upvote ratio、matched query；作者身份默认不进入 SEO 标准 Signal。
- 原文只在受控、短期和政策允许范围保存；标准 Observation 尽量保存 source reference、hash 和非识别摘要，并建立删除同步/TTL。
- 读取 `X-Ratelimit-*`，按剩余额度调度；401/403、429、deleted、quarantined/restricted 分开处理。
- Reddit 结果为讨论证据，不是搜索需求量；不能用帖子数或点赞直接替代 keyword volume。

已验证：Day adapter 代码及当前官方 OAuth、QPM 和保留要求。待验证：Fastlane 商业 SEO 场景是否获准、OAuth app 状态、具体 subreddit/query 覆盖与删除机制；在此之前不得标记 ready。

## SEO 数据供应商候选矩阵与接入建议

商业 SEO 平台在本 MVP 中属于**供应商估算信号**，适合补足关键词难度、搜索意图、竞品排名、内容/关键词 gap、反链和域名流量估算。它们不是 GSC/GA4 的替代品，也不能把其估算值冒充第一方真实表现。MVP 应只接一个综合 provider，避免同一批关键词同时付费、重复存储，并避免把不同供应商的专有指标错误混成一个评分刻度。

### 候选矩阵

| 候选 | API、权限、认证与官方 MCP | 与本 MVP 相关的数据族 | US/en、历史与刷新 | 额度/计费与限制 | 相对现有来源的新增价值 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| **DataForSEO** | 注册后用 API login + API password 做 HTTP Basic Auth；Labs、SERP、Backlinks、Domain Analytics 等均有 API。官方 GitHub 组织发布了 [DataForSEO MCP Server](https://github.com/dataforseo/mcp-server-typescript)。 | Keyword suggestions/related/volume/KD/intent；Google SERP 实时快照与 features；ranked keywords、SERP competitors、domain/page intersection；backlinks/referring domains/new-lost；domain rank 与 traffic estimate。 | location/language 列表明确支持 US/English；SERP 是请求时扫描；Google 历史关键词/排名数据的可用起点按 endpoint/location 查询，历史搜索量 endpoint 通常可回溯至 2019，关键词数据库样本含 2021-08 起月度数据；量级指标按月更新。[Labs API](https://docs.dataforseo.com/v3/dataforseo_labs/overview/) [历史搜索量](https://docs.dataforseo.com/v3/dataforseo_labs-historical_search_volume-live/) | Pay-as-you-go，当前最低充值 $50，注册试用有 $1 credit；价格按 endpoint、行数、深度和 Standard/Live 模式计算。Labs 公开上限 2,000 calls/min、30 并发；SERP Standard、Priority、Live 分价。[Pricing](https://dataforseo.com/pricing) | 可同时替代“关键词指标 provider + 通用 SERP provider”，并新增竞品 domain/page intersection 和反链；比 Google Ads 多自然 KD/intent，比 Serper 多结构化 SEO 数据族。 | **MVP 首选 spike**：无年度 SaaS 套餐前置、API 颗粒度和成本控制最适合窄切片。通过质量、许可和真实成本验收后作为唯一综合 provider。 |
| **Semrush** | Standard SEO API 的常规接入要求 SEO Toolkit Business + 单独购买 API units；v4 用 `Authorization: Apikey` 和可撤销、可设 TTL 的版本专用 key。另有官方 [Semrush MCP](https://developer.semrush.com/api/v3/introduction/semrush-mcp/)，部分较低档 SEO 套餐可含 50K units，但 MCP 权益不等于任意生产批处理权益。 | Keyword metrics 含 volume/KD/intent/CPC/SERP features；top-100 organic results；domain organic keywords/competitors，以及最多 5 域名的原生 content-gap 报告；backlinks/referring domains/gap；Trends API 另提供网站流量与市场估算。 | v4 keyword metrics 明确支持 `country=US`，但没有独立 `language=en` 参数，需用英文输入和输出校验落实 US/en；月快照可请求到 2012-01。官方总体说明 SEO 历史始于 2012、Traffic & Market 始于 2017，但具体 endpoint/套餐可见范围需实测。[Keyword metrics](https://developer.semrush.com/api/v4/seo/keyword-reports/) [Data coverage](https://developer.semrush.com/api/v4/introduction/available-data/) | Standard 按 report/返回行计 units，历史数据通常更贵；常规上限 10 RPS、10 并发。v4 Keyword/Backlinks 在 2026-08 仍标 Early Access，schema/价格可变。[API access](https://developer.semrush.com/api/v4/get-started/api-access/) | 原生多域 content gap 和可另购的跨渠道竞品流量最有差异；其他 keyword/backlink 能力与 DataForSEO/Ahrefs 重叠。Traffic & Market 与 GA4 不同，前者是竞品估算。 | **Phase 2 / 条件备选**：只在确需原生 content gap 或跨渠道竞品流量、已有套餐/units，并解决一个月缓存与 AI 使用限制后接入；不作为 MVP launch blocker。 |
| **Ahrefs** | 当前官方 API v3 可用于 eligible paid plans；workspace owner/admin 创建 API key，请求用 `Authorization: Bearer`。默认 60 requests/min。官方还提供 Lite 起可用的 hosted [Ahrefs MCP](https://docs.ahrefs.com/en/mcp/docs/introduction)，但官方明确 MCP endpoint 不允许当通用脚本 API，生产采集必须走 REST API。 | Site Explorer 的 backlinks、organic/paid keywords 与 traffic estimates；Keywords Explorer 的 volume/KD/intent/parent topic/traffic potential、volume history/ideas；SERP Overview top 100；Rank Tracker、Site Audit、Batch Analysis。API 无独立 Content Gap endpoint，可用 organic competitors + organic keywords 差集实现，但更耗 units。 | keyword/SERP endpoint 支持 `country=us`，核心 keyword endpoint 没有独立 `language=en` 参数，需 adapter 后置校验；套餐公开历史窗口为 Lite 6 个月、Standard 2 年、Advanced 5 年、Enterprise unlimited。搜索量通常至少月更；SERP 与 backlink freshness 随数据族和热度变化。[API introduction](https://docs.ahrefs.com/en/api/docs/introduction) [Plans](https://ahrefs.com/pricing) | 按返回行和请求字段消耗 API units，非免费请求最低 50 units；公开套餐当前含每月 100K/400K/1M/2M API integration units，单次行数上限随档位变化；Lite/Standard/Advanced 的额外容量限制需按账户确认。 | 强项是 Ahrefs 自有 link index、organic traffic/排名、parent topic 与 traffic potential；与 DataForSEO 高度重叠，但采购门槛低于 Semrush Standard API，可作为整套替代数据库。 | **第一备选**：DataForSEO 未通过且 raw retention 获书面确认时，优先对 Ahrefs Direct API 做同样本 spike；不建议同时购买两者。 |
| **Similarweb（后续专用）** | API 是 subscription add-on，也有 API-only package；管理员生成 API key。官方 hosted [Similarweb MCP](https://developers.similarweb.com/docs/similarweb-mcp) 要求 API-only、Business 或 Enterprise 等带 API 权限的订阅。 | 网站 visits/engagement、channel mix、geography、popular pages、referrals、audience overlap；Search 的 SERP players/click-share；不以 backlink/KD 为核心。 | country filter 支持美国；Website Batch 数据最多可有 61 个月历史，实际 countries/history 由 capability endpoint 和合同决定。低流量/小众站点可能无结果。[Websites dataset](https://developers.similarweb.com/docs/websites-dataset) | 按返回结果/指标/时间粒度消耗 data credits，月度刷新额度；API 需销售或账户套餐开通，价格不是公开统一 pay-as-you-go。[API overview](https://developers.similarweb.com/docs/similarweb-web-traffic-api) | 与 GA4 的区别是可看竞品估算流量、channel share 和 audience overlap；对市场份额/竞品规模有差异价值，但不补齐关键词 KD、反链和实时 SERP 的最小组合。 | **不进入 MVP 综合 provider 采购**；到竞品基准或市场份额节点再单独评估，不能用其估算流量替代 GA4 sessions。 |

### 为什么不把 Moz 纳入本轮 shortlist

Moz 的链接索引和 DA/PA 可以提供反链/authority 的另一套专有口径，但这与 DataForSEO、Semrush、Ahrefs 已覆盖的反链与域名权威度高度重叠。本轮没有从可访问的 Moz 官方开发者资料中核验到一套同时覆盖 keyword、SERP、content gap 和 domain traffic 的当前公共 API 契约，也没有找到 Moz 官方 MCP 的一手证据。因此本 MVP 不为“再多一个 authority 指标”增加第四套采集与校准成本；若组织已有 Moz API 合同，再按“反链专项 provider”做独立 spike，而不是综合 provider 候选。这里的结论是**证据不足且差异价值有限**，不是断言 Moz 没有任何 API。

### 供应商指标不得跨库直接混分

下面这些名称相似但不是同一个量：

- Semrush KD、Ahrefs KD、DataForSEO `keyword_difficulty` 的模型、索引、更新点和标度都不同；一个 provider 的 60 不能直接与另一个 provider 的 60 求平均。
- Semrush/Ahrefs/DataForSEO 的 organic traffic estimate 与 Similarweb visits、GA4 sessions 不是同一测量对象；GA4 是站点第一方观测，其他是供应商模型估算。
- Authority Score、Domain Rating、DataForSEO Rank 等只能保留为 `provider_metric_namespace + metric_name + metric_version`，不能统一改名为一个未经校准的 `authority` 数字。
- SERP 只能在相同 provider、query、US/en、device、时间和深度配置内比较；切 provider 必须运行重叠窗口，记录 top-10 overlap、feature coverage 和排名差异。

因此本 Issue 只把供应商输出定义为可追溯的 Raw Observation/Metric Snapshot，**不决定 Opportunity 评分权重**。评分节点将来可以选择 provider 内 percentile、显式分桶或经验证的归一化方法，但不得在这里提前固化。

### 数据溯源、缓存与合同边界

所有商业 provider 的标准记录至少额外保存：`provider_dataset`、`endpoint`、`api_version`、`metric_namespace`、`requested_fields`、`location/language/device`、`snapshot_month` 或 `observed_at`、`request_id/task_id`、`cost`、`raw_payload_hash/ref` 和 `terms_review_version`。供应商自己的结果保留期，不等于本项目拥有无限期存储或再分发权：

- **DataForSEO**：Standard task 一般可由供应商端取回 30 天，Live-only 的 Labs/Backlinks 结果不会由供应商保留，SERP HTML 仅 7 天；因此若选用必须在成功响应时立即 raw-first 落库。[Result retention](https://dataforseo.com/help-center/how-long-do-you-keep-results) 其当前条款限制以 SERP 数据损害搜索引擎业务的用途，但没有为本报告明确授予对外转售权；内部长期存储、衍生数据和展示范围仍需采购/法务书面确认。[Terms](https://dataforseo.com/terms-of-service)
- **Semrush**：官方条款限制为内部业务使用，禁止未经许可的转售/第三方提供，并明确 API 数据未经书面同意最多缓存一个月；当前条款还限制把 Semrush 的 insights、analyses 和 outputs 用于开发、训练、改进、微调、测试或增强 AI/ML，官方嵌入式集成是例外，但并未自动覆盖本项目的 LLM 分析流水线。[API restrictions](https://developer.semrush.com/api/v4/introduction/api-usage-restrictions/) [Semrush Terms](https://www.semrush.com/company/legal/terms-of-service/) 这与本项目长期 raw evidence 和 LLM 初审目标存在直接冲突；若采用，必须先取得书面许可，或由法务批准只保留允许的引用/hash/派生快照和 TTL 删除方案。不能先存 180 天再补手续。
- **Ahrefs**：公开条款授予的是内部业务用途的有限许可，并限制未经许可的复制、销售、发布和商业利用。[Ahrefs Terms](https://ahrefs.com/legal/terms) 条款没有在本轮检索中给出通用“可缓存 N 天”承诺；因此 raw payload 的内部保留期、报告展示和衍生物权利要以实际订单/合同确认。
- **Similarweb**：公开条款称数据包含第三方数据、估算和外推，并限制未经同意向第三方展示/分享。[Similarweb Terms](https://www.similarweb.com/corp/legal/terms/) 该数据只能标为 modeled estimate；项目若未来接入，需把内部存储、客户交付和 attribution 写入合同验收。

官方 MCP 的存在只证明厂商支持 agent 式查询，不自动证明适合生产定时采集、批量成本可控或可绕过 REST API 的合同限制。尤其 Ahrefs 明确禁止把 hosted MCP 当通用程序接口。MVP 的生产 collector 应以官方 REST API 为准；MCP 可用于人工探索、能力发现和 spike 对照，并同样记录调用成本与来源。

### MVP 选择与必须实测的 spike

**推荐只选一个综合 provider：DataForSEO 首选，Ahrefs 第一备选；Semrush 只在 Phase 2 或既有合同条件满足时接入。** Similarweb 留作后续竞品流量/市场份额专项；Moz 暂不进入。Serper 仍保留为 SERP 连续性 fallback，Google Ads Keyword Planning 保留为 volume/CPC 口径校准来源，GSC/GA4 始终保留为第一方表现事实。

采购或实施前必须用同一固定样本完成一次只读 spike：

1. 为 Heyup 和 REDMAGIC 各选一组 brand/product/category/problem/comparison query，并固定 US、English、desktop、同一采集日；竞品域名也固定，避免样本漂移。
2. DataForSEO 至少调用 keyword overview/ideas、Google organic SERP、ranked keywords 或 domain intersection、backlink summary；记录每个 endpoint 的真实成功率、空值率、响应时间、内部 status code、返回版本和实际 `cost`。
3. 同一批 keyword volume 与 Google Ads 的区间/排序做校准；SERP top 10 与 Serper 做 URL overlap 和 feature coverage 对照。比较是为了理解口径与覆盖，不是把两个 provider 的值平均。
4. 对 KD、intent、domain traffic、backlink/new-lost 抽样人工核验可解释性；确认每个字段的单位、snapshot month、`NULL` 语义和更新日期。
5. 用供应商的 free/test capability 先跑 schema；再以真实付费账户验证 US/en 数据、分页、限流、余额不足、无结果、401/403、429、5xx 和部分任务失败的状态映射。
6. 在真实写入前完成合同检查：允许的 raw/parsed 保留期、内部 dashboard 展示、LLM 输入、客户交付、删除/TTL 和 attribution。任何不允许 raw-first 的 provider 都不能在未修订 ADR/合同前标记 ready。
7. 用 REST API 做生产候选 smoke；官方 MCP 只做同查询人工对照，验证 MCP 返回是否省略字段、是否隐藏成本或改变分页，不能把自然语言回答当原始证据。
8. 连续跑两个刷新周期，核对 snapshot 是否稳定、同请求是否重复计费、增量去重是否幂等，并形成按“query 数 × endpoint × cadence”的月成本估算。

若 DataForSEO 在数据覆盖、可解释性、许可或真实成本任一关键项不通过，再对 Ahrefs 做同样本 spike；Semrush 只在确需原生 content gap/跨渠道竞品流量，或组织已有合同且解决缓存与 AI 条款时实测。不得同时把三个 provider 接入 MVP 后再用 Opportunity 评分“选优”，那会把供应商选择问题和业务评分问题混在一起。

## Freshness、成本和失败处理总表

| 来源 | Freshness/SLA 建议 | 主要成本或限额 | 不可混淆的失败状态 |
| --- | --- | --- | --- |
| GSC | 每日 D-3；回补 7 天 | load quota、分页、50K rows/day/type | 无行、隐私/top-row 截断、quota、property 无权 |
| GA4 | 每日 D-2；回补 12 天 | tokens、并发、高基数 | 无流量、threshold/(other)、quota、指标不兼容、无权 |
| Keyword | 新词按需；月更 | 综合 provider endpoint/row units；Google Ads 1 QPS/CID | no metrics、access restricted、partial rows、quota、provider missing |
| SERP | 核心词日更；其余周更 | 每 query/task credit、深度与优先级 | no results、credit exhausted、rate limited、schema drift |
| Trends | 日更；官方 Alpha 最新约 D-2 | Actor 结果/计算费；Alpha access | no interest、empty dataset、actor timeout/fail、partial |
| News | 4 小时或日更 | Serper query credit；RSS 无 SLA | no coverage、provider failure、date parse error、feed stale |
| Reddit | 6 小时或日更 | 100 QPM/OAuth client；合规/留存 | no posts、auth denied、rate limit、deleted/restricted |

## 双切片的实际就绪门槛

在开始每切片至少 10 个真实 Opportunity 的验证前，必须完成：

1. Heyup 和 REDMAGIC 的 GSC/GA4 property 映射及一次真实 180 天 backfill 验证；
2. 两个切片的 Content Inventory 可按 URL/canonical 与 GSC page、GA4 landing page 对齐；
3. US/en 综合 SEO provider 已通过固定样本 spike、合同审查并获得实际权限；核心 keyword endpoint 若不能强制 `language=en`，adapter 已落实输入限制与输出语言校验；
4. SERP、Trends、News、Reddit 都有至少一次真实成功运行、raw evidence 和运行状态；
5. 每个来源至少准备 `success_with_data`、`success_empty`、`provider failure` 三类 fixture；
6. 数据库能够保存 Collection Plan → Run → Raw Observation → Standard Signal 的引用链；
7. 两个切片使用截至“最近共同完整日期”的近 180 天，但外部事件源可从系统开始持续积累，不强求供应商能回放完整 180 天；历史缺口必须显式标注。

其中第 2 项由 Content Inventory 节点解决；REDMAGIC 的 BQ 产品评论和客服工单由 VOC View 节点解决。本节点不能代替它们，但它们是双切片整体 ready 的组成部分。

## 已验证、待验证与不成立的结论

### 已验证

- Day 的真实代码在 `day-demo`，而 `day-pipeline` 是未实施的规划包。
- Day demo 已有 News、Reddit、GSC、GA4、provider/fallback/market-localization 的参考实现。
- 旧 Heyup 已有 Apify Trends、Serper、Reddit 和 Trends RSS 的 connector 雏形与部分测试。
- GSC/GA4/Google Ads/Reddit 的官方接口能力和当前主要配额/政策如上所述。
- Google Trends 官方 API 目前仍是有限 Alpha；Apify Actor 是当前更现实的 MVP provider。

### 必须通过凭据或组织信息验证

- Heyup/REDMAGIC 的 GSC、GA4 实际 property、权限、时区、事件和数据完整性；
- Fastlane 的 Google Ads developer token 是否具备 Basic/Standard 及 Keyword Planning permissible use；
- DataForSEO、Ahrefs、Semrush 是否已有账户/合同，以及实际 US/en 覆盖、余额、结果留存、LLM 使用与客户展示权利；
- Serper、Apify 的现有账户、余额、真实响应和配额；
- Reddit OAuth app 和商业使用/数据留存是否获得许可；
- Google Trends Alpha 是否已获准；
- 中台是否已经实现 Day News/Reddit DWD，而非仍停留在本地计划；
- 最终 Operational DB / Warehouse 的物理分工和具体技术选型。

### 明确不成立

- “找到了 day-pipeline，所以已有一套可直接接入的 BQ 管道”；它没有实现代码。
- “Day demo 已覆盖 SEO MVP”；它没有 Trends、通用 SERP、Content Inventory，也没有 SEO 所需的 GSC query×page 与 GA4 landing-page 持久化。
- “某来源返回空数组就表示市场没有信号”；空结果必须与未配置、无权、限流、超时和 schema error 分开。
- “LLM 分析后保存摘要即可追溯”；原始证据必须先持久化，LLM 失败不能删除观测。
- “关键词广告 competition 就是自然搜索难度”；二者口径不同。

## 核心决策建议

1. **采用七个采集来源族加 Content Inventory 的最低组合，不扩成完整 Listening。** 先让 GSC、GA4、Keyword、SERP、Trends、News、Reddit 与 Content Inventory 形成可追溯闭环；YouTube/X/TikTok 等留给后续 Day/Marketing Listening。
2. **raw-first，Signal-later。** 任意来源先保存 Collection Plan、Run 和 Raw Observation，再由规则/LLM 标准化；分析失败绝不丢数据。
3. **适配器只负责来源语义。** 下游只能依赖统一 Observation/Run；provider 切换要并行校准，不覆盖历史证据。
4. **把来源 ready 当验收状态。** 没有凭据、live smoke run、raw persistence、明确空/错状态和 freshness 监控，就不能开始双切片 Opportunity 验证。
5. **Day 是未来上游，不是当前阻塞项。** 复用 `day-demo` 的接口模式、`day-pipeline` 的 raw/run-log 设计；具体 collector 按本项目重写。未来 Day DWD 可替换 News/Reddit provider，但不替代 SEO 专属表现和 SERP 数据面。
6. **商业 SEO provider 只接一个。** 先用固定 Heyup/REDMAGIC 样本验证 DataForSEO；通过后由它提供关键词、SERP、竞品 gap 与反链估算，Ahrefs 作为第一备选。Semrush 因 Business/API units、一个月缓存和 AI 使用限制只作 Phase 2 条件接入；Similarweb 只作后续竞品流量专项。Google Ads 保留为 volume/CPC 校准，不用 LLM 生成指标。
7. **供应商指标保持命名空间。** KD、authority、traffic estimate 和 SERP 快照不得跨供应商直接混分；本节点只保存 raw signal 与口径，不决定 Opportunity 权重。

## 本报告不包含

- Opportunity 的准入、评分维度、权重或阈值；
- Content Inventory、BQ VOC View 的完整 schema；
- Operational DB、BigQuery、Drizzle 的最终物理架构；
- 完整 Marketing Listening 的平台范围与实施计划；
- 任何生产代码、凭据配置或真实数据写入。
