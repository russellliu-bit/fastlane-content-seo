# DTC 第一方 VOC 的 BigQuery 只读消费契约

- 日期：2026-08-12
- Wayfinder 节点：定义 DTC 第一方 VOC 的标准 BigQuery View
- 结论性质：只读消费契约与架构边界；不是 BigQuery 建表、建 View 或存储改造方案
- 数据安全：研究过程没有查询评论、工单或用户明细，没有复制真实正文或 PII

## 结论

SEO MVP 不修改现有 BigQuery schema、View、表、权限模型、存储和上游数据管道。它只通过受控、参数化、显式字段的查询读取当前项目和时间窗口所需的数据。

Issue 标题中的“标准 BigQuery View”在本项目内解释为**稳定的逻辑读取契约**，不是要求数据中台创建物理或逻辑 BigQuery View。消费端分为两个 source adapter：

1. `ProductReviewAdapter`：读取第一方站内产品评论；
2. `SupportMessageAdapter`：读取客户发送的客服消息，ticket 只补充上下文；
3. 两个 adapter 都输出统一的 `First-party VOC Observation`；
4. 采集运行和来源健康状态写入 SEO Operational DB，不写回 BigQuery。

当前后端默认方向为 Supabase/PostgreSQL，使用 Drizzle 定义 SEO 自有表、关系和 migration。这个节点只确定数据所有权与交换边界，不提前锁定最终 Supabase 表数量、列名或部署结构。

```text
现有 BigQuery 表（只读、不改）
  → 项目绑定、时间有界、显式列的参数化查询
  → ProductReviewAdapter / SupportMessageAdapter
  → 内存中清洗、标准化、PII 去标识、质量检查
  → Supabase/PostgreSQL（仅写入 SEO 所需的安全工作数据）
  → Signal → SEO Opportunity → 内容与表现生命周期
```

## 已验证的本地事实

### 存量第一方 VOC 与规划中的统一 VOC 表不是同一状态

Day 的数据蓝图记录了一次 2026-07-01 的生产 BigQuery 检查：客服工单 `dwm_cuservice_ticket_*` 与站内评价 `dwm_user_product_reviews_dtl` 已存在；规划中的统一 `dwm_user_voc_feedback_event` 以及社媒 VOC 当时尚未进入生产（`/Users/russell/Desktop/04_product/DTC+/day/03_数据/DATA-BLUEPRINT-voc-vs-listening.md:6-10`；`/Users/russell/Desktop/02_agent_dev/day-pipeline/docs/[2026-06-12] - [数据收集] - VOC舆情数据v0.2.0.md:1271-1294`）。

因此 SEO MVP 不能依赖未来统一表，也不能把 2026-07 的说明当成当前线上事实。实际 adapter 必须在获得只读权限后核验正式表名、字段、覆盖期和更新时间。

### REDMAGIC 配置了多套第一方来源

中台 dbt 配置显示：

- REDMAGIC Judge 评论源覆盖 `br`、`ca`、`eu`、`global`、`na`、`sa`、`mx`、`sg`、`uae`、`uk` 等 shop（`/Users/russell/Desktop/04_product/DTC+/ml-dev/_ref/mid-platform/data-cleaner-py/transfer/dbt_project.yml:233-251`）；
- REDMAGIC 同时配置了 Gorgias 与 Zendesk（同文件 `:332-366`）；
- source YAML 中存在 `ods_gorgias_redmagic` 的 `messages`、`tickets`，以及 `ods_zendesk_redmagic` 的 `ticket_comments`、`tickets` 声明。

这不能证明这些来源当前都在生产稳定刷新，也不能证明 Gorgias 与 Zendesk 没有迁移重叠。adapter 必须保留 `source_system`，并通过只读聚合查询验证覆盖期；不能按文本相似度擅自跨系统合并。

`na`、`global` 等 shop scope 也不能直接解释为美国英语市场。`shop/source scope → market/language` 必须来自受控配置；无法确认时记录为 unknown，不进入 REDMAGIC US/en 验证切片。

### 上游包含 SEO 不应持久化的敏感数据

现有 Judge/Fera 模型除评论正文外还包含邮箱、姓名、电话、IP、订单或用户 ID。Gorgias/Zendesk 模型包含 sender/requester、headers、附件、正文、外部 ID 等高敏上下文。

SEO 查询必须只选择业务需要的显式列，禁止 `SELECT *`。但仅不选择结构化 PII 仍不够，因为正文中可能出现姓名、邮箱、电话、地址、订单或物流号。因此未经文本级 PII 检测和去标识的正文不得写入 Supabase、日志、GitHub fixture、Opportunity evidence 或 LLM 请求。

### `project_id` 与 `brand_code` 是两套身份

中台使用如 `redmagic` 的项目 slug；DTC+ Service 使用 `BRD…` 形式的品牌主数据编码（`/Users/russell/Desktop/04_product/DTC+/ml-dev/dtcplus-service-ts/CONTEXT.md:7-13`）。没有证据证明两者天然一一对应。

SEO 项目配置必须显式维护 `project_id → brand_code`。映射不存在、过期或冲突时采集 fail closed，不能按品牌名称、大小写或域名猜测。

### 当前无法证明生产 freshness 和质量

本地 Dagster 配置显示 data-cleaner job 计划每日运行多次，但不能证明生产调度已启用、目标 VOC model 均被包含或上游同步成功。本机 `bq` CLI 当前没有 active account，因此本研究没有核对线上 schema、partition、最近写入、180 天覆盖和真实数据质量。

## 逻辑消费契约

### Product Review

粒度是一条第一方站内产品评论。

允许读取并标准化：

- 项目和非 PII 来源 scope；
- source system 与不含客户身份的 source record ref；
- 评论发生/更新时间；
- 产品引用与受控产品映射；
- 评分、量表和来源明确提供的 verified purchase 状态；
- 标题和正文，仅用于采集进程内去标识；
- published、hidden、spam 等状态，但是否可用于内部分析需由数据 owner 确认。

不持久化：姓名、邮箱、电话、IP、customer/user/order ID、原始媒体 URL、附件和未经处理的正文。

### Support Message

粒度是一条**客户发送的** message/comment，不是一张 ticket。

- agent、bot、private internal note 不构成第一方 VOC Observation；
- ticket 只补充 channel、status、priority、language、opened/closed 等上下文；
- opening description 与首条 message 可能重复，必须按 source-specific 规则去重；
- 若来源只有 ticket description，可作为明确标记的 fallback，但必须证明不是首条消息副本；
- headers、附件、recipient/requester/assignee/sender 标识和联系信息不得持久化。

### First-party VOC Observation

两个 adapter 的统一输出是一条完成项目归属、标准化、去标识和质量检查的反馈证据。建议的逻辑字段组如下；它们是 TypeScript/数据库边界契约，不是 BigQuery DDL：

| 字段组 | 最低语义 |
| --- | --- |
| 身份 | 稳定且不可反推客户身份的 `observation_id`、`revision`、内容 fingerprint |
| 项目 | `project_id`、`brand_code`、映射版本 |
| 来源 | `source_kind`、`source_system`、非 PII source scope/ref、parent ref |
| 时间 | event、source update、collection、standardization 时间 |
| 市场 | market、country、language 及其映射来源 |
| 产品 | canonical 产品引用、映射状态和版本 |
| 内容 | 只包含去标识后的 title/text |
| 评论 | rating、scale、verified purchase；不适用时为 NULL |
| 客服 | channel、ticket status/priority；不适用时为 NULL |
| 治理 | PII scan、record/quality status、quality codes |
| 血缘 | collection run、contract version、source query version |

taxonomy、主题、使用场景、购买阶段、意图、情绪和严重度是版本化 LLM/规则标注，不是源事实。它们应与 Observation 分开保存，并记录模型、prompt、taxonomy 和时间；空值表示尚未标注，不能解释成“没有该主题”。

## BigQuery 只读边界

### 查询约束

每次采集必须满足：

1. 查询使用显式列清单，禁止 `SELECT *`；
2. `project_id` 来自受控项目配置，不接受 LLM 或普通用户任意输入；
3. 必须有有界时间窗口、partition 条件或其他等价扫描边界；
4. 使用参数化查询，记录 query/adapter version、窗口、项目、来源、行数和扫描量；
5. 先做 metadata 与 aggregate-only smoke，再在受控环境验证少量明细的清洗效果；
6. 不执行 DDL、DML、建 View、建表、export raw dump 或写回 BigQuery；
7. 不把 BigQuery 原始响应缓存为本地文件或提交 Git。

### 项目隔离

由于本次不创建项目专属 Authorized View，MVP 的项目隔离是**消费应用层隔离**，不能描述成仓库层强隔离：

- 每个 collection run 绑定一个已注册 Project；
- 查询固定使用该 Project 的 `project_id`；
- adapter 输出后、写入 Supabase 前再次校验所有行的项目归属；
- 查询返回意外项目值时整批 fail closed，并记录安全事件；
- 服务身份仍应遵守现有 BigQuery 最小只读权限，但本项目不修改 IAM；
- 如果未来要求仓库层强隔离，需要另行与数据平台决策 Authorized View/RLS，不属于本 MVP。

### PII 处理

```text
BQ selected text
  → 采集进程短暂内存
  → 去 HTML、签名、quoted history 和模板噪音
  → PII 检测与替换
  → 二次扫描与质量 gate
  → 仅将 redacted text 写入 Supabase
```

只有 `pii_scan_status = passed | redacted` 的内容可以持久化、进入 LLM 或人工审核。`not_scanned`、`blocked` 和清洗失败的记录只记计数与失败状态，不保留正文。

原始正文的事实来源仍是 BigQuery。Supabase 中的去标识内容是 SEO 工作副本，必须保留 `observation_id + revision + fingerprint + contract_version`，并遵循来源删除和保留政策。

## Supabase 与 Drizzle 的边界

当前预期使用 Supabase/PostgreSQL 作为 SEO Operational DB，Drizzle 管理该数据库的 schema 与 migration。Drizzle 不映射、迁移或管理 BigQuery 原始表。

Operational DB 负责：

- 项目配置与 `project_id → brand_code` 映射引用；
- source connection 的非密钥配置；
- collection run、窗口、状态、计数、错误和 freshness；
- 完成去标识的 VOC Observation 与版本化 annotation；
- Signal、cluster、SEO Opportunity、评分、LLM 初审和人工终审；
- 内容资产、发布记录和 GSC/GA4 表现快照；
- Opportunity 使用的 Observation revision 引用和政策允许的最小证据片段。

Operational DB 不负责：

- 保存 180 天完整原始评论/工单镜像；
- 保存原始 PII、附件、headers 或未经扫描的正文；
- 代替 BigQuery 成为第一方 VOC 的原始事实仓库；
- 让 Drizzle 对 BigQuery 执行 migration；
- 在当前 Issue 中锁定最终表数量、索引和物理部署。

第一版可能涉及 `projects`、`source_connections`、`collection_runs`、`voc_observations`、`voc_annotations`、`signals`、`signal_evidence`、`opportunities` 等概念表，但它们应在后续原型和规格阶段确定，而不是由本研究直接当成实施 schema。

## 来源健康与就绪标准

来源健康不需要 BigQuery View，直接作为 `collection_runs` 及其质量统计写入 Operational DB。最低状态应区分：

- `not_configured` / `access_pending`；
- `running`；
- `succeeded_with_data` / `succeeded_empty`；
- `partial`；
- `auth_failed` / `upstream_error` / `schema_error`；
- `quality_blocked` / `stale`。

`succeeded_empty` 仅表示查询成功且窗口内确实无新增；权限失败、字段变化和过期数据不得伪装为空。

建议的 SEO 消费 SLA 是每日更新，目标 lag 不超过 24 小时，36 小时 warning，48 小时 stale；首次验证回填共同完整日期之前的近 180 天。这是待真实验证的 MVP 目标，不是对现有数据管道的事实声明。

在 REDMAGIC VOC 标为 ready 前，至少完成：

1. 只读 metadata 核验正式表名、字段、类型、location、partition 和最近写入；
2. aggregate-only 查询核验近 180 天按来源/shop/day 的覆盖、最大时间、NULL 和重复比例；
3. 确认 `redmagic → BRD…` 的正式映射、owner 和失败处理；
4. 确认 shop scope 到 US/en 的映射依据；
5. 确认 Gorgias/Zendesk 的覆盖和重叠边界、客户/客服消息识别规则；
6. 确认 Judge/Fera 的 published/hidden/spam/verified 语义和允许内部使用的范围；
7. 用合成 fixture 和受控抽样验证 PII 清洗，不把真实样本带入仓库；
8. 连续完成至少两个刷新周期，并验证成功、空、schema error 与 stale 状态；
9. 验证查询只读、有界、项目过滤有效，异常项目值会 fail closed；
10. 记录查询成本、扫描量、删除传播和回看窗口。

## 已确认、待验证与明确不做

### 已确认

- 第一方 VOC 来源是产品评论和客服客户消息；客服 ticket 只是上下文。
- BigQuery 是现有第一方数据来源，本 SEO MVP 对其只读，不改 schema、View 或存储。
- 标准化、正文去标识、质量 gate 和统一 Observation 在 SEO 采集应用完成。
- 去标识后的工作数据及 Signal/Opportunity 生命周期进入 SEO Operational DB。
- Supabase + Drizzle 是当前默认后端方向，最终物理 schema 留给后续原型和规格。

### 待真实只读验证

- 当前线上正式表名、schema、partition、更新时间和 180 天覆盖；
- REDMAGIC 的正式 `brand_code`、shop/market/language 映射；
- Gorgias/Zendesk 与 Judge/Fera 的真实覆盖、状态语义和重复边界；
- 可供 SEO/LLM 使用的正文范围、保留期与 PII 方案；
- 当前只读身份的可见项目范围、查询成本和生产 freshness。

### 明确不做

- 不创建或修改 BigQuery 表、View、dataset、RLS、policy tag、IAM 或存储策略；
- 不建立完整 VOC/Marketing Listening 数据管道；
- 不把 BQ 原始表镜像到 Supabase；
- 不在本节点设计最终 Drizzle schema、taxonomy、prompt 或 Opportunity 评分；
- 不读取或提交真实 PII 样本。

## 决议

1. BigQuery 对 SEO MVP 是只读来源，不做 schema、View、存储和上游管道改造。
2. 产品评论与客服客户消息分别通过 adapter 读取，在应用层统一为 First-party VOC Observation；ticket 只提供上下文。
3. 所有查询必须显式字段、项目绑定、时间有界、参数化，并记录 collection run；异常项目数据整批 fail closed。
4. 原始正文只在采集进程中短暂存在；完成 PII 去标识和质量 gate 后，才允许写入后端、发送 LLM 或人工查看。
5. BigQuery 保持原始事实来源；SEO Operational DB 保存去标识 Observation、采集健康、Signal、Opportunity、内容与表现生命周期。
6. Supabase/PostgreSQL + Drizzle 是当前默认后端方向；Drizzle 只管理 SEO 自有数据库，不管理 BigQuery。
7. 在来源标为 ready 前，必须完成真实只读 metadata、aggregate quality、映射、PII、刷新和项目过滤 smoke。

## 本报告不包含

- 真实 BigQuery 行数据、评论/工单正文、PII 或凭据；
- 生产 SQL、BQ schema/View/IAM 变更；
- 最终 Supabase/Drizzle schema；
- VOC taxonomy、Signal 聚类、Opportunity 评分或内容生成流程。
