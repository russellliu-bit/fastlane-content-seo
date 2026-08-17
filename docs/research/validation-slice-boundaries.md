# SEO MVP 双验证切片边界

- 状态：已确认
- 日期：2026-08-12
- 对应 Issue：[选择代表性 DTC 品牌与双切片验证数据边界](https://github.com/russellliu-bit/fastlane-content-seo/issues/2)

## 决策摘要

SEO MVP 使用两个薄纵向切片验证共同底座与两种 SEO 运行模式：

| 切片 | 运行模式 | 市场 | 语言 | 数据范围 |
| --- | --- | --- | --- | --- |
| Heyup | 媒体 SEO | 美国 | 英语 | 截至最近共同完整日期的近 180 天日粒度数据 |
| REDMAGIC | DTC 品牌 SEO | 美国 | 英语 | 截至最近共同完整日期的近 180 天日粒度数据 |

两个切片使用相同市场和语言，以减少无关变量；核心验证对象是两种运行模式的决策逻辑，而不是品牌间流量规模的横向比较。近 180 天是原型的数据准备范围，分析可按 7、28、90 和 180 天窗口观察；它不构成生产系统永久固定的 Opportunity 评分窗口。

## 切片证据边界

### 共同证据

两个切片都需要：

- 现有内容资产清单；
- GSC 搜索表现；
- GA4 站内行为；
- 关键词需求数据与 SERP 快照；
- Google Trends 趋势数据；
- Reddit 社区信号；
- Google News 或等价新闻源。

REDMAGIC 还必须接入按项目隔离、脱敏、只读的 BigQuery 产品评论与客服工单标准视图。Heyup 不强制第一方 VOC，但必须具备媒体内容资产和外部热点信号。

### 最低信号就绪门槛

双切片 Opportunity 验证开始前，必须有一套小型但端到端可运行的 SEO Signal Collector，至少完成：

```text
关键词配置
→ 分源采集
→ 原始结果持久化
→ 标准化 Signal
→ 聚类与去重
→ 关联已有内容
→ 形成 Opportunity 证据包
```

“来源已接通但当前没有结果”是有效状态；“来源采集能力尚未接通”不算该来源 ready。MVP 不等待完整 Marketing Listening 数据管道，但小型采集器应遵循可被长期系统替换的 Signal 语义和来源契约。

Fastlane 仓库中用户提及的 `day` 项目是后续设计小型信号采集器时的候选参考资产；其能力和代码在信号采集专项 Issue 中另行核验，本决策不预设复用结论。

## 数据安全与持久化

- 分析在受控环境中使用真实、只读的 GSC、GA4、BigQuery、内容资产和外部来源数据。
- 仓库只保存 schema、聚合统计、脱敏代表性样本、合成 fixtures、Opportunity 结果和不含个人信息的证据摘要。
- 客服工单或评论原文、用户标识、订单信息、邮箱、凭据及其他个人信息不得进入 GitHub。
- Opportunity 可以在受控后端保存内部证据引用；仓库文档只展示脱敏摘要。
- 原始信号、中间结果、Opportunity、评分版本、审核和发布后表现都必须进入后端持久化层；本地 artifacts 不是系统事实来源。

## 验证样本与追溯要求

每个切片至少人工复核 10 个由真实数据形成的 SEO Opportunity。样本不设置机械动作配额，但整体应覆盖：

- Create；
- Update 或 Expand；
- Link；
- Monitor；
- 被拒绝或证据不足的 Opportunity Assessment。

Merge 和 Reposition 只在真实证据支持时纳入，不为覆盖动作而人为制造样本。

每个 Opportunity 必须可以回溯：

```text
原始 Signal 与来源
→ 聚类或主题
→ 关联的现有内容
→ GSC / GA4 / VOC / 外部证据
→ 准入判断
→ 评分解释与版本
→ 推荐动作
```

单条 Opportunity 不要求同时使用所有来源，但必须记录实际使用的证据、缺失或冲突的证据，以及结论置信度。

## 审核链与最终裁决

验证使用三层审核：

1. **确定性规则校验**：检查必填字段、来源引用、时间范围、重复项、评分计算和证据包完整性。
2. **LLM 独立初审**：以独立 reviewer prompt 和调用读取原始证据包，质疑证据充分性、搜索意图、动作合理性及证据冲突，并输出 `recommend_approve`、`recommend_decline` 或 `escalate`。MVP 可以复用同一基础模型，但不能复用生成调用的上下文来完成自我认证。
3. **SEO 责任人终审**：由用户或其指定的单一 SEO 负责人作出 `approved`、`declined` 或 `needs_evidence` 的最终判断并记录理由。

系统必须保存规则版本、模型与 prompt 版本、LLM 初审结论、人工终审结论、理由和时间。LLM 只有建议权，不能覆盖人工终审。两组标签将用于后续计算 LLM 与人工判断的一致率。

## 判定验证充分

只有同时满足以下条件，单个切片才算验证充分：

- 最低信号组合达到就绪门槛；
- 真实数据形成的 Opportunity 不少于 10 个；
- 样本整体覆盖规定的核心动作类别；
- 每个 Opportunity 具备端到端证据链和版本留痕；
- 每个 Opportunity 已通过规则校验、LLM 独立初审和人工终审；
- 审核结果能够区分 `approved`、`declined` 与 `needs_evidence`，而不是只保留成功样本。

双切片都满足以上条件，才足以说明共同底座可以进入后续规格设计；这不等同于生产系统已经具备上线条件。

## 本决策不包含

- 完整 Marketing Listening 平台的实现；
- 具体关键词数据供应商的最终选择；
- Opportunity 准入门槛、各评分维度、权重和阈值；
- Operational Database 与 Analytics/Warehouse 的最终技术选型及物理拆分；
- CMS 发布或后台写入。
