# Fastlane Content SEO

Fastlane 面向科技与消费品牌的博客选题、SEO 研究和内容生产工作区。

项目从 Heyup Affiliate Buying Guides 工作流迁移而来，保留已验证的热点发现、种子词生成、候选选题评分、文章 brief、内容生成和 SEO 输出能力，并将范围扩大到 Fastlane 服务的多个品牌。

## 当前范围

- 覆盖品牌：Heyup、REDMAGIC、Hypershell、Nothing、Airseekers、Anta，以及后续新增客户。
- 主要产出：博客选题、搜索意图、关键词与主题集群、SEO 标题、Meta Description、URL Handle、标签、摘要、文章结构、正文和 Shopify 博客所需内容字段。
- 明确不做：Shopify 发布、后台写入、发布状态管理和上线操作。
- 内容方向：追随当下科技与消费电子热点，同时符合具体品牌定位和自然搜索机会。

## 上下文入口

1. `docs/context/PROJECT_CONTEXT.md`：项目范围、关键决策与工作边界。
2. `docs/context/MIGRATION_MANIFEST.md`：旧项目来源、迁移内容与排除项。
3. `codex_knowledge_base/00_index.md`：Heyup 原始业务与内容知识库。
4. `docs/context/source/`：Fastlane AI 共创项目原始申报资料。
5. `docs/agents/`：Agent skills、Issue tracker、triage 标签及领域文档维护规则。
6. 本地可选的 `assets/legacy/heyup-runs/`：迁移前已生成的选题、brief、文章和研究运行资产。该目录仅在迁移机器保留，不纳入 Git 仓库。

## 现有基建

- `heyup_buying_guides/`：原 Heyup 工作流代码。迁移阶段保留包名，避免破坏已验证行为。
- `config/workflow.sample.json`：示例工作流配置。
- `tests/`：现有离线测试与 fixtures。
- `brand_official_websites.csv`：品牌官网基础注册表。
- `.agents/skills/`：项目固定版本的探索、交付与 SEO 专用 Agent 能力。
- `skills-lock.json`：Agent skills 的来源与版本锁。
- `scripts/legacy/`：仅本地保留的旧 Shopify 手工脚本，不纳入 Git 仓库。

## 本地运行

```bash
python3 -m unittest discover -s tests
python3 -m heyup_buying_guides.cli discover --config config/workflow.sample.json
```

需要在线模型或第三方服务时，从 `.env.example` 创建本地 `.env`。任何密钥都不得提交到 Git。

## 状态

当前为可运行的迁移基线。历史运行快照和旧手工 Shopify 脚本不随仓库分发；下一阶段应先完成多品牌领域模型与统一内容输出 Schema，再重构旧的 Heyup 专用命名和 Shopify 发布代码。
