# SEO Opportunity Assessment 决策模型

- 状态：已确认
- 首次确认：2026-08-15
- 最近更新：2026-08-17
- Wayfinder 节点：[定义 SEO Opportunity 准入、动作与评分维度](https://github.com/russellliu-bit/fastlane-content-seo/issues/8)
- 后续校准节点：[用双切片样本校准 Opportunity 判断](https://github.com/russellliu-bit/fastlane-content-seo/issues/9)

## 用途

本文是 SEO Opportunity 判断的可解释决策记录，用于统一人类讨论、Agent 输出、后端记录和后续样本校准。它记录已经确认的领域边界和 `confidence-model-v1` / `review-flags-v1` 初始契约，不是最终 Drizzle schema，也不表示这些阈值已经被统计验证。

## 1. 候选评估与正式 Opportunity 分离

采用以下关系：

```text
Signal Cluster
  → Opportunity Assessment
  → SEO Opportunity
  → Recommended Action
```

- `Opportunity Assessment` 保存对候选的版本化评估，包括准入门槛、缺失数据、反向证据、评分输入和结果。
- `rejected` 与 `insufficient_evidence` 是 Assessment 结果，不生成 SEO Opportunity。
- 只有通过准入的 Assessment 才生成 SEO Opportunity。
- `Monitor` 是正式 Opportunity 的有效行动；`Reject` 不是行动。

这样可以保留被拒绝或暂时证据不足的判断历史，同时不把它们计入正式 Opportunity 数量。

## 2. 两阶段决策

Opportunity 判断分为两个阶段：

1. **准入**：先检查不可被其他高分抵消的共同底线和证据配方。
2. **排序与行动**：只有通过准入的候选才计算 Priority、Confidence、Review Flags，并选择推荐行动。

搜索量、趋势或业务价值不能抵消超出品牌边界、缺少必要证据、身份无法确认或阻断性风险。

## 3. 共同准入底线

所有 Opportunity Assessment 都必须满足：

1. 项目、SEO 运行模式、市场、语言和主题边界明确，并符合项目或品牌内容边界。
2. 使用确定 revision 的 Signal Cluster，关键主张可回溯到 Source Observation 与 Evidence Reference。
3. 至少一项主要证据符合当前来源和内容类型的 freshness 要求。
4. 已检查 Content Inventory，明确没有承接页、已有相关资产，或存在待解决的 URL/资产关系。
5. 反向证据、重复转载、数据异常、品牌与事实风险已显式记录；关键冲突无法解释时不得准入。
6. 至少存在一个符合资产治理权限的可执行方向；`unknown` 或 `observed_only` 资产不得被自动覆盖。

## 4. Opportunity Evidence Recipe

共同底线之上，各类判断使用自己的证据配方，不要求每条候选同时拥有全部来源，也不采用固定“最低来源数量”。

| 判断类型 | 最低证据角色 |
| --- | --- |
| 新需求或热点覆盖 | 需求/趋势证据 + SERP/关键词证据 + Inventory 覆盖检查 |
| 第一方问题覆盖 | VOC/社区问题证据 + 搜索可发现性证据 + Inventory 覆盖检查 |
| 内容更新或扩写 | 目标 Content Asset + 当前 Revision + 表现或内容时效证据 |
| CTR 优化 | GSC impressions/CTR/query intent + 当前 title/meta |
| 内容衰退 | 成熟页面表现窗口 + 可比较基线 + 季节性/追踪异常排查 |
| 关键词蚕食 | 同一 query-intent 下多个独立 Content Asset + 重复时间窗口 + canonical 排查 |
| 内链机会 | 两个以上相关 Content Asset + 主题/实体关系 + 当前链接覆盖 |
| Monitor | 机会方向成立，但时机、数据量或发布条件尚未成熟 |

证据配方后续可以版本化扩展。Evidence Family 独立性和证据角色比表面来源数量更重要。

### 缺失数据三分法

- `source_not_ready`：来源能力尚未接通；若它承担当前配方的必要角色，Assessment 为 `insufficient_evidence`。
- `ready_no_result`：来源已就绪但当前返回空结果；这是有效空观测，可作为反向或背景证据。
- `not_applicable`：来源不适用于当前判断；不扣分，也不阻止准入。

三者不得统一记录为“数据缺失”，也不得把 API 缺行自动解释为指标为零。

## 5. Priority、Confidence 与 Review Flag 分离

每个正式 SEO Opportunity 独立输出：

- `Opportunity Priority Score`：用于 backlog 相对排序；不表达结论为真的概率。
- `Opportunity Evidence Confidence`：表达证据和匹配足以支持当前判断的程度；不参与 Priority 加权。
- `Review Flag`：表达需要解释、复核、限制动作或阻断推进的结构化条件；不能作为普通扣分项被高价值抵消。

例如，一个高时效、证据尚短的新产品新闻可以是“高 Priority + 中 Confidence”；一个证据完整但影响较小的旧文衰退可以是“中 Priority + 高 Confidence”。

## 6. confidence-model-v1

底层保存 `0–100` 的 Evidence Confidence Score；`high / medium / low` 是由分数和非补偿规则共同产生的展示等级，不是 LLM 自报信心，也不是统计概率。

| 维度 | 权重 | 含义 |
| --- | ---: | --- |
| Evidence Recipe Coverage | 25 | 该类判断要求的证据角色是否完整 |
| Evidence Independence | 20 | 是否排除了重复采集、转载和非独立佐证 |
| Source Reliability | 15 | 来源级别、采集状态、原始记录和 provenance 是否可靠 |
| Freshness Fitness | 15 | 数据是否适合当前内容类型和判断窗口 |
| Identity & Asset Match | 15 | 实体、query intent、URL 和 Content Asset 匹配是否可靠 |
| Conflict Resolution | 10 | 反向证据、异常和来源冲突是否得到解释 |

### 初始分档

| Score | Level | 解释 |
| ---: | --- | --- |
| 80–100 | `high` | 证据角色基本完整、关键匹配可靠且没有未解决的重要冲突 |
| 60–79 | `medium` | 有足够依据，但存在非关键缺口或需人工核验的语义判断 |
| 40–59 | `low` | 可以形成 Opportunity，但只能进入 Monitor、研究或强人工审核路径 |
| 0–39 | 无 | Assessment 为 `insufficient_evidence`，不生成 Opportunity |

### 非补偿规则

- 缺少 Opportunity Evidence Recipe 的必要角色时，不得通过准入。
- 存在未解决的 `blocker` Review Flag 时，不得通过准入或进入该 Flag 所阻断的流程。
- Confidence 输入、子分、权重、规则和模型版本必须留存，不能只保存最终等级。

这些权重和 `80/60/40` 阈值是可检验的 MVP 初始假设。后续通过 Heyup 与 REDMAGIC 的真实、只读双切片样本和人工终审标签检查分档的单调性、误判类型和阈值，不把 80 分解释成“80% 正确率”。

## 7. priority-model-v1

Priority Score 使用共享维度语义、运行模式初始权重和有证据的 `0–5` rubric。LLM 必须选择 rubric 中有定义的等级并引用证据，不能自由生成一个缺少计算过程的总分。

### 共享维度

| 维度 | 回答的问题 |
| --- | --- |
| Audience Demand | 是否存在真实搜索、讨论或用户需求 |
| Momentum & Timing | 需求是在上升、稳定还是衰退，时间窗口是否紧迫 |
| Strategic Fit | 是否符合项目使命、频道定位、品牌边界和当前重点 |
| Organic Upside | 是否存在搜索覆盖缺口、排名推进空间、CTR 或内容衰退机会 |
| Expected Outcome Value | 成功后对受众、媒体影响或业务结果的潜在价值 |
| Content Leverage | 能否利用已有资产、内链、实体资料和已有权重，以较小内容动作获得收益 |

维度语义由共同底座定义；Heyup 媒体模式与 DTC 品牌模式使用不同的初始权重。

### Heyup 媒体模式初始权重

| 维度 | 权重 |
| --- | ---: |
| Audience Demand | 15 |
| Momentum & Timing | 25 |
| Strategic / Editorial Fit | 20 |
| Organic Upside | 15 |
| Expected Audience / Media Value | 15 |
| Content Leverage | 10 |

Heyup 提高 Momentum & Timing 权重，以适应媒体内容的时效窗口；Editorial Fit 防止系统只追逐与 Heyup 无关的高热度。

### DTC 品牌模式初始权重

| 维度 | 权重 |
| --- | ---: |
| Audience Demand | 20 |
| Momentum & Timing | 15 |
| Strategic / Brand Fit | 20 |
| Organic Upside | 15 |
| Expected Business Value | 20 |
| Content Leverage | 10 |

DTC 提高稳定需求和业务价值权重，以支持新品、活动、购买决策与第一方 VOC，而不是完全跟随热点。

### 执行成本独立保存

执行成本不进入 Priority 加权。Opportunity 另行保存：

- `effort_level`：`xs / s / m / l / xl`；
- estimated lead time；
- required review tier；
- required capabilities。

排期可以同时比较 Priority 和 Effort，但不能让高成本被误写成低价值，也不能让低成本自动变成高价值。

共享维度、rubric、权重、输入和模型版本都必须留存。品牌 SEO Profile 可以提供评分上下文，但不能任意发明新的 Priority 维度。以上权重是 `priority-model-v1` 初始假设，留待双切片样本校准。

## 8. review-flags-v1

### Code 规范

稳定机器 code 使用：

```text
{category}.{subject}.{condition}
```

- 全部小写英文，使用点号分层。
- code 不编码严重级别，也不随显示语言变化。
- 人类标题、解释、影响和解除条件单独存储。
- code 发布后保持稳定；含义变化时升级 catalog version 或使用新 code。

允许的第一版 category：

- `evidence`
- `source`
- `identity`
- `fact`
- `brand`
- `legal`
- `content`
- `measurement`
- `workflow`

示例：

- `fact.product.unverified`
- `identity.asset.match_uncertain`
- `evidence.required_role.missing`
- `evidence.families.not_independent`
- `measurement.ga4.thresholded`
- `brand.topic.out_of_scope`
- `legal.claim.review_required`
- `workflow.asset.approval_required`

### 严重级别

- `blocker`：解决前不能准入，或不能进入明确指定的后续流程。
- `review_required`：可以保留 Opportunity，但进入指定阶段前必须人工复核。
- `advisory`：不阻断，只提供解释和背景。

严重级别不使用 high/medium/low，避免与 Evidence Confidence 混淆。

### Flag 必备信息

```json
{
  "code": "fact.product.unverified",
  "catalog_version": "review-flags-v1",
  "category": "fact",
  "severity": "review_required",
  "title": "产品事实尚未核验",
  "explanation": "文章涉及的产品参数目前只有非官方来源支持。",
  "evidence_refs": ["evidence-ref-123"],
  "blocks_transitions": ["cms_handoff"],
  "resolution": "获得官方产品页或产品负责人确认。",
  "status": "open",
  "detected_by": "rule.product-fact-source.v1"
}
```

每个 Flag 必须让机器能够稳定判断 code、严重级别、阻断阶段和状态，也必须让人能够读懂发生了什么、为何触发、影响什么以及如何解除。

## 9. Recommended Action Plan

每个正式 SEO Opportunity 使用“一个主动作 + 零个或多个辅助操作”。主动作表达核心内容策略，辅助操作表达实现组成，避免多个平级动作无法确定决策中心。

### 主动作

| Code | 定义 |
| --- | --- |
| `create` | 没有合适承接资产，建议建立新的 Content Asset |
| `update` | 修正或刷新已有资产，但不显著改变其主要搜索意图与覆盖范围 |
| `expand` | 在已有资产上新增重要子主题、query family 或内容模块，扩大覆盖范围 |
| `consolidate` | 两个或更多资产意图高度重叠，建议选定 survivor 并整合其他资产 |
| `reposition` | 改变已有资产的主要搜索意图、受众、频道角色或内容定位 |
| `link` | 内容本身基本合适，主要机会是建立或优化内部链接 |
| `monitor` | 机会成立，但目前不应实施内容变更，等待时机或更多证据 |
| `retire` | 资产继续存在的价值低于重复、过期、风险或维护成本，建议退出活跃内容组合 |

`reject` 是 Opportunity Assessment 结果，不是主动作。

### 动作边界

- `update` 保持主要搜索意图与覆盖范围，处理事实、时效、失效引用、metadata 等刷新。
- `expand` 保持主要意图，但增加重要 query family、子主题或内容模块。
- `reposition` 改变主要受众、搜索意图、频道角色或内容定位。
- `consolidate` 是内容策略；redirect 是可能伴随它的实施建议，不是主动作。
- `link` 只在内部链接是主要干预时作为主动作；伴随其他内容动作时使用辅助操作。

### 辅助操作初始集合

- `metadata_optimize`
- `content_refresh`
- `add_section`
- `internal_link_add`
- `internal_link_remove`
- `merge_content`
- `redirect_recommendation`
- `canonical_review`
- `schema_markup_recommendation`
- `fact_verification`
- `localization`

辅助操作也必须使用稳定 code，并保存解释、目标资产与完成条件。

### 资产和治理约束

- `create` 必须证明没有合适承接资产。
- `update`、`expand`、`reposition`、`link`、`retire` 必须指向明确 Content Asset 与当前 Revision。
- `consolidate` 必须指定一个 survivor 和至少一个 donor。
- `monitor` 必须记录复评日期或可检测的复评触发条件。
- `retire`、`consolidate`、`redirect_recommendation` 始终需要人工审批。
- 所有动作只是建议与内容交付计划，不执行 Shopify、CMS、redirect 或站点写入。

## 10. 共同底座、Operating Mode 与 Brand SEO Profile

### 共同底座固定

以下语义不能由单个项目或品牌覆盖：

- Signal Cluster、Opportunity Assessment、SEO Opportunity 的关系；
- Assessment 结果和缺失数据状态；
- Priority 与 Evidence Confidence 的维度语义；
- Confidence 非补偿原则；
- Review Flag code、category 和 severity 规范；
- Recommended Action Plan 的主动作与辅助操作语言；
- 评分、判断和规则版本必须可追溯。

### SEO Operating Mode 选择默认策略

媒体模式与 DTC 模式可以分别配置：

- Priority 默认权重；
- Opportunity Evidence Recipe；
- Content Type freshness 与分析窗口；
- Momentum、Strategic Fit、Expected Outcome Value 的具体 rubric；
- 动作默认审核级别；
- 内容节奏、复评时机和成功结果解释。

### Brand SEO Profile 提供上下文

Brand SEO Profile 可以提供市场、语言、受众、定位、内容边界、产品与竞品实体、频道或内容类型、业务事件、数据连接、outcome 定义和资产治理权限。它们作为共同 rubric 的输入，不形成隐藏的品牌专属算法。

第一版不允许 Brand SEO Profile：

- 新增或删除 Priority / Confidence 维度；
- 自定义 Confidence 分档；
- 把 blocker 改成普通扣分；
- 改变 Action code 的含义；
- 隐式覆盖总分公式；
- 让高分绕过人类审核要求。

真实样本若证明需要不同算法，应创建显式、可审查的 scoring policy version，而不是通过 Profile 隐式改变结果。

### Strategic Directive

品牌或项目可以保存有期限的 Strategic Directive，作为评分输入表达新品、活动或阶段性业务重点。它至少包含主题或实体、生效与失效时间、影响的 rubric、业务理由和批准人。

Strategic Directive 影响 Strategic Fit、Momentum 或 Expected Outcome Value 的证据判断，但不直接给总分加固定分数，也不能绕过准入、Review Flag 或审核规则。

## 11. Assessment 与 Opportunity 审核状态

### Opportunity Assessment

```text
draft
  → evaluating
      ├─ admitted
      ├─ rejected
      └─ insufficient_evidence
```

- `admitted`：通过准入并生成正式 SEO Opportunity。
- `rejected`：候选可以判断但不成立，例如超出边界或属于误识别。
- `insufficient_evidence`：当前无法可靠判断，补充数据后可以重新评估。
- 重新评估创建新 Assessment version；旧版本标记 `superseded`，不覆盖当时的证据、规则和结果。

### LLM Preliminary Review

正式 SEO Opportunity 以 `proposed` 状态进入独立 LLM 初审。LLM 重新读取原始证据包、支持/反向/背景证据、Evidence Recipe、站内覆盖和 Action Plan，只能输出：

- `recommend_approve`；
- `recommend_decline`；
- `escalate`。

LLM reviewer 必须使用独立 prompt 和调用；可以复用同一基础模型，但不能复用生成 Opportunity 的隐藏上下文完成自我认证。模型、prompt、证据输入、建议与理由都要版本化保存。

### Human Opportunity Review

明确 SEO 责任人对 Opportunity 与 Action Plan 作出：

- `approved`：接受当前 Opportunity 和 Action Plan；
- `declined`：证据可以判断，但负责人不接受该机会或行动；
- `needs_evidence`：当前证据不足，返回新的 Assessment，而不是作为正式拒绝。

人工决定保存 reviewer、时间和理由。LLM 建议不能覆盖人工结论。

### 分数不拥有批准权

Priority、Evidence Confidence 和 LLM 初审都不能单独自动批准 Opportunity。高分不能绕过 Review Flag、品牌治理或人工终审。

Heyup-first 仍可以高度自动化信号收集、Assessment、评分、Action Plan、evidence package、Brief/草稿/SEO 字段预生成和 LLM 初审；人工终审前的内容只能是内部候选，`approved` 前不能形成正式 CMS Handoff。本项目始终不执行 CMS 发布。

## 留给双切片校准

- 六个 Priority 维度的 `0–5` rubric 锚点与实际数据映射。
- `priority-model-v1` 权重产生的真实排序质量。
- `confidence-model-v1` 权重与 `80/60/40` 阈值的区分度。
- LLM 与人工判断的一致率及常见 false positive / false negative。
- Heyup 与 REDMAGIC 是否需要不同阈值或新的显式 scoring policy version。
- 哪些审核步骤在真实验证后有资格提高自动化程度。
