# 统一 Signal、Cluster 与 Evidence 低保真原型结论

- 日期：2026-08-12
- Wayfinder 节点：原型化统一 Signal、聚类与证据模型
- 原型性质：已完成并删除的 throwaway Python TUI；本文只保留问题、样本、观察结果与用户确认的答案
- 数据安全：全部使用贴近 REDMAGIC 与 Heyup 来源形态的合成数据，没有读取 BigQuery 明细、真实客户正文或 PII

## 原型要回答的问题

一个统一模型能否同时承载第一方 VOC、GSC、GA4、关键词、趋势、新闻和社区输入，并做到：

- 每个判断可追溯到来源及其 revision；
- 重复采集不造成重复计数；
- 来源更新不覆盖历史；
- 一条来源记录可以表达多个问题；
- 跨来源转载保留血缘但不冒充多源共识；
- 不同项目、运行模式、市场和语言不会误聚类；
- 在进入 SEO Opportunity 之前不提前引入统一评分。

## 被验证的模型

```text
Source Observation
  → Atomic Signal
  → versioned Signal Cluster snapshot
  → SEO Opportunity（后续节点）
```

### Source Observation

来源事实或指标窗口的版本化观测。它保留来源自然键、revision、项目、市场、语言、发生/采集时间、原生指标、质量与 freshness。第一方 VOC Observation 是其受治理的子类型。

### Atomic Signal

从一个或多个 Observation 得到的单主题事实主张。一条多主题客户消息可以产生多个 Signal；每个 Signal 都保留 derivation、taxonomy/model/prompt version 和 Evidence Reference。Signal 保留来源原生指标，不计算跨来源通用强度分。

### Signal Cluster

一次聚类运行产生的不可变成员快照。默认边界为：

```text
Project × SEO Operating Mode × Market × Language
× Canonical Topic/Aspect × Analysis Window
```

Cluster 只表达“这些当前有效 Signal 可能共同描述同一需求、问题或变化”，不等于 SEO Opportunity，也不自动推荐新建文章。

### Evidence Reference 与 Evidence Family

Evidence Reference 是 Signal 到具体 Observation revision、安全摘要或原生指标的中立引用。`support`、`counter`、`context` 是 Signal 在特定 Cluster 中的 membership role，不是 Evidence 的固有属性。

已确认来自同一底层内容或事件的多条来源记录组成一个 Evidence Family。它们保留各自来源血缘，但在独立佐证数量中只计算一次。

## 合成样本与结果

### REDMAGIC DTC 模式

原型输入 11 条合成来源记录，覆盖 GSC、DataForSEO、Google Trends、Reddit、Judge、Gorgias、Serper 和 Google News RSS，并加入以下压力场景：

- 同一个 GSC window 被完全重复拉取；
- 同一个 Reddit 帖子有 revision 1 和 revision 2；
- 一条去标识 VOC 同时提及发热与风扇噪音；
- Serper 与 RSS 抓到同一篇转载新闻；
- 相同散热主题同时出现在 US/en 和 UK/en。

结果：

| 项目 | 结果 |
| --- | ---: |
| 输入来源记录 | 11 |
| 保留的唯一 Observation revision | 10 |
| 忽略的完全重复拉取 | 1 |
| 标记为 superseded 的旧 revision | 1 |
| 派生 Atomic Signal | 13 |
| 当前 Signal Cluster | 4 |

REDMAGIC US/en 的 `gaming-phone-cooling` Cluster 有 8 个当前 Signal，但只有 7 个独立 Evidence Family：两条新闻来源属于同一转载家族。独立成员角色为 5 个 support、1 个 counter、1 个 context。DataForSEO 的较低关键词量没有被平均掉，仍作为反向证据可见。

同一条 VOC 产生了“gaming phone cooling”和“sustained gaming performance”两个 Signal；同一个更新后的 Reddit Observation 产生“cooling”和“fan noise”两个 Signal。UK/en 的 cooling Signal 没有进入 US/en Cluster。

### Heyup 媒体模式

原型输入 5 条合成来源记录，覆盖 GSC、GA4、Reddit、DataForSEO 和 News。它们形成一个 US/en 的 `mini-projector-netflix` Cluster：3 个 support 与 2 个 context，所有成员均可回到来源 Observation revision。

这证明共同底座不需要为 Heyup 改变数据关系；差异发生在 Operating Mode、Profile、后续准入和动作判断，而不是 Signal 基础结构。

## 原型暴露并修正的两个错误

### Evidence 不能自带支持或反对立场

“关键词量为 90”对“这是大规模需求”是 counter，但对“这是低竞争长尾”可能是 support。因此角色必须属于 Cluster membership，不能写死在 Evidence 上。

### 来源数量不等于独立证据数量

Serper 和 RSS 可能返回同一篇转载。两条来源记录都要保留以审计采集与解析，但需要 Evidence Family 避免把转载次数当作独立佐证。

## 用户确认的决议

1. 使用 `Source Observation → Atomic Signal → Signal Cluster → SEO Opportunity` 四层结构。
2. Signal 原子化；一个 Signal 只表达一个主题下的一项事实主张，一条 Observation 可以派生多个 Signal。
3. Signal 不设置跨来源统一强度分，保留来源原生指标；评分留给 Opportunity 节点。
4. 完全重复采集只计一次；新 revision 保留历史但只有当前有效 revision 进入最新 Cluster；跨来源相似内容不自动删除。
5. Signal Cluster 是有项目、模式、市场、语言、主题和分析窗口边界的版本化成员快照。
6. Evidence 保持中立；support/counter/context 属于 Cluster membership。转载血缘保留，但独立 Evidence Family 只计一次。
7. LLM 可以提出实体、主题、拆分、membership 和转载判断；来源指标由确定性计算提供，低置信度语义判断进入待审核。
8. Supabase/PostgreSQL 后端需要表达 Observation、Signal、Cluster Run、Cluster Membership 和 Evidence Reference 的关系；具体 Drizzle schema 留到规格阶段。BigQuery 继续只读且不修改 schema 或存储。

## 对后续节点的约束

- Signal Cluster 不能直接被当作 SEO Opportunity。
- 不把旧 `DiscoverySignal.score` 或 `draftability_score` 迁移为 Signal 强度。
- Opportunity 准入与评分必须读取支持、反向和背景证据，并使用独立 Evidence Family 数量。
- Content Inventory 与发布后表现可以生成 Signal，但原始 URL/页面资产及 performance snapshot 仍有自己的领域身份。
- Cluster membership、derivation 与 Evidence Family 判断都必须版本化，不能原地覆盖后失去可解释性。

## 原型处置

用户确认以上结论后，throwaway TUI、纯逻辑模块和合成 fixture 已删除。本文和领域模型、ADR 是保留资产；正式实现需在规格与 ticket 阶段重新设计并测试，不能直接复制原型代码进入生产。

