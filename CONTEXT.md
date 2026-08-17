# Fastlane Content SEO Domain

本文件定义 Fastlane Content SEO 在不同客户与内容业务之间共享的稳定领域语言。

## Language

**SEO 运行模式（SEO Operating Mode）**：
一类 SEO 项目共享的内容使命、决策流程和成功标准。只有这些要素发生根本变化时才新增运行模式；品牌上下文、参数或评分权重不同不构成新模式。
_Avoid_: 每品牌一套模式、工作流模板

**品牌 SEO Profile（Brand SEO Profile）**：
描述单个 DTC 品牌的市场、受众、定位、内容边界、竞争环境和业务约束的上下文资产；它约束 DTC 品牌模式，但不改变该模式的决策逻辑。
_Avoid_: 品牌运行模式、品牌配置文件

**Marketing Listening 系统（Marketing Listening System）**：
独立于 SEO 项目的共享上游能力，持续采集并标准化社交媒体、论坛、新闻、VOC 和其他市场信号，供 SEO 及其他营销场景消费。
_Avoid_: SEO 监听模块、SEO 爬虫

**Listening Profile**：
定义一个品牌或研究对象需要持续观察的品牌、产品、品类、需求、竞品、实体、来源和动态扩展词，是 Marketing Listening 系统的监测边界。
_Avoid_: 关键词列表、搜索词配置

**SEO 信号收集器（SEO Signal Collector）**：
SEO MVP 内置的有限信号采集能力，遵循未来 Marketing Listening 系统的同一信号语义，并在共享系统可用后被其替代；它不是独立的长期监听产品。
_Avoid_: Mini Marketing Listening、第二套 Listening 系统

**第一方 VOC 信号（First-party VOC Signal）**：
DTC 项目自身产品评论和客服工单中表达的用户问题、评价、需求与使用情境；当前源数据按项目维度存放在 BigQuery，不能与外部社区讨论混为一类。
_Avoid_: 博客评论、Reddit VOC、社媒声量

**来源观测（Source Observation）**：
对一个来源事实、记录或指标窗口的版本化捕获，是 Signal 的可追溯输入；它保留来源语义，但本身不表示选题或行动结论。
_Avoid_: Raw Signal、Topic、Opportunity

**第一方 VOC Observation（First-party VOC Observation）**：
从一条产品评论或一条客户客服消息形成、已确认项目归属并完成去标识的单条第一方反馈证据；它保留来源版本引用，但不是可直接公开引用的客户原文。
_Avoid_: 客户原声、VOC 原始行、客服工单

**信号（Signal）**：
由一个或多个来源观测支持、只表达单个主题下一项事实主张的原子记录；它保留原生指标和推导版本，但不包含跨来源统一强度分，也不是选题或行动结论。
_Avoid_: Discovery Score、选题、趋势结论、Opportunity

**Signal Cluster**：
一次聚类运行在同一项目、运行模式、市场、语言、主题和分析窗口内形成的版本化 Signal 成员快照；它表达相关性，但不表示已形成 SEO Opportunity。
_Avoid_: Topic Cluster、合并 Signal、Opportunity

**证据引用（Evidence Reference）**：
Signal 对具体来源观测 revision、安全摘要或原生指标的中立引用；支持、反向或背景角色属于特定 Cluster membership，而不是证据自身。
_Avoid_: 来源 URL、Evidence Score、事实结论

**证据家族（Evidence Family）**：
已确认来自同一底层内容或事件的一组来源记录；各来源血缘分别保留，但计算独立佐证数量时只视为一份证据。
_Avoid_: Source Count、多源共识

**Opportunity Assessment**：
对一个 Signal Cluster 结合站内覆盖、项目边界和证据完整性进行的版本化候选评估；它保存准入门槛、缺失数据、反向证据、评分输入和评估结果。`rejected` 与 `insufficient_evidence` 是 Assessment 结果，不生成 SEO Opportunity。
_Avoid_: SEO Opportunity、Reject 动作、候选选题

**Opportunity 证据配方（Opportunity Evidence Recipe）**：
某类 Opportunity Assessment 通过准入所需的证据角色、站内检查和反证处理规则；它按判断类型配置，不要求每个候选同时具备所有来源，也不以表面来源数量代替独立证据质量。来源未接通、来源就绪但无结果、来源不适用是三个不同状态。
_Avoid_: 固定来源清单、最低来源数、缺失数据统一扣分

**SEO Opportunity**：
由通过 Opportunity Assessment 准入的候选形成、值得采取或规划 SEO 行动的结构化机会；它必须保留评估版本、证据、评分版本和推荐行动，而不等同于新文章选题。`Monitor` 可以是有效行动，`Reject` 不是行动。
_Avoid_: Topic Candidate、自动选题、内容 Idea、被拒绝的 Opportunity

**Opportunity Priority Score**：
对已经通过准入的 SEO Opportunity 进行 backlog 排序的版本化多维分数；它表达相对投入优先级，不表达判断为真的概率，也不能用高价值抵消阻断性风险。
_Avoid_: Opportunity Confidence、成功概率、统一 Signal 强度分

**Opportunity Evidence Confidence**：
对一次 Opportunity Assessment 的证据充分性、独立性、时效性、来源可靠性、实体或资产匹配以及冲突处理程度的版本化评估；它与 Priority Score 分离，不能直接解释为统计概率。
_Avoid_: LLM 自报置信度、Priority Score、主观 high/medium/low

**Review Flag**：
Opportunity Assessment 或 SEO Opportunity 上一项需要解释、复核、限制动作或阻断推进的结构化条件；它使用稳定 code、类别、严重级别、人类可读标题与解释、证据引用、动作影响和解除条件，而不是自由文本标签。
_Avoid_: Risk 扣分项、模糊 warning、无解释的字符串标签

**发布记录（Publication Record）**：
外部 CMS 中已交付或已发布内容的身份、URL、市场、版本、状态和时间记录，用于连接内容资产与后续表现；它不表示本项目负责执行发布。
_Avoid_: 发布任务、Shopify 写入结果

**验证切片（Validation Slice）**：
用于探索或原型验证的一组有边界的数据样本，由品牌、SEO 运行模式、市场、语言、时间范围和可用证据共同限定；它不规定生产系统的永久分析窗口。
_Avoid_: 固定评分窗口、试点品牌配置

**LLM 初审（LLM Preliminary Review）**：
在确定性规则校验之后、人工终审之前进行的独立模型审核；它读取原始证据包并给出建议结论与理由，但没有最终裁决权。
_Avoid_: 自动批准、LLM 终审、自我认证
