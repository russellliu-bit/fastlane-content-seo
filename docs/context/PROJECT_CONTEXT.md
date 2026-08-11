# Project Context

## 1. 项目目标

构建 Fastlane 公司级的博客 SEO 与内容工作流，为 DTC 出海科技及消费品牌持续发现值得发布的话题，并生成从选题到成稿所需的 SEO 和内容字段。

首批覆盖：

- Heyup
- REDMAGIC
- Hypershell
- Nothing
- Airseekers
- Anta

品牌知识库尚未全部补齐。Heyup 已有较完整本地知识库；其他品牌应先建立带来源的基础上下文，再逐步替换为内部资料确认后的版本。

## 2. 从 Heyup 阶段继承的目标

原项目聚焦 Heyup 长尾词文章，主要内容类型为 Buying Guide 和 Comparison Roundup。选题需要跟随当下科技与消费电子热点，同时满足 Heyup 的内容定位和 SEO 价值。

已形成的核心流程：

```text
市场与趋势信号
  -> 种子主题发现
  -> searchTerms 生成
  -> 相关查询与品牌/产品切口扩展
  -> 候选选题标准化和评分
  -> 文章 brief
  -> 正文与 SEO 字段
```

## 3. 关键讨论与决策

### 种子词不能预先固定

项目没有稳定的 `searchTerms` 或种子词池。把 `ai glasses` 直接写进市场研究输入只能验证该主题，不能回答“现在最适合 Heyup 或某品牌写什么”。

因此必须把种子发现独立为上游阶段：先从科技新闻、产品发布、搜索趋势、社区讨论和品牌相关市场信号中发现主题，再把合格主题传给市场研究和关键词扩展工具。

### Apify Market Research 的角色

Apify Market Research 能力适合在已知主题后获取相关查询、品牌、产品和市场信号，例如从 `ai glasses` 扩展出购买、价格、定义、品牌和具体产品切口。它不是完整的无种子热点发现器。此前个人全局安装的同名 skill 缺少引用脚本，当前仓库不将它作为可复现依赖；后续应以完整实现或直接 API 集成恢复该能力。

### Skill 分工

- 热点/种子发现：负责从当前市场信号产生候选 seed topics。
- Apify Market Research 能力：验证并扩展已知 seed topic；当前仍待补齐可复现实现。
- `keyword-research`：处理关键词、意图、难度、搜索量和优先级。
- `programmatic-seo`：只在未来需要模板化批量页面或规模化内容时使用，不应替代选题判断。

### 输出边界

项目可以生成 Shopify 博客发布所需的 SEO 与内容字段，但不执行 Shopify 发布。旧代码中的 `shopify.py` 和发布模式属于迁移遗留能力，后续应隔离或移除，不能作为新范围默认行为。

## 4. 新范围的内容输出

每个最终选题至少应能形成以下结构化字段：

- 品牌与目标市场
- 内容类型
- Primary Keyword 与 Secondary Keywords
- Search Intent
- Topic Angle 与趋势依据
- SEO Title
- Meta Description
- URL Handle
- Excerpt
- Tags
- Suggested Headings
- Internal Link Suggestions
- Product/Brand Entities
- Evidence and Sources
- Full Article Content
- Research Timestamp 与 Freshness Notes

字段 Schema 尚待统一设计，目前不应直接沿用 Heyup 单品牌结构作为最终公司标准。

## 5. 本地资产地图

- `codex_knowledge_base/`：Heyup 业务、品牌、内容、产品和 Shopify 历史知识。
- `heyup_buying_guides/`：旧工作流实现，包含发现、评分、生成、渲染和发布遗留模块。
- `assets/legacy/heyup-runs/`：历史运行快照，可用于理解输入输出、失败模式和有效样例。
- `docs/context/source/`：Fastlane AI 共创项目申报原文。
- `brand_official_websites.csv`：旧品牌官网映射，可作为新品牌注册表的输入之一。

## 6. 当前待决策事项

- 公司级统一领域模型：Brand、Market、Topic、Keyword、Content Brief、Article、SEO Metadata、Evidence。
- 每个品牌的内容边界、目标市场、语气、竞争对手与禁区。
- 热点发现的数据源、刷新频率和证据门槛。
- 关键词指标的数据提供方与缺失数据处理规则。
- Buying Guide、Comparison、How-to、Explainer、News Analysis 等内容类型的统一模板。
- 新 GitHub 仓库归属、名称和团队权限。
