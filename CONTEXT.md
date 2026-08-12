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

**信号（Signal）**：
带有来源、观测时间、市场和证据引用的标准化事实记录；它可以提示需求或变化，但本身不是选题或行动结论。
_Avoid_: 选题、趋势结论、Opportunity

**SEO Opportunity**：
由一个或多个信号及站内覆盖情况支持、值得评估采取 SEO 行动的结构化机会；它必须保留证据、准入结果、评分版本和推荐行动，而不等同于新文章选题。
_Avoid_: Topic Candidate、自动选题、内容 Idea

**发布记录（Publication Record）**：
外部 CMS 中已交付或已发布内容的身份、URL、市场、版本、状态和时间记录，用于连接内容资产与后续表现；它不表示本项目负责执行发布。
_Avoid_: 发布任务、Shopify 写入结果

**验证切片（Validation Slice）**：
用于探索或原型验证的一组有边界的数据样本，由品牌、SEO 运行模式、市场、语言、时间范围和可用证据共同限定；它不规定生产系统的永久分析窗口。
_Avoid_: 固定评分窗口、试点品牌配置

**LLM 初审（LLM Preliminary Review）**：
在确定性规则校验之后、人工终审之前进行的独立模型审核；它读取原始证据包并给出建议结论与理由，但没有最终裁决权。
_Avoid_: 自动批准、LLM 终审、自我认证
