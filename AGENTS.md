# Fastlane Content SEO Agent Instructions

## 沟通

- 永远使用中文沟通。

## 项目上下文

- 开始工作前阅读 `docs/context/PROJECT_CONTEXT.md`。
- 涉及迁移边界或历史资产时，同时阅读 `docs/context/MIGRATION_MANIFEST.md`。
- 涉及 Heyup 业务、品牌或内容判断时，从 `codex_knowledge_base/00_index.md` 按需进入知识库。

## Agent skills

- 项目级 skills 位于 `.agents/skills/`，使用方式见 `docs/agents/skills.md`。
- Issue 与规格使用 GitHub Issues，操作约定见 `docs/agents/issue-tracker.md`。
- Triage 标签使用项目统一词汇，见 `docs/agents/triage-labels.md`。
- 领域术语和 ADR 的读取、维护规则见 `docs/agents/domain.md`。

## 项目边界与安全

- 项目负责博客选题、SEO 研究、内容及 Shopify 博客所需内容字段；不执行 Shopify 发布、后台写入或店铺运维。
- 品牌结论必须区分已验证事实、外部来源事实和待验证假设；热点与搜索需求使用前必须重新获取当前数据。
- `assets/legacy/heyup-runs/`、`scripts/legacy/` 和 `artifacts/` 仅在本地保留，不得提交。
- 不提交 `.env`、Token、Cookie、密钥、运行数据库、缓存或个人凭据。
- 重构 `heyup_buying_guides/` 前先通过现有测试，并记录兼容策略。
