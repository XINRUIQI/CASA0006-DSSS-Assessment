# 1. Select a Main Dataset

## 1.1 英文版

**Main dataset:**
**Integrated Prominent Open-AI Projects Dataset (202201–202512)**, constructed by integrating:

1. **GitHub / GH Archive / GitHub API**, used to capture city-level innovation activity, cross-city collaboration, repository prominence, and the city collaboration network;
2. **Hugging Face Hub API**, used to capture model, dataset, and Space releases, popularity, and city-level adoption signals;
3. a project filtering layer that retains **open-AI-related projects** within the selected time window that have reached a **minimum diffusion threshold**, such as stars, downloads, visits, forks, or other platform-specific prominence indicators.

## 1.2 中文说明

主数据集定义为：
在指定时间范围内，与 open-AI 相关、并且传播已经达到一定程度的 prominent open-AI projects 的整合数据集。

这样做的好处是：

第一，它避免把整篇作业压在“技术家族边界怎么划分”这个最容易引起争议的问题上。

第二，它贴合主问题：你真正想研究的是全球城市如何参与 open-AI 技术/项目的创造、协作、传播和使用，而不一定只研究某一个狭窄家族。

第三，它仍然符合课程要求，因为作业允许使用自选数据集，只要与 urban or spatial processes 相关，并且适合分析。

## 1.3 主数据集的对象定义

主数据集中的“project”可以包括但不限于：

1. GitHub 上与 open-AI 相关的高影响仓库

2. Hugging Face 上与 open-AI 相关的高影响模型、数据集或 Spaces

“高影响 / prominent”可通过门槛筛选定义，例如：

1. GitHub：stars、forks、watchers、contributors、discussion/activity

2. Hugging Face：downloads、likes、model card visibility、Space visits 等

3. 必须满足 open-AI 相关性规则与最小传播门槛

## 1.4 样本设计

1. 时间范围：**202201–202512**
2. 时间粒度：**月度**
3. 城市数量：**100-150 个高置信度城市**
4. 技术范围：**主分析不强制先划分单一家族，而是对 prominent open-AI projects 的整体生态进行研究；具体技术家族可在 case study 中单独展示**
5. 分析单位：
   1. 城市
   2. 城市—城市协作边
   3. 城市—项目—月度采用事件

# 2. Define Your Research Question

作业要求研究问题要 **specific and clear**，并且在 notebook 中显式写出；Research Questions 部分应明确列出问题，且以问号结尾。

## 2.1 英文版

### 2.1.1 Main research question

**How do global cities participate in the creation and use of prominent open-AI projects, and what factors shape the diffusion of these projects across the global urban system?**

### 2.1.2 Sub-questions

1. **What distinct roles do global cities play in the ecosystem of prominent open-AI projects, such as originators, collaboration hubs, bridge cities, and late adopters?**
2. **Which city characteristics are associated with innovation-oriented roles and faster adoption within the ecosystem of prominent open-AI projects?**
3. **Can the GitHub city collaboration network help predict which cities will become the next adopters of prominent open-AI projects?**


# 3. Augment Your Data

作业允许你用 census、demographic、social、economic、environmental 等额外数据增强主数据集。
## 3.1 中文说明

需要额外的城市属性数据来解释：

1. 为什么有些城市更像 originators / collaboration hubs
2. 为什么有些城市更快 adopted 高影响项目
3. 为什么某些城市更容易成为下一波 adopter

## 3.2 推荐补充数据层

### 3.2.1 城市定义与空间匹配层

用于统一全球城市边界与名称：

1. OECD Functional Urban Areas 或 GHS Urban Centre Database
2. 城市经纬度
3. 国家 / 区域
4. 时区

### 3.2.2 人口与规模变量

1. 总人口
2. 劳动力规模 proxy
3. 城市规模等级

### 3.2.3 教育与人力资本变量

1. 高等教育比例
2. 本科及以上占比
3. STEM / 研究能力 proxy

### 3.2.4 经济变量

1. GDP per capita
2. 收入水平
3. 创业 / 创新环境 proxy

### 3.2.5 科研与创新能力变量

1. 顶尖大学 / 研究机构数量
2. R&D proxy
3. AI 研究能力 proxy

### 3.2.6 数字基础设施变量

1. 宽带 / 数字连接 proxy
2. ICT 或数字经济指标

## 3.3 用途说明

这些增强变量主要用于回答RQ2：

哪些城市特征与 innovation-oriented roles 和 faster adoption 相关？

同时，作业指南特别提醒，很多分析里应尽量使用 **rate** 而不是 raw count，因为 rate 更能控制规模差异。
所以后续建议尽量构造：

1. per-capita innovation rate
2. per-capita adoption rate
3. collaboration intensity rate

而不是只用绝对数。

# 4. Structure Your Analysis

## 4.1 中文说明

作业要求使用 notebook template，并把分析放在**单个 Python notebook**中；内容应包括代码、分析过程、解释和 narrative text，且 narrative 控制在 **1500 词以内**。

## 4.2 更新后的分析主线

建议 notebook 按下面这条逻辑展开：

项目筛选与城市映射

→ 构建 prominent open-AI projects 的城市活动、协作与采用指标

→ **EDA：对三张核心表和关键变量进行探索性数据分析，检查数据质量、分布特征和初步模式**

→ 识别 open-AI 项目生态中的城市 roles

→ 测量城市对高影响项目的 adoption lag

→ 解释哪些城市特征与 innovation-oriented roles / faster adoption 相关

→ 利用协作网络预测下一波 adopter 城市

→ 用 1–2 个具体技术家族或代表项目作为 case study 展示扩散路径和可视化

## 4.4 Notebook 运行策略

重要tips：

1. 不要在提交版 notebook 里做大量原始 API 抓取
2. 不要在 notebook 里做大规模 location 实时地理编码
3. 预处理尽量在 notebook 外完成，再读取清洗后的 csv/parquet
4. 提交前做 Restart & Rerun all

因为作业要求 notebook 应能完整运行，并建议在提交前验证可执行性；若预处理耗时较大，可以提供预处理后的数据并写清说明。

# 5. Choose Your Methods

作业要求所选方法必须与研究问题直接相关，避免堆砌无关方法。

## 5.1 Method 1: K-means

Purpose: identify distinct city roles in the ecosystem of prominent open-AI projects

Addresses: RQ1

### 5.1.1 输入变量

1. 项目 origination rate
2. 项目 adoption rate
3. collaboration intensity
4. network centrality
5. bridge/betweenness indicators
6. prominence-adjusted activity indicators

### 5.1.2 输出

1. 城市 cluster
2. cluster 的角色解释，例如：
   1. originators
   2. collaboration hubs
   3. bridge cities
   4. late adopters

### 5.1.3 中文说明

K-means 在所有 prominent open-AI projects 聚合形成的城市层指标上做聚类。

也就是说，它回答的是：

在高影响 open-AI 项目生态中，全球城市分别扮演什么角色？

## 5.2 Method 2: Adoption-lag regression

Purpose: model how quickly cities adopt prominent open-AI projects after each project’s first global appearance

Addresses: part of RQ2

### 5.2.1 因变量

project-level adoption lag：某城市首次采用某个 prominent project 距离该项目全球首次出现晚了多少个月

### 5.2.2 自变量

1. network centrality
2. prior open-AI activity
3. connection strength to early-originating cities
4. city attribute controls
5. project-level controls or project fixed effects

### 5.2.3 输出

1. 哪些变量与更短 project-level adoption lag 相关
2. 哪些城市在整体上更快 adopted 高影响项目

### 5.2.4 中文说明

lag 要按下面方式计算：

1. 对每个项目分别计算全球首次出现时间
2. 再计算每个城市相对这个项目的首次采用时滞
3. 最终把这些 城市—项目 级别的 lag 样本合并建模

为了控制不同项目之间的异质性，建议在回归里加入：

1. project fixed effects

或

2. project-level popularity controls

这样 adoption-lag regression 才和主数据定义一致。

## 5.3 Method 3: XGBoost

Purpose: explain how city characteristics relate to innovation-oriented roles and faster adoption in the ecosystem of prominent open-AI projects

Addresses: part of RQ2

### 5.3.1 可选任务

1. 预测城市是否属于 innovation-oriented role cluster
2. 预测城市是否属于 fast-adopting cities
3. 预测城市在多个项目上的平均 adoption speed

### 5.3.2 输入变量

1. education
2. income
3. population
4. research capacity
5. digital infrastructure
6. network centrality
7. baseline open-AI activity

### 5.3.3 配套解释

SHAP for feature importance and interpretability

### 5.3.4 中文说明

XGBoost 承担的是：

1. 哪些城市特征与 innovation-oriented roles 相关
2. 哪些城市特征与 faster adoption 相关

它的 outcome 不是某一个技术家族里的结果，而是在 prominent open-AI projects 整体生态中定义的结果变量。

## 5.4 Method 4: GraphSAGE

Purpose: predict which cities are likely to become the next adopters of prominent open-AI projects

Addresses: RQ3

### 5.4.1 任务定义

1. 使用 t 期 GitHub 城市协作网络 + 节点特征
2. 预测 t+1 期哪些城市会成为 prominent open-AI projects 的新 adopters

### 5.4.2 输入

1. 节点特征：城市属性、历史 open-AI 活跃度、历史采用状态
2. 图结构：城市—城市协作边与边权

### 5.4.3 输出

1. next-adopter probability
2. model performance
3. examples of correctly and incorrectly predicted cities

### 5.4.4 中文说明

更适合的轻量定义是：

某城市在 t+1 期是否会成为某个尚未采用的 prominent open-AI project 的新 adopter

或者更进一步，按城市级聚合：

某城市在 t+1 期是否会新增 adopted 任一 prominent open-AI project

建议用后者的轻量版本，因为更稳、更容易实现，也更符合 notebook 可运行性要求。

# 6. Include Required Notebook Sections

## 6.1 Introduction

### 6.1.1 英文版

The introduction should frame the project around the idea that open-AI production appears digitally distributed, yet the creation, collaboration, and adoption of prominent open-AI projects may still be highly uneven across global cities.

It should also explain that, rather than focusing on one narrowly pre-defined technology family, this project studies a broader ecosystem of prominent open-AI projects that have already achieved visible diffusion on GitHub and/or Hugging Face.

### 6.1.2 中文说明

Introduction 需要围绕“高影响 open-AI 项目生态”展开。

建议按下面四段写：

第一段，说明开放 AI 看似“去地理化”，但其创造、协作和采用在全球城市间可能高度不均衡。
第二段，回顾至少 3 篇可信文献，分别覆盖：

1. GitHub / 开源协作的空间集聚
2. 数字协作与距离/时区/组织摩擦
3. 开放 AI 平台的不平等与核心—边缘结构

第三段，指出现有研究往往聚焦单一平台或单一技术对象，而你关注的是：

1. prominent open-AI projects 的整体生态
2. 城市在其中的角色、采用速度与传播

第四段，引出本文的三个贡献：

1. 识别城市 roles
2. 测量高影响项目的 adoption lag
3. 解释并预测下一波 adopter 城市

同时要记得，References 必须是真实、可信来源，不能用 LLM 生成虚假文献。

## 6.2 Research Questions

### 6.2.1 Main research question

**How do global cities participate in the creation and use of prominent open-AI projects, and what factors shape the diffusion of these projects across the global urban system?**

### 6.2.2 Sub-questions

1. **What distinct roles do global cities play in the ecosystem of prominent open-AI projects, such as originators, collaboration hubs, bridge cities, and late adopters?**
2. **Which city characteristics are associated with innovation-oriented roles and faster adoption within the ecosystem of prominent open-AI projects?**
3. **Can the GitHub city collaboration network help predict which cities will become the next adopters of prominent open-AI projects?**

## 6.3 Data

### 6.3.1 英文版框架

The Data section should describe three layers of data:

1. Platform data from GitHub and Hugging Face, used to identify prominent open-AI projects and city-level activity;
2. City definition and matching data, used to map users, organisations, and projects into a unified global urban system;
3. City attribute data, used to explain variation in city roles and adoption speed.

It should also explain the filtering logic for “prominent open-AI projects,” the city-matching procedure, temporal aggregation to months, and the construction of project-level adoption events and lag variables.

### 6.3.2 中文说明

这一部分要重点把新的数据逻辑说清楚。

#### 6.3.2.1 数据源 1：平台数据

1. GitHub / GH Archive / GitHub API
2. Hugging Face Hub API

作用：

1. 识别与 open-AI 相关的项目
2. 通过 stars、downloads、forks、likes、visits 等门槛筛选出 prominent projects
3. 构建城市层创新、协作与采用指标

#### 6.3.2.2 数据源 2：城市定义与空间匹配数据

1. OECD FUA / GHS Urban Centre
2. 城市名称、国家、时区、经纬度

作用：

1. 将用户、组织、仓库、模型统一映射到城市层

#### 6.3.2.3 数据源 3：城市属性数据

1. population
2. education
3. income
4. research capacity
5. digital infrastructure

作用：

1. 用于解释城市 roles 与 adoption speed 差异

#### 6.3.2.4 预处理重点

Data 部分应明确说明以下步骤：

第一，如何定义 “open-AI-related projects”。
第二，如何设置 prominence threshold。
第三，如何做 location 清洗与城市映射。
第四，如何把时间聚合到月。
第五，如何构建三类核心数据表：

1. city_attributes
2. city_collaboration_edges
3. city_project_adoption_events

#### 6.3.2.5 分析单位说明

新的三层分析单位现在应写成：

1. 城市：用于 K-means、XGBoost
2. 城市—城市协作边：用于网络分析、GraphSAGE
3. 城市—项目—月度采用事件：用于 adoption-lag regression、GraphSAGE 标签构造

#### 6.3.2.6 变量表重点

变量表建议包括：

1. innovation indicators
2. collaboration indicators
3. bridge/network indicators
4. project-level adoption indicators
5. project-level lag variables
6. city attributes

同时要避免：

1. 直接把 ID 列拿来分析
2. 错把类别变量当成数值变量

这些都在作业说明里被列为常见问题。

## 6.4 Methodology

### 6.4.1 英文版框架

The methodology should explain that, after constructing city-level indicators, the project begins with an exploratory data analysis (EDA) to assess data quality, examine variable distributions and correlations, and reveal preliminary spatial and temporal patterns. Building on these findings, the project then combines clustering, regression, tree-based modelling, and graph neural networks to study city roles, adoption speed, explanatory patterns, and network-based adoption prediction in the ecosystem of prominent open-AI projects.

### 6.4.2 中文说明

Methodology 现在应按下面这条顺序写：

#### 6.4.2.1 Step 1. Project filtering and city-level indicator construction

1. 识别与 open-AI 相关且达到传播门槛的 prominent projects
2. 做城市映射
3. 构建创新、协作、桥梁、采用、lag 等指标
4. 尽量采用 rate 而非 raw count

#### 6.4.2.2 Step 2. Exploratory Data Analysis (EDA)

EDA 在正式建模之前完成，目的是理解数据质量、发现分布特征、检验变量可用性、并为后续方法提供初步依据。

##### 2a. 数据质量检查

1. 检查三张核心表的维度、缺失值比例、数据类型
2. 标记并处理异常值（如某城市 origination_count 异常高是否合理）
3. 检查类别变量与数值变量是否正确分类，避免把 ID 列或类别变量误用为数值变量
4. 确认 prominence threshold 筛选后的样本量是否足够（城市数 ≥ 100、项目数、采用事件数）

##### 2b. 单变量分布

1. 对关键数值变量画直方图 / KDE：origination_count、adoption_count、avg_lag、degree、betweenness、population、education_rate、income_per_capita 等
2. 检查是否需要 log 变换（如 adoption_lag、population 等通常高度右偏）
3. 对类别变量画频率条形图：region、timezone、lag_group
4. 描述性统计汇总表：count、mean、std、min、25%、50%、75%、max

##### 2c. 双变量关系与相关性

1. 数值变量相关性矩阵 + 热力图（Pearson 或 Spearman）
2. 重点关注输入变量之间的多重共线性（若两变量相关系数 > 0.8，考虑合并或剔除）
3. 关键散点图：
   - origination_rate vs. population（创新是否与城市规模正相关）
   - avg_lag vs. network centrality（网络位置是否与采用速度相关）
   - adoption_count vs. education_rate（教育水平是否与采用量相关）
4. 箱线图：按 region 或 cluster（如有先验分组）拆分关键变量分布

##### 2d. 空间分布与地理格局

1. 全球地图：按城市标注 origination_count / adoption_count 的气泡大小
2. 区域汇总条形图：按洲或国家分组统计城市数量、项目创造数量、采用数量
3. 初步判断是否存在明显的核心—边缘空间格局

##### 2e. 时间趋势

1. 月度时间序列：每月全球新增 prominent projects 数量、新增 adoption events 数量
2. 区域层面时间趋势对比：北美 / 欧洲 / 东亚 / 其他地区的活跃度月度变化
3. 检查是否存在季节性或突变点

##### 2f. 网络初步描述

1. 协作网络基本统计：节点数、边数、平均度、密度、连通分量数
2. 度分布图：检查是否近似幂律分布
3. 网络可视化（小规模采样或 top 城市子图）

##### 2g. 对后续建模的指导

1. 确认哪些变量需要标准化（K-means 输入必须标准化）
2. 确认哪些变量需要 log 变换（Adoption-lag regression 的因变量）
3. 确认是否需要降维或剔除高共线性变量（XGBoost 和 regression 的输入）
4. 确认图结构是否足够稠密以支撑 GraphSAGE 训练
5. 记录 EDA 中发现的关键模式，留待 Discussion 部分对照模型结果讨论

#### 6.4.2.3 Step 3. K-means for city roles

1. 使用城市层指标识别 roles
2. 输出 originators、collaboration hubs、bridge cities、late adopters 等 cluster

#### 6.4.2.4 Step 4. Adoption-lag regression

1. 在 城市—项目 层面计算 adoption lag
2. 分析哪些因素与更快项目采用相关
3. 可加入项目固定效应或项目控制变量

#### 6.4.2.5 Step 5. XGBoost for explanatory modelling

1. 解释哪些城市特征与 innovation-oriented roles 和 faster adoption 相关
2. 用 SHAP 做辅助解释

#### 6.4.2.6 Step 6. GraphSAGE for next-wave adopter prediction

1. 基于城市协作网络与节点特征
2. 预测哪些城市会在下一期成为 prominent project 的新 adopter

#### 6.4.2.7 Step 7. Optional case-study visualisation

1. 选 1–2 个技术家族或代表项目
2. 展示更具体的扩散时间线、空间地图、网络路径

## 6.5 Expected Results and Discussion

### 6.5.1 中文说明

期望的结果可能包括以下几个方面。

### 6.5.2 小节 1：Spatial concentration of prominent open-AI projects

预期展示：

1. 全球地图
2. 哪些城市在高影响 open-AI 项目中更活跃
3. 创造、协作、采用活动的空间不均衡

### 6.5.3 小节 2：Distinct city roles in the ecosystem

预期展示：

1. K-means cluster 结果
2. originators、collaboration hubs、bridge cities、late adopters 的角色画像

### 6.5.4 小节 3：Project-level adoption lag and diffusion speed

预期展示：

1. prominent projects 的全球首次出现分布
2. 城市对这些项目的 lag 分布
3. 哪些因素与更短 lag 相关

### 6.5.5 小节 4：City characteristics and explanatory patterns

预期展示：

1. XGBoost feature importance
2. SHAP summary plot
3. 高学历、高收入、科研能力、数字基础设施、网络中心性与创新/采用能力的关系

### 6.5.6 小节 5：Predicting next-wave adopters

预期展示：

1. GraphSAGE 的性能
2. 哪些城市在下一期最可能 adopted 新的 prominent projects
3. 预测正确与错误的案例

### 6.5.7 小节 6：Case-study visualisation

预期展示：

1. 1–2 个具体技术家族或代表项目的扩散时间线
2. 地图、网络图或 Sankey / timeline 图
3. 用于更直观地演示传播过程

### 6.5.8 小节 7：Critical reflection

建议主动讨论：

1. prominent projects 的筛选规则可能引入平台偏差
2. 不同类型项目的扩散机制并不完全相同
3. adoption lag 在跨项目比较时受项目异质性影响
4. GraphSAGE 预测的是 adopter，而不是 originator emergence

## 6.6 Expected Conclusion

### 6.6.1 中文说明

Expected Conclusion 现在应围绕“高影响 open-AI 项目生态”来收束。

### 6.6.2 第一层：城市角色

全球城市在 prominent open-AI projects 的生态中并不扮演同质角色。
有些城市更像 originators，有些是 collaboration hubs，有些是 bridge cities，而更多城市是 late adopters。

### 6.6.3 第二层：扩散速度

高影响 open-AI 项目的扩散并不是随机发生的。
不同城市对这些项目的 adoption lag 有明显差异，说明传播速度在全球城市体系中高度不均衡。

### 6.6.4 第三层：解释因素

城市的教育、收入、科研能力、数字基础设施和网络位置等因素，可能与 innovation-oriented roles 和 faster adoption 相关。

### 6.6.5 第四层：预测价值

GitHub 城市协作网络对“下一波 adopter 城市”的识别具有预测价值，因此网络结构不仅能描述协作关系，也能帮助理解技术扩散。

### 6.6.6 第五层：future work

1. 可进一步把 PatentsView 引入为 formal innovation validation layer
2. 可把 case-study 技术家族扩展成系统性对比研究
3. 可进一步比较不同项目类型的扩散机制差异
