# Issue Tracker: GitHub

本项目的规格与执行任务使用 `russellliu-bit/fastlane-content-seo` 的 GitHub Issues。

## 工具约定

- 优先使用 GitHub MCP 读取、创建和更新 Issue。
- 执行 GitHub MCP 搜索或写入前先确认当前认证账号。
- 当 skill 要求“publish to the issue tracker”时，创建 GitHub Issue。
- 当 skill 要求“fetch the relevant ticket”时，读取完整 Issue 正文、标签和评论。
- Pull Request 不是本项目的需求入口；除非用户明确要求，不把 PR 当作待 triage 请求。

## Issue 约定

- `to-spec` 创建一个规格 Issue，并添加 `ready-for-agent`。
- `to-tickets` 每个纵向切片创建一个独立 Issue，写清验收条件和阻塞项。
- GitHub 支持子 Issue 时，用原生子 Issue 表达父子关系。
- 当前 GitHub MCP 未暴露依赖关系写入时，在正文的 `## Blocked by` 中使用真实 Issue 链接。
- 评论用于补充过程信息；最终决策、验收结果或关闭原因必须明确写入 Issue。
- 关闭 Issue 时设置准确的 state reason。

## 安全

Issue 中不得粘贴 Token、Cookie、`.env` 内容、客户隐私资料、未脱敏日志或仅限本地的迁移资产。
