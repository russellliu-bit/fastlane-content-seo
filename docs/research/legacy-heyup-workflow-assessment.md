# 旧 Heyup 工作流可复用能力与失败模式盘点

- 日期：2026-08-12
- Wayfinder 节点：盘点旧 Heyup 工作流的可复用能力与失败模式
- 结论性质：本地一手资料研究，不是新系统规格，也不代表实施决定

## 摘要

旧 `heyup_buying_guides/` 已经证明一条端到端链路可以跑通：配置与来源发现、候选提取、标准化、评分、Brief、结构化文章、校验、HTML 渲染、运行留痕和 CMS 草稿接口。最值得继承的不是当前的 `TopicCandidate`、评分公式或 Shopify/Amazon 代码，而是以下工程模式：阶段拆分、结构化数据契约、证据引用意图、可重复 fixture/stub 测试、运行级观测以及品牌实体归一化。

它不能直接升级为公司级 SEO 核心。代码把“美国英语科技商业内容”“Buying Guide/Comparison”“至少三个产品”“Affiliate/Shopify”固化在数据结构、Prompt、评分、校验和发布路径中；信号仍以已知关键词或硬编码查询驱动，`TopicCandidate` 被自动选中后直接进入写作，没有站内内容盘点、`SEO Opportunity`、动作决策、GSC/GA4 反馈或 DTC VOC。

历史运行快照还证明：`passed` 只表示当时那版校验器通过，不等于证据充分或可发布。40 份 Brief 的 124 个产品里，62 个没有规格，57 个没有正面证据，57 个没有负面证据；38 篇生成文章中，23 篇没有 `claim_references`，12 篇没有 `source_manifest`。个别 `passed` 运行甚至是零产品、零来源。这些快照适合用来建立失败样本和回归语料，不能直接作为新模型的金标数据。

因此建议：把旧包冻结为“可执行参考实现”，优先抽取契约、fixture 和失败样本；不要在旧编排器上继续堆新模式。新模型应围绕 `Raw Observation → Signal → Signal Cluster → SEO Opportunity → Action Decision → Content/Handoff → Publication Record → Performance Snapshot` 重新定义持久化领域对象，再选择性移植旧适配器和测试思想。

## 研究范围与证据口径

本报告读取了：

- 项目上下文、迁移清单、当前领域语言和持久化 ADR：`docs/context/PROJECT_CONTEXT.md`、`docs/context/MIGRATION_MANIFEST.md`、`CONTEXT.md`、`docs/adr/0001-persist-seo-lifecycle-data.md`。
- Heyup 知识库全部 15 个文件，从 `codex_knowledge_base/00_index.md` 进入。
- `heyup_buying_guides/` 全部 Python 源码与两个 Prompt 模板。
- `tests/test_workflow.py` 和 `tests/fixtures/audio_comparison/`。
- 本地只读 `assets/legacy/heyup-runs/` 全量文件统计，以及若干代表性运行的字段级检查。

证据强度按以下顺序理解：当前代码与测试说明“现在实现了什么”；内部扫描型知识库说明“Heyup 业务是什么”；迁移快照说明“历史上实际留下了什么结果”。知识库自身也标注了 draft、内部解释或外部参考等不同状态，例如索引要求把外部来源包当参考而非内部事实来源（`codex_knowledge_base/00_index.md:24-34`）。

> 重要限制：`assets/legacy/heyup-runs/` 是迁移快照，迁移清单明确声明其“不代表历史输出已经通过质量审核”（`docs/context/MIGRATION_MANIFEST.md` 的“完整性原则”）。本报告没有逐份使用当前 `validate_article` 重新执行校验；下文的 `passed/failed` 是历史 `run_report.json` 原值，不可解释为按现行规则重验后的结果。

## 旧系统实际边界

### 业务边界比旧代码宽

Heyup 不是单纯的购买指南站。知识库把它定义为社区驱动的内容与商业平台（`codex_knowledge_base/01_company_overview.md:9-33`），其内容层同时承担产品理解、趋势叙事、活动放大、评测可信度、购买指导和品牌曝光（`codex_knowledge_base/07_content_and_newsroom_architecture.md:12-20`）。已观察到的频道至少包括 Tech News、Hunts、Product Reviews、Buyer’s Guide、Brand Buzz、Trend & Insight Lab、Feature Stories 和 Creator Program（`codex_knowledge_base/07_content_and_newsroom_architecture.md:22-62`）。

产品又连接发现、试用、评论、社区、Affiliate 和零售（`codex_knowledge_base/05_product_lifecycle_and_catalog_architecture.md:12-35`）；Tryout 会产生需求、参与、评论、社证与商业资产（`codex_knowledge_base/06_tryout_and_campaign_architecture.md:62-73`）。这说明 Heyup SEO 模式至少需要消费产品生命周期、社区和内容频道上下文，不能继续把 Buying Guide 视为 Heyup 内容的默认全集。

### 代码边界是单一“内容生产流水线”

当前编排器的主路径是：发现主题，选择一个分数合格的主题，处理候选产品，生成 Brief 和文章，校验、渲染，再调用 Shopify 草稿发布（`heyup_buying_guides/orchestrator.py:37-148`）。动态发现依赖搜索 Grounding、Google Trends、可选 Serper 和 Reddit（`heyup_buying_guides/orchestrator.py:195-285`），但结果立即被压成 `TopicCandidate` 并自动挑最高项（`heyup_buying_guides/orchestrator.py:361-363`）。

现有数据类也围绕文章生产：`SourceDocument`、`CandidateProduct`、`DiscoverySignal`、`TopicCandidate`、`ArticleBrief`、`GeneratedArticle` 和 `RunReport`（`heyup_buying_guides/schemas.py:7-152`）。其中 `DiscoverySignal` 虽已命名，却没有进入主编排；主流程没有 `Raw Observation`、聚类、`SEO Opportunity`、动作决策、发布后指标或内容更新对象。

## 可直接复用的能力

这里的“直接复用”是指概念或隔离良好的通用组件可以原样或仅做命名适配后进入原型，不表示应保留旧编排器。

### 1. 运行级产物留痕和可观察性模式

`ArtifactStore` 按 `run_id` 建目录并记录每个 JSON/TXT 产物路径（`heyup_buying_guides/artifacts.py:9-23`）；编排器在 discovery、seed、grounding、Apify polling、Brief、文章和 report 等阶段持续写快照（例如 `heyup_buying_guides/orchestrator.py:159-191`、`heyup_buying_guides/seed_query_generator.py:70-93`、`heyup_buying_guides/seed_query_generator.py:228-257`）。这个模式适合继续作为调试/导出层，并与 ADR 所要求的后端系统事实来源并存；不能再把文件本身当唯一数据库。

### 2. 可替换的外部数据适配器边界

Google Trends、Reddit、Serper 和 Gemini Search Grounding 已被拆成独立客户端（`heyup_buying_guides/discovery/google_trends.py:9-32`、`heyup_buying_guides/discovery/reddit.py:10-117`、`heyup_buying_guides/discovery/serper.py:8-24`、`heyup_buying_guides/discovery/search_grounding.py:13-85`）。这些连接器的 HTTP 细节和缓存策略可以作为 SEO MVP 小型信号收集器的起点，但输出必须先映射为统一 Observation/Signal 契约，不能继续直接拼成 Topic。

### 3. LLM 结构化输出与确定性本地模式

LLM 层支持 Gemini、OpenAI-compatible 和 deterministic stub，且 Gemini 使用 JSON Schema 约束输出（`heyup_buying_guides/llm.py:14-20`、`heyup_buying_guides/llm.py:123-192`、`heyup_buying_guides/llm.py:240-271`）。这对原型很有价值：事实指标由数据源提供，LLM 只做结构化、归类和解释；本地 stub 则允许不依赖外部服务验证流程。

### 4. 品牌名称归一化与官方域名注册表

`brand_registry.py` 已有 canonical name、alias、domain 和规范化 key（`heyup_buying_guides/brand_registry.py:14-76`），`brand_official_websites.csv` 也包含 Heyup 相关的大量品牌映射。注册表可以成为通用实体解析的种子数据，但官网 URL 只能表明品牌归属，不能自动证明某个产品或声明。

### 5. 标准化、去重、结构化验证的工程骨架

候选按 `dedupe_key` 合并来源、证据、规格和置信度（`heyup_buying_guides/stages/normalize.py:8-22`）；文章校验器检查模板字段、证据 ID、FAQ、source manifest 与 claim references（`heyup_buying_guides/stages/validate.py:8-46`）。具体规则是 Buying Guide 专用的，但“先结构化，再校验，不合格即阻塞”的骨架应直接保留。

### 6. fixture 驱动的端到端测试方式

测试用固定 source documents 和 topic candidates 执行 CLI 端到端流程，检查产物、状态和持久化（`tests/test_workflow.py:55-200`）；同时对 LLM JSON、Amazon URL、Shopify payload、seed 规范化等边界做隔离测试（`tests/test_workflow.py:211-649`）。`tests/fixtures/audio_comparison/topic_candidates.json:1-190` 还展示了一份字段相对完整的候选样本。新原型应继承这种 fixture/stub 测试策略，但样本必须扩展为 Heyup + 一个 DTC 薄切片。

## 需要抽象后复用的能力

| 旧能力 | 可保留部分 | 必须改变的边界 |
| --- | --- | --- |
| 多源发现 | Connector、缓存、重试、运行日志 | 每条原始观测独立持久化；增加 source、project、market、language、observed_at、retrieved_at、raw reference、采集状态与版本；不直接生成 Topic |
| `DiscoverySignal` | 来源、query、score、evidence、observed_at 的雏形（`heyup_buying_guides/schemas.py:50-61`） | 拆开原始事实与计算分；增加稳定 ID、项目隔离、实体、市场、语言、去重/聚类关联、来源可信度和数据血缘 |
| `TopicCandidate` | 意图、信号摘要、风险、理由 | 替换为 `SEO Opportunity`；必须先检查站内覆盖，再记录准入结果、评分快照和 Create/Update/Expand/Merge/Link/Reposition/Monitor/Reject 动作 |
| `draftability_score` | 多维而非单分的意图 | 评分维度、权重和门槛版本化；事实指标与 LLM 解释分离；DTC 与 Heyup 可有不同策略，不沿用当前固定公式 |
| CandidateProduct 与证据 | 产品实体、来源 URL、evidence binding 的目标 | 证据必须是可验证声明，不得用品牌首页或泛化 positioning 充当事实；产品存在、页面类型和具体 claim 分层验证 |
| Article Brief / GeneratedArticle | SEO title、description、slug、sections、FAQ、source manifest 等结构化字段 | 变为多内容类型契约；品牌、市场、语言、版本、内部链接、内容资产 ID、证据 freshness 和 CMS handoff 独立建模 |
| `StateStore` | 运行/候选/文章状态持久化意识 | SQLite JSON blob 仅作原型；新 Operational DB 需要稳定实体、版本、状态机、审计和上下游关系；分析明细进入 Warehouse |
| Shopify publisher | Shopify-ready 字段映射经验 | 改成 CMS handoff/export；本项目不得调用 CMS 写入。外部回传 CMS ID、URL、状态和时间后形成 Publication Record |
| `RunReport` | run ID、状态、错误、产物索引 | 将 collection、normalization、qualification、scoring、content、handoff、performance 分成可追踪运行；不能用一个文章报告代表全生命周期 |

## 必须淘汰的单品牌或 Buying Guide 假设

### 1. 默认只有两种商业内容类型

代码只在 `comparison_roundup` 与 `buying_guide` 之间选择模板（`heyup_buying_guides/stages/generate.py:11-27`），Brief 固定为排行、如何挑选、FAQ 和推荐产品（`heyup_buying_guides/stages/briefing.py:9-58`）。这与 Heyup 已存在的新闻、评测、品牌、趋势和专题频道冲突，也无法覆盖 DTC 的 How-to、产品教育、支持内容等动作。

### 2. 默认美国英语、Heyup 语气和 Affiliate

Grounding Prompt 固定“US English tech commerce newsroom”并优先 comparison/buying-guide intent（`heyup_buying_guides/discovery/search_grounding.py:20-27`）；seed Prompt 再次固定美国、英语和 commercial investigation（`heyup_buying_guides/seed_query_generator.py:728-743`）；生成层硬编码 Heyup 的 community-first voice（`heyup_buying_guides/llm.py:30-47`）。Prompt 模板又要求 disclosure 和 affiliate placeholder（`heyup_buying_guides/prompt_templates/buying_guide.txt:1-15`）。这些都必须迁移到 SEO Operating Mode、Brand SEO Profile 和具体内容类型规则中。

### 3. 已知关键词或硬编码查询等同于“发现”

`raw_keyword` 是 seed 流程入口；没有 raw keyword 时仍回退到三条耳机查询（`heyup_buying_guides/orchestrator.py:49-54`、`heyup_buying_guides/orchestrator.py:201-206`）。示例配置也内置耳机主题（`config/workflow.sample.json:10-35`）。该设计只能扩展已知需求，不能发现 Profile 边界内的新实体、异常增长或未知主题。

### 4. 主题合格后自动写新文章

`_pick_topic` 直接取分数最高的 ready topic，随后立刻生成 Brief 和文章（`heyup_buying_guides/orchestrator.py:52-71`、`heyup_buying_guides/orchestrator.py:361-363`）。它没有先判断是否已有页面、是否关键词蚕食，以及动作应是更新、合并、链接还是观察。这一控制流必须淘汰，而不是加一个 Opportunity 字段后继续原路径。

### 5. 至少三个产品、统一 Affiliate 披露和 Amazon 匹配是通用质量要求

默认 `min_products=3`、Amazon 开启、美国站点（`heyup_buying_guides/config.py:44-47`、`heyup_buying_guides/config.py:79-80`）；校验强制 disclosure、affiliate slot 和最少产品数（`heyup_buying_guides/stages/validate.py:12-17`）。这些只适用于部分商业文章。Amazon 匹配和 Affiliate URL 填充（`heyup_buying_guides/amazon_resolver.py:45-81`）不应进入共同底座。

### 6. CMS 写入属于 SEO 工作流

主编排器通过校验后直接调用 `publish_draft`（`heyup_buying_guides/orchestrator.py:116-124`），旧 publisher 可对 Shopify REST/GraphQL 发起创建（`heyup_buying_guides/shopify.py:23-108`、`heyup_buying_guides/shopify.py:111-220`）。新项目边界明确只提供 Shopify 所需字段，不执行发布（`docs/context/PROJECT_CONTEXT.md` 的“输出边界”）；这条路径必须隔离，不应作为兼容能力保留在默认运行中。

### 7. 年份和品类可以通过少量硬编码规则推断

seed 标题会把一组年份替换成当前年，并强制添加 Best/Top/Buying Guide 格式（`heyup_buying_guides/seed_query_generator.py:470-535`）；品类只靠关键词字典映射六类（`heyup_buying_guides/orchestrator.py:337-358`）。这会把标题格式当作意图，把跨品类/多语言判断压缩成英文 token 规则，不能成为通用模型。

## 已证实的失败模式

### 历史资产总体统计（事实）

对 `assets/legacy/heyup-runs/` 全量扫描得到：

| 指标 | 结果 |
| --- | ---: |
| 运行目录 | 72 |
| 文件 | 499（421 JSON、38 HTML、39 TXT、1 Markdown） |
| `run_report.json` | 33 |
| 历史 validation status | 30 passed、3 failed |
| 历史 Shopify status | 4 published、26 stubbed、3 skipped |
| `generated_article.json` | 38 |
| 含至少一个 `risk_flag` 的文章 | 26 |
| 无 `claim_references` 的文章 | 23 |
| 无 `source_manifest` 的文章 | 12 |
| `article_brief.json` | 40 |
| Brief 中产品总数 | 124 |
| 缺 specs / pros / cons | 62 / 57 / 57 |
| 零产品 Brief | 12 |

这些目录集中在 2026-03-11 至 2026-03-17 的历史报告时间范围，且显然混合了 stub、测试式运行和少量真实 CMS 尝试。统计是迁移快照事实，不是质量认证。

### 1. 历史 `passed` 与证据充分性脱钩

`assets/legacy/heyup-runs/0ffa6fe03647/run_report.json` 标记 `passed`，但候选数和选中数均为 0；同目录 `generated_article.json` 的 products、source manifest 和 claim references 都为空。另有多份 `passed` 文章缺 claim references 或 source manifest。解释：校验规则曾随代码演进，历史状态不能跨版本比较；新系统必须保存 validator/scoring 版本，并建立可重放的质量评估。

### 2. 品牌首页被当成产品证据并抬高置信度

当前 resolver 在命中品牌注册表时会把品牌官网填为 `brand_origin_url`；只要存在该 URL，就把 `source_confidence` 至少提高到 0.8 并标为 `ready`（`heyup_buying_guides/origin_resolver.py:23-59`）。`enrich_candidates` 还会仅因存在 origin/source URL 增加 confidence（`heyup_buying_guides/stages/enrich.py:8-28`）。

历史样本 `assets/legacy/heyup-runs/5ed730da1bdf/article_brief.json` 中，ASUS ROG Phone 10 Pro、RedMagic 11S Pro、Samsung Galaxy S26 Ultra、Sony Xperia 1 VIII 只有品牌首页，没有 specs/pros/cons，却可达到 0.8 source confidence 或 0.95 confidence。解释：URL 存在性被误当成产品和声明已验证；未来应把“实体归属”“产品存在”“页面为具体产品页”“claim 被来源支持”分成四种证据状态。

### 3. 伪证据可由泛化文案和 URL 自动生成

当没有 pros/cons 时，`bind_candidate_evidence` 会把 positioning 包装成 `source_summary`，再把 origin/reference URL 字符串作为 evidence（`heyup_buying_guides/evidence_extractor.py:8-44`）。上述 gaming phone 样本的 evidence 文本只是“某产品与当前购买意图相关”和“Primary source URL: 品牌首页”。解释：现有 evidence ID 证明了“记录存在”，没有证明“声明被来源支持”。新契约必须保存 claim、原文片段/结构化事实、精确来源、抽取方式和校验状态。

### 4. 泛页面抽取会把导航和站点文案识别为产品

早期/回退抽取使用正则识别大写词组（`heyup_buying_guides/stages/extract.py:13-25`、`heyup_buying_guides/stages/extract.py:75-95`）。历史 `assets/legacy/heyup-runs/5ed730da1bdf/article_brief.json` 中出现了 `Expert Reviews`、`Simplify Your Shopping Categories Online`、`Shopping Blog Today`、`Deals Categories Online Shopping Blog` 和 `Deals America` 等伪产品。当前代码已经增加首页跳过、generic pattern 与 LLM judge（`heyup_buying_guides/stages/extract.py:98-127`、`heyup_buying_guides/intelligence.py:34-110`），说明这一失败模式已被部分修补，但历史样本应留作新实体抽取器的负例回归集。

### 5. 主题和信号分数是粗代理，不是可审计的 SEO 需求事实

当前 `search_discovery_score` 只要存在 source URL 就是 0.9，否则 0.4；content fit 对两种既定商业格式给高分（`heyup_buying_guides/topic_ranker.py:20-39`、`heyup_buying_guides/topic_ranker.py:103-121`）。Google Trends 用标题 token overlap 评分（`heyup_buying_guides/discovery/google_trends.py:22-32`），Reddit 只取帖子 score + comments 的最大值再除以 500（`heyup_buying_guides/orchestrator.py:366-372`）。解释：这些分数可以作为原型启发式，但不能冒充搜索量、趋势强度、相关性或业务价值；每个维度需要原始观测、计算版本、缺失状态和解释。

### 6. 重复主题在生成后才被提示，未被防止

30 份 `topic_candidate.json` 中，`best-laptops` 出现 12 次，`best-wireless-headphones-2026` 出现 7 次，`best-noise-cancelling-headphones` 出现 5 次。38 篇文章中有 21 篇带 `duplicate_topic_risk`。代码虽然配置了 `duplicate_topic_window_days` 和 `discovery_frequency_hours`（`heyup_buying_guides/config.py:66-78`），但除加载外没有执行逻辑；重复检查仅在文章生成后查询同 `topic_key` 最近五次并加 flag（`heyup_buying_guides/orchestrator.py:97-102`、`heyup_buying_guides/storage.py:111-122`）。解释：新系统需要先做站内 content inventory 与覆盖匹配，重复不是文章级警告，而是 Opportunity action 判定的一部分。

### 7. Apify 相关查询路径有真实不稳定记录

历史有两个 `apify_run_failure.json`：`assets/legacy/heyup-runs/dfe72a875194/apify_run_failure.json` 是 120 秒 timeout；`assets/legacy/heyup-runs/5ed730da1bdf/apify_run_failure.json` 是 actor 请求 0 succeeded/1 failed、空 dataset。当前代码有 polling、terminal status 和 fallback/阻塞开关（`heyup_buying_guides/seed_query_generator.py:128-180`、`heyup_buying_guides/seed_query_generator.py:185-277`）。解释：适配器必须把失败、空结果和 freshness 当数据状态持久化，Opportunity 不能把“无数据”解释成“无需求”。

### 8. Schema 演进和运行语义不稳定

历史 Brief 同时出现 `buying guide` 与代码要求的 `buying_guide`；部分历史 reports 缺少后来新增的 topic/quality 字段；产物集合随运行年代变化。当前 `RunReport` 已包含 topic scores、quality、blocking reasons 等（`heyup_buying_guides/schemas.py:132-152`），但没有 schema version。解释：后端所有生命周期对象都需要 schema version、producer/version、created_at 和 immutable score/decision snapshot，避免原地覆盖后失去解释能力。

### 9. 测试验证的是结构与控制流，不是外部事实质量

fixture 中的 source 文本和 topic score 是人工构造（`tests/fixtures/audio_comparison/source_documents.json:1-33`、`tests/fixtures/audio_comparison/topic_candidates.json:1-190`）；端到端测试断言产物存在、状态通过和 stub publish 成功（`tests/test_workflow.py:55-97`）。它们很好地保护了程序结构，但不会证明实际产品存在、来源新鲜、搜索需求真实或文章可发布。新测试体系需要保留这些单元/契约测试，并额外建立真实但脱敏的黄金样本与人工评审基准。

## 新工作模型目前缺失的能力

以下能力在旧实现中没有可直接继承的完整对象或闭环，应该进入后续 Wayfinder 节点，而不是在本节点提前定解：

1. **项目与 Profile 隔离**：Brand SEO Profile、Listening Profile、Heyup/DTC operating mode、市场、语言和权限边界。
2. **统一信号契约**：原始观测、标准化 Signal、去重/聚类、实体与主题关系、来源可信度、时效、采集失败和血缘。
3. **小型 SEO 信号收集器**：外部搜索/趋势/新闻/社区的渐进适配，以及未来 Marketing Listening 替换契约。
4. **DTC 第一方 VOC**：项目隔离、脱敏、标准化的只读 BigQuery View；评论和工单不能与 Reddit 等外部社区信号混类。
5. **站内 Content Inventory**：URL、canonical、目标 query/topic、内容类型、版本、市场/语言、内部链接和历史表现，支持覆盖/蚕食判断。
6. **SEO Opportunity**：准入门槛、评分快照、证据解释、人工覆盖和 action recommendation；维度与标准仍待讨论。
7. **非新建动作**：Update、Expand、Merge、Link、Reposition、Monitor、Reject 及其状态机。
8. **后端生命周期数据层**：Operational DB 保存实体、状态、版本和决策；Warehouse 保存 BQ VOC、GSC/GA4 周期明细和分析聚合。
9. **CMS handoff 与 Publication Record**：只交付，不执行发布；接收外部 CMS ID、URL、版本、状态和发布时间。
10. **GSC + GA4 闭环**：query/page 可见性与 organic landing/content/business performance 联合分析；形成 refresh/merge/retire 等新机会。
11. **人工治理**：资格门槛、证据不足、敏感 VOC、事实校验和发布前 QA 的明确责任人及审计记录。
12. **多内容类型与 Heyup 业务上下文**：News、Review、Trend、Brand、Program、Tryout 等类型，以及社区/产品生命周期信号。

## 对后续 Wayfinder 的约束与建议

### 应作为硬约束写入后续节点

- 不把 `TopicCandidate` 直接改名为 `SEO Opportunity`；两者的决策语义不同。
- 不把旧 `draftability_score` 当第一版评分基线；最多作为待校准的一个旧启发式样本。
- 不用“存在官网 URL”作为产品/claim 证据；证据必须可回到具体页面和事实。
- 不以历史 `passed` 作为金标；先按 schema generation 分层并人工挑选样本。
- 不在 SEO MVP 内恢复 Shopify 写入；只设计 handoff 与 publication 回传。
- 不让本地 artifacts 替代后端数据库；artifacts 只用于调试和导出。

### 建议优先抽取的旧资产

1. 把 Google Trends、Reddit、Serper、Grounding 的输入/输出包装成 connector contract fixture。
2. 把完整的 audio fixture 作为“结构正确”样本，而不是“事实正确”样本。
3. 把 `5ed730da1bdf` 的伪产品、品牌首页伪证据，以及 `0ffa6fe03647` 的零产品 passed 作为负例。
4. 把两个 Apify failure 作为采集失败/空数据语义样本。
5. 把 `7e2c766abdb5`、`cff1c5f0480d`、`cd50762dd358` 的证据 ID 校验失败作为 evidence lineage 负例。

## 最终判定矩阵

| 分类 | 判定 |
| --- | --- |
| 可直接复用 | 运行级 artifacts、connector 隔离、LLM JSON/schema + stub、品牌归一化、结构化校验骨架、fixture 测试方法 |
| 抽象后复用 | Signal 雏形、候选标准化、证据绑定目标、评分思想、Brief/Article 字段、SQLite 状态意识、CMS 字段映射 |
| 必须淘汰 | Heyup/US/English 固定 Prompt、只有两种文章、已知词驱动即发现、自动 Topic→文章、统一 Affiliate/Amazon 规则、Shopify 写入、品牌首页即证据、硬编码年份/品类 |
| 已证实失败 | passed 与证据质量脱钩、缺 specs/pros/cons、伪产品、伪证据、重复选题、粗代理评分、Apify timeout/空集、schema 演进无版本 |
| 新模型缺失 | Profile/模式、统一 Observation/Signal/Cluster、VOC、Content Inventory、Opportunity/Action、Operational DB + Warehouse、CMS 回传、GSC/GA4 闭环、治理审计 |

## 结论

旧项目不是应该继续扩建的“半成品平台”，而是一条已经暴露关键问题的 Heyup Buying Guide 参考流水线。它的工程可复现性比其业务模型更有价值：我们应复用隔离、结构化、校验、fixture 和运行留痕；重新设计信号、机会、动作、证据和生命周期数据模型；把历史资产转化为正负样本，而不是继承为公司级事实。
