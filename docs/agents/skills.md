# Agent Skills

Skills 随仓库提交，克隆项目后即可获得一致的 Agent 工作流，不依赖某台电脑的全局安装。

## 目录

`.agents/skills/<name>/SKILL.md` 是唯一事实来源，供 Codex 等支持共享 skills 目录的 Agent 使用。

Claude Code 使用 `.claude/skills/<name>` 中指向 `.agents/skills/<name>` 的软链接，不维护第二份副本。

`skills-lock.json` 固定每个 skill 的来源、Git ref 与内容哈希。

## 已安装的 Matt skills

以下 skills 固定自 `mattpocock/skills` 的 `v1.1.0`：

- `grilling`：一次一个问题，持续澄清计划或设计。
- `grill-me`：只进行深度访谈，不写文档。
- `grill-with-docs`：访谈过程中同步维护领域词汇和必要 ADR。
- `wayfinder`：当目标大、路径不清晰时，建立探索地图并编排研究、原型和决策任务。
- `prototype`：用最小可运行实验验证高风险假设，不直接承诺生产实现。
- `domain-modeling`：定义统一领域语言，维护 glossary 与 ADR。
- `research`：为待决策问题调查外部或本地事实。
- `to-spec`：把已经讨论清楚的方案整理成规格 Issue，不再访谈。
- `to-tickets`：把规格拆成带依赖关系的纵向任务 Issue。
- `implement`：按已确认规格或任务实施。
- `tdd`：以测试驱动方式实现行为。
- `code-review`：审查已经完成的代码改动。
- `diagnosing-bugs`：诊断缺陷并形成可验证解释。
- `triage`：整理进入 GitHub Issues 的请求。
- `handoff`：在暂停、换人或换 Agent 时，留下可继续执行的结构化交接。

## 已安装的 SEO skills

以下 skills 固定自 `aaron-he-zhu/seo-geo-claude-skills` 的独立版 `v9.9.12`：

- `keyword-research`：按搜索意图、价值和可行性研究并组织关键词。
- `competitor-analysis`：分析搜索竞争对手、内容策略和可借鉴机会。
- `content-gap-analysis`：识别本站与竞争对手之间的主题和内容覆盖缺口。
- `technical-seo-checker`：检查抓取、索引、站点结构和页面技术 SEO 问题。

选择独立版是为了让每个 skill 及其引用资料都完整保存在仓库中，不依赖个人电脑上的外部 bundle。`programmatic-seo` 暂不安装；只有项目明确进入模板化批量页面阶段时才需要。原全局 `apify-market-research` 副本缺少其引用脚本，因此不纳入项目依赖。

## 推荐工作流

当目标较大、只有方向且需要同时探索多个未知领域时：

```text
wayfinder
  -> research / prototype / grill-with-docs / domain-modeling
  -> to-spec
  -> to-tickets
  -> implement（按需结合 tdd）
  -> code-review
```

- 单个方案已经成形、只需澄清时，可直接从 `grill-with-docs` 开始，不必建立 Wayfinder 地图。
- 事实缺口在任一决策阶段交给 `research`。
- 已有清晰计划、只想接受压力测试时使用 `grill-me`。
- Bug 从 `diagnosing-bugs` 开始，不直接跳到实现。
- `triage` 面向新增 Issue，不替代产品或 SEO 战略讨论。
- 关键词、竞争、内容缺口和技术审计分别调用对应 SEO skill；它们可以成为 Wayfinder 地图中的研究节点。
- 任务中断或需要跨会话继续时使用 `handoff`。

SEO 专用 skills 负责领域分析；Matt skills 负责探索、澄清、记录、拆解和执行，两者可以组合，但职责不能混淆。

## Setup skill

`setup-matt-pocock-skills` 不作为日常 skill 安装。它的一次性输出已经由本仓库的 `AGENTS.md`、`docs/agents/issue-tracker.md`、`docs/agents/triage-labels.md` 和 `docs/agents/domain.md` 承担。

## 更新

更新前先查看上游变更。Matt skills 可在仓库根目录运行：

```sh
npx skills update -p
```

SEO skills 当前固定在上游独立版 tag，应通过 `skill-installer` 明确指定新 tag 后更新，并重新计算内容哈希。升级上游版本时应单独提交 `skills-lock.json` 与 skill 内容变化，便于审查行为差异。
