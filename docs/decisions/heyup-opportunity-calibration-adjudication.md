# Heyup Opportunity 校准裁决

- 日期：2026-08-27
- Wayfinder 节点：[用双切片样本校准 Opportunity 判断](https://github.com/russellliu-bit/fastlane-content-seo/issues/9)
- 状态：探索阶段裁决完成；不是生产模型效果认证

## 1. 本次回答了什么

本次用 15 个 Heyup US/en 真实只读 maintenance case，验证规则、事实指标、独立 LLM 初审和人工业务复核应如何组合。结果足以确定后续规格中的审核职责、fail-closed 边界和状态流，但不能证明 Priority 权重、Confidence 阈值或任何自动化模型已经达到生产准确率。

本次没有执行 CMS/Shopify 写入，也没有修改 GSC、GA4、CMS 或其他源系统。

## 2. 裁决输入与可追溯性

| 输入 | 作用 | 留存边界 |
| --- | --- | --- |
| expansion cohort 中立 evidence package | 真实页面、GSC、GA4、页面快照与链接关系 | 本地 `artifacts/`，不提交 |
| generator proposal | 被审核的 Assessment、Opportunity 与 Action Plan | 本地 `artifacts/`，不作为金标 |
| `reviewer_output.jsonl` | 独立技术 Assessment、初审、动作判断与排序 | 本地 `artifacts/`；SHA-256 `8f659a2e77f5e545726724c7b4e9245a8dd2b8504b89d8bf3b4f920300ff0b56` |
| TL 简版问卷 | Heyup 编辑价值、业务时机、动作可接受性与排期信号 | 原始工作簿不提交；SHA-256 `20033da7e10e434d9abd2d5742a8fb1997028ad961c6e6adba64cccbc9b01324` |
| `adjudicated_review.jsonl` | 15 个 case 的复合裁决结果 | 本地 `artifacts/`，本文件保存可提交摘要 |

TL 问卷第一步完成 11/15：8 个 positive、3 个 insufficient context、4 个未答；第二步动作选择完成 15/15，只有 4 个给出编辑排期 band。未答不被补造，`不确定` 和 `信息不够` 保留为有效反馈。

## 3. 审核职责必须拆成三层

### 3.1 Technical / Data Gate

系统与 SEO/Data Reviewer 负责：

- country/language/query slice 是否一致；
- GSC、GA4、页面快照和 CMS revision 的状态及冲突；
- Evidence Recipe 是否齐备；
- 实体聚类、页面身份、canonical 和事实时效；
- `admitted | rejected | insufficient_evidence`；
- Action Plan 是否与证据匹配。

异常、缺数和身份不明必须 fail closed，不能要求内容 TL 用经验替代数据裁决。

### 3.2 Editorial / Business Review

Heyup TL 负责：

- 主题是否符合 Heyup 媒体定位；
- 行业事件、新品周期和内容角度是否值得跟进；
- 动作是否符合编辑实践；
- 当前 calendar、资源与业务节奏下的排期优先级。

TL 的 positive signal 不能绕过 Technical Gate；TL 的 `信息不够` 也不等于技术上不存在 Opportunity。

### 3.3 Final Owner Decision

最终负责人合并技术结论与编辑信号，决定：

- `approved`：接受 Opportunity 与当前 Action Plan；
- `needs_evidence`：退回补证据或改写 Action Plan；
- `not_applicable`：Assessment 未准入，不存在正式 Opportunity。

`approved` 只表示进入合格 backlog，不等于立即排期、发布或授权 CMS Handoff。

## 4. 最终裁决

| Case | Assessment | Opportunity Decision | Action | Rank | TL 排期信号 | 裁决摘要 |
| --- | --- | --- | --- | ---: | --- | --- |
| A01 | admitted | approved | correct | 1 | low | SEO 机会强，但当前编辑排期低；两种优先级同时保留 |
| A02 | insufficient_evidence | needs_evidence | uncertain | — | low | 编辑时机为正，但主导 query 与 US/en slice 存在语言身份冲突 |
| A03 | admitted | needs_evidence | uncertain | — | low | 先确认公开页、URL 与 CMS revision 身份 |
| A04 | admitted | approved | correct | 5 | high | 产品状态核验阻断 handoff，不阻断 Opportunity 准入 |
| A05 | admitted | approved | correct | 7 | high | 执行前补 CMS、hands-on 与 H1 证据 |
| B01 | rejected | not_applicable | not_applicable | — | — | slug 通用词造成错误实体聚类 |
| B02 | admitted | needs_evidence | incorrect → consolidate | — | — | 旧闻互相矛盾，不能直接互链，先形成合并/重定位提案 |
| B03 | admitted | approved | correct | 2 | — | 以 review 为中心连接 4 页产品生命周期 |
| B04 | admitted | approved | correct | 9 | — | 跨代路径成立但预期价值较弱 |
| B05 | admitted | approved | correct | 8 | — | 固件版本序列关系与链接缺口成立 |
| C01 | insufficient_evidence | needs_evidence | uncertain | — | — | 先解释 GSC/GA4 与尖峰窗口异常 |
| C02 | admitted | approved | correct | 3 | — | 保留 URL，将 preview 更新为当前产品状态 |
| C03 | admitted | approved | correct | 4 | — | 保留 URL，将 leak 更新为发布后事实 |
| C04 | rejected | not_applicable | not_applicable | — | — | 可保留观察记录，但不生成正式 Opportunity |
| C05 | admitted | approved | correct | 6 | medium | 新闻生命周期与更新动作一致 |

汇总：

- Assessment：`admitted 11 / insufficient_evidence 2 / rejected 2`；
- Final decision：`approved 9 / needs_evidence 4 / not_applicable 2`；
- Action：`correct 9 / uncertain 3 / incorrect 1 / not_applicable 2`；
- 9 个 approved case 形成无并列相对排序。

## 5. 校准暴露的五类失败模式

1. **技术机会与编辑排期混为一个优先级。** A01 的 SEO rank 为 1，而 TL 当前排期为 low；两者都可能正确，必须分字段保存。
2. **编辑热度替代数据质量。** A02、C01 有业务意义，但不能绕过语言 slice 或跨来源异常。
3. **无动作/观察项使用“批准进入处理队列”。** B01、C04 暴露问卷选项歧义；后续必须提供 `确认排除` 和 `接受观察、不建任务`。
4. **低成本动作掩盖事实冲突。** B02 不能因为补链接便宜就连接互相矛盾的旧闻。
5. **执行阻断被误当成机会阻断。** A04、A05 的事实和 CMS 核验应阻断 Handoff，不必自动否决已成立的 Opportunity。

## 6. 对 v1 模型的决定

- 保留 Assessment 与正式 Opportunity 分离。
- 保留 `Priority`、`Evidence Confidence`、`Review Flag` 分离。
- 新增或明确区分 `opportunity_priority` 与 `editorial_schedule_priority`。
- LLM 初审只能建议 `recommend_approve | recommend_decline | escalate`；不能覆盖人工责任。
- `needs_evidence` 创建新 Assessment revision，不把缺数写成零，也不把暂缓写成拒绝。
- 获批 Opportunity 可以进入内部 research/brief/draft 自动化；事实、作者责任、披露或 CMS revision flag 未解除时不得形成正式 Handoff。
- 不根据这 15 个 maintenance case 修改 `0–5` rubric、模式权重或 `80/60/40` Confidence 阈值；样本量、角色和覆盖面不足以支持统计调参。

## 7. 本次关闭范围与延期验证

Wayfinder 的终点是进入规格设计，而不是生产实现。接受以下证据组合完成本节点：

- Heyup 真实 maintenance cohort 的技术与编辑复合裁决；
- REDMAGIC 低保真端到端切片对共同生命周期与 DTC 决策点的验证。

以下内容不冒充已完成，进入规格后的 Eval/实施计划：

- REDMAGIC 至少 10 个真实只读 case 与责任人复核；
- Heyup `new-topic/create` cohort 10–15 个真实 case；
- 修改后 Action Plan 的再次审核，如 B02 consolidate；
- GSC/GA4 发布后实验与长期 outcome；
- Priority rank correlation、Confidence calibration、阈值误判和分模式阈值；
- 多 reviewer 一致性与真正盲化的生产验收。

因此，本节点解决的是“应该如何组合判断与责任”，不是宣称“系统已经达到某个准确率”。
