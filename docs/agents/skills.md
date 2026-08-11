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
- `domain-modeling`：定义统一领域语言，维护 glossary 与 ADR。
- `research`：为待决策问题调查外部或本地事实。
- `to-spec`：把已经讨论清楚的方案整理成规格 Issue，不再访谈。
- `to-tickets`：把规格拆成带依赖关系的纵向任务 Issue。
- `implement`：按已确认规格或任务实施。
- `tdd`：以测试驱动方式实现行为。
- `code-review`：审查已经完成的代码改动。
- `diagnosing-bugs`：诊断缺陷并形成可验证解释。
- `triage`：整理进入 GitHub Issues 的请求。

## 推荐工作流

当目标只有方向、尚无清晰框架时：

```text
grill-with-docs
  -> to-spec
  -> to-tickets
  -> implement（按需结合 tdd）
  -> code-review
```

- 事实缺口在任一决策阶段交给 `research`。
- 已有清晰计划、只想接受压力测试时使用 `grill-me`。
- Bug 从 `diagnosing-bugs` 开始，不直接跳到实现。
- `triage` 面向新增 Issue，不替代产品或 SEO 战略讨论。

SEO 专用 skills（例如关键词研究、市场研究）负责领域工作；Matt skills 负责澄清、记录、拆解和执行，两者可以组合，但职责不能混淆。

## Setup skill

`setup-matt-pocock-skills` 不作为日常 skill 安装。它的一次性输出已经由本仓库的 `AGENTS.md`、`docs/agents/issue-tracker.md`、`docs/agents/triage-labels.md` 和 `docs/agents/domain.md` 承担。

## 更新

更新前先查看上游变更，再在仓库根目录运行：

```sh
npx skills update -p
```

升级上游版本时应单独提交 `skills-lock.json` 与 skill 内容变化，便于审查行为差异。
