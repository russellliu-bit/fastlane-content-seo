# Migration Manifest

## 迁移信息

- 迁移日期：2026-08-11
- 旧对话工作区：`/Users/russell/Desktop/heyup_affiliate`，迁移时已不存在。
- 实际旧项目：`/Users/russell/Desktop/03_heyup_ops/affiliate`
- 新项目：`/Users/russell/Desktop/04_product/Ai_colab/fastlane-content-seo`
- 新项目策略：干净仓库，不继承旧 `.git`。

## 已迁移内容

- 当前工作区版本的 Python 工作流代码，包括未提交的 `seed_query_generator.py`。
- 当前配置、测试和 fixtures。
- Heyup Codex 知识库 15 个文件。
- 历史运行资产 499 个文件：421 JSON、38 HTML、39 TXT、1 Markdown。
- `brand_official_websites.csv` 与 `.env.example`。
- Ai_colab 原有两份 Fastlane 2026 H2 AI 共创项目申报文档。

## 旧仓库状态快照

- 分支：`codex/discovery_modify`
- 基线提交：`b26466f Before Modifying Discovery`
- Git Remote：无。
- 迁移时已修改：`config/workflow.sample.json`、`heyup_buying_guides/cli.py`、`heyup_buying_guides/config.py`、`heyup_buying_guides/orchestrator.py`、`tests/test_workflow.py`。
- 迁移时未跟踪：`heyup_buying_guides/seed_query_generator.py`。

以上修改以工作区当前内容迁移，未回退到旧提交。

## 明确排除

- 旧 `.git/` 历史与索引。
- `.env` 和所有真实凭据。
- `.DS_Store`、`__pycache__`、`.pyc`。
- `artifacts/cache/`。
- `artifacts/state.db` 与 `artifacts/test_state.db`。

## 目录映射

```text
旧 codex_knowledge_base/ -> 新 codex_knowledge_base/
旧 heyup_buying_guides/ -> 新 heyup_buying_guides/
旧 tests/               -> 新 tests/
旧 artifacts/           -> 新 assets/legacy/heyup-runs/
Ai_colab/*.md            -> 新 docs/context/source/
```

## 完整性原则

- 旧项目未被删除或修改。
- 历史运行资产作为迁移快照保留，新运行不得写入该目录。它们仅在迁移机器本地保留，不纳入新的 GitHub 仓库。
- 新运行继续使用根目录 `artifacts/`，该目录由 Git 忽略。
- 此清单记录迁移事实，不代表历史输出已经通过质量审核。

## GitHub 基线整理（2026-08-11）

- 新仓库只包含可运行代码、测试、示例配置、项目文档、品牌注册表和 Heyup 知识库。
- `assets/legacy/heyup-runs/` 与 `scripts/legacy/` 作为本地迁移资料保留并由 `.gitignore` 排除。
- 根目录的旧 Shopify 手工脚本已归档至 `scripts/legacy/create_blog_副本.py`；它不属于项目运行范围，也不会被提交。
