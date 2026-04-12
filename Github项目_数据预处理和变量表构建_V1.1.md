# 1. 数据预处理：数据预处理的重点是什么？怎么构建？长什么样？

从原始平台数据出发，经过哪些步骤，最终把它整理成可用于 K-means、Adoption-lag regression、XGBoost、GraphSAGE 的分析数据？

原文里列了 5 步。可以把它理解成一条数据流水线：

**原始平台对象**  
→ **筛项目**  
→ **清位置**  
→ **映射到城市**  
→ **统一时间粒度**  
→ **生成三张核心分析表**

## 第一步：如何定义 “open-AI-related projects”

它是一个**项目筛选规则**。  
意思是：从 GitHub 仓库、Hugging Face 模型/数据集/Spaces 里，先挑出“和 open-AI 有关”的对象。

否则你原始数据里会混入很多不相关内容：
- 普通软件仓库
- 纯数据工程工具
- 与 AI 无关的 web 项目
- 一般性 Python 库

你研究的是 **open-AI projects**，所以必须先定义“什么算 open-AI-related”。

### 具体如何构建？
最常见的是“规则筛选 + 人工复核”。

### 做法 A：关键词 / 标签规则
从这些字段里识别：
- 项目名
- description
- README
- tags / topics
- model card / dataset card
- Hugging Face pipeline tags

例如你可能保留包含这些线索的对象：
- `llm`
- `transformer`
- `diffusion`
- `multimodal`
- `agent`
- `rag`
- `text-generation`
- `image-generation`
- `embedding`
- `open-weight`

同时排掉明显不相关的对象。

### 做法 B：平台原生类别
例如 Hugging Face 本身就有：
- task tags
- pipeline tags
- model types

这些比单纯关键词更稳一点。

### 做法 C：种子名单 + 扩展
先人工整理一批你确信属于 open-AI 的代表对象，再根据它们的标签和社区关系向外扩展。

### 举个例子
假设有 5 个 GitHub/HF 对象：

| object_name | platform | description/tag | 是否保留 |
|---|---|---|---|
| `awesome-llm-agents` | GitHub | agent, llm | 保留 |
| `stable-audio-open` | HF | audio-generation | 保留 |
| `react-dashboard-kit` | GitHub | frontend dashboard | 删除 |
| `embedding-benchmark` | GitHub | embedding, evaluation | 保留 |
| `weather-scraper` | GitHub | scraping utility | 删除 |

这里“保留 / 删除”的依据就是你的 **open-AI-related definition**。

### 最后长什么样？
你最终最好有一张“项目筛选结果表”：

| project_id | platform | project_name | open_ai_related | evidence | confidence |
|---|---|---|---:|---|---|
| gh_001 | GitHub | awesome-llm-agents | 1 | topic=agent; readme=llm | high |
| hf_038 | HF | stable-audio-open | 1 | pipeline=audio-generation | high |
| gh_105 | GitHub | react-dashboard-kit | 0 | no AI terms | low |

这张表通常不会直接进最终模型，但它是所有后续分析的入口。

## 第二步：如何设置 prominence threshold

### 这具体是什么？
它是一个**传播门槛 / 影响力门槛**。  
意思是：即使一个对象和 open-AI 有关，也不代表它值得纳入主分析。现在研究的是prominent open-AI projects，所以还必须定义“什么叫 prominent”。

### 为什么需要这一步？
因为如果不设门槛，会把大量：

- 只存在几天
- 几乎没人看
- 没有任何扩散痕迹
- 完全长尾的小项目

都纳入。这样会让：
- adoption 定义很噪
- lag 没意义
- 图网络太稀疏
- narrative 变散

### 具体如何构建？
通常有三种方式。

### 方式 A：绝对门槛
例如：
- GitHub stars ≥ 500
- forks ≥ 50
- Hugging Face downloads ≥ 10,000
- likes ≥ 100

优点是简单。  
缺点是不同平台和不同项目类型之间可能不公平。

### 方式 B：相对门槛
例如：
- 进入同类对象的前 10%
- 某月新增传播量进入前 20%

优点是更稳。  
缺点是解释略复杂。

### 方式 C：组合门槛
这是最实用的。

例如一个项目只要满足：
- `open_ai_related = 1`
- 并且在 GitHub 或 HF 至少一个平台上达到传播门槛
- 再加一个“最小活跃度”条件

例如：
- GitHub：stars ≥ 300 或 forks ≥ 30
- HF：downloads ≥ 5000 或 likes ≥ 50
- 且项目在 202201–202512 内有活动或采用事件

### 举个例子
| project_name | stars | forks | hf_downloads | 是否 prominent |
|---|---:|---:|---:|---:|
| Project A | 2200 | 180 | 0 | 是 |
| Project B | 80 | 5 | 45000 | 是 |
| Project C | 90 | 8 | 600 | 否 |
| Project D | 350 | 25 | 7000 | 是 |

这里你会看到：  
prominent 不一定只靠 GitHub，也可以靠 Hugging Face 扩散强度。

### 最后长什么样？
你会得到一张“prominent projects master list”：

| project_id | platform | project_name | stars | forks | downloads | prominent_flag |
|---|---|---|---:|---:|---:|---:|
| gh_001 | GitHub | awesome-llm-agents | 2200 | 180 | null | 1 |
| hf_038 | HF | stable-audio-open | null | null | 45000 | 1 |
| gh_105 | GitHub | small-local-demo | 27 | 1 | null | 0 |

主分析只保留 `prominent_flag = 1` 的对象。

## 第三步：如何做 location 清洗与城市映射

### 这具体是什么？
这是把平台上的“人 / 组织 / 项目”的位置文本，变成统一城市单位的过程。

原始位置通常非常乱，比如：
- `London`
- `London, UK`
- `LDN`
- `SF Bay Area`
- `Remote`
- `Earth`
- `Shenzhen/HK`
- 空白

你必须把这些文本尽可能规范化，然后映射到统一的城市体系。

### 为什么需要？
因为你的研究问题是：
- 全球城市 roles
- 城市 adoption
- 城市网络扩散

所以**城市是核心分析单位**。  
如果 location 不清洗，后面所有城市层分析都会不可靠。

### 具体如何构建？

### Step 1：收集位置来源
可能的来源包括：
- GitHub user profile location
- GitHub organization location
- repository owner location
- Hugging Face user / org location
- 相关元数据中的国家/城市字段

### Step 2：文本标准化
例如：
- 去大小写差异
- 去 emoji、无关符号
- 统一国家缩写
- 把 `SF` 规范成 `San Francisco`
- 把 `NYC` 规范成 `New York`

### Step 3：去掉无效位置
例如：
- `remote`
- `worldwide`
- `earth`
- `internet`
- 空值

### Step 4：地理编码 / 词典匹配
把位置字符串匹配到：
- 城市名
- 经度纬度
- 国家
- 都市区/FUA

### Step 5：打置信度标签
例如：
- high：明确匹配到单一城市
- medium：模糊但基本可信
- low：过于模糊或冲突

主分析最好只保留 high，或 high + 部分 medium。

### 举个例子
| raw_location | cleaned_location | matched_city | country | confidence |
|---|---|---|---|---|
| `London, UK` | London UK | London | UK | high |
| `SF Bay Area` | San Francisco Bay Area | San Francisco | USA | medium |
| `Remote` | null | null | null | low |
| `Shenzhen/HK` | Shenzhen Hong Kong | Shenzhen | China | low |

### 最后长什么样？
你会得到一张“location mapping table”：

| entity_id | entity_type | raw_location | matched_city | country | lat | lon | confidence |
|---|---|---|---|---|---:|---:|---|
| user_1 | github_user | London, UK | London | UK | 51.5074 | -0.1278 | high |
| org_5 | hf_org | SF Bay Area | San Francisco | USA | 37.7749 | -122.4194 | medium |

这张表会被后面所有城市层表使用。

## 第四步：如何把时间聚合到月度

### 这具体是什么？
这是把原始时间戳，比如：
- repo created at
- first release date
- first adoption event time
- collaboration event timestamp

统一转成月度，例如：
- 202401
- 202402
- 202503

- adoption lag 用月度算
- GraphSAGE 用 t 到 t+1 的月度预测
- 项目采用事件按月度记录

如果不统一时间粒度，后面所有表都对不上。

### 具体如何构建？
假设原始时间戳是 `2025-05-17 13:24:00`，你把它映射成：

- 年 = 2025
- 月 = 5

最终得到 `202502`。

### 最后长什么样？
原始事件表里的所有时间字段都会多出一列：

| event_id | city | project | event_type | timestamp | months |
|---|---|---|---|---|---|
| e1 | London | Project A | first_release | 2024-02-10 | 202402 |
| e2 | Berlin | Project A | first_adoption | 2024-07-02 | 202407 |

## 第五步：如何构建三类核心数据表

这一步最重要。你前面所有清洗和匹配，最后都要落到这三张主表上。  
这三张表分别服务不同模型和分析场景。

## 5.1 `city_attributes`

## 它是什么？
这是**城市层总表**。  
每一行是一个城市，包含：

- 静态城市属性
- 聚合后的平台活动指标
- 网络指标
- adoption 汇总指标

它主要服务：
- **K-means**
- **XGBoost**
- 一部分描述性分析

### 怎么构建？
把这些信息按城市聚合后合并：

### 来自外部城市数据
- population
- income
- education
- research_capacity
- digital_infrastructure

### 来自平台项目生态
- innovation_count
- adoption_count
- collaboration_count
- avg_adoption_lag
- degree
- betweenness

### 它长什么样？
| city | population | education_rate | income_pc | innovation_count | adoption_count | avg_lag | degree | betweenness |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| London | 9500000 | 0.52 | 47000 | 34 | 118 | 1.8 | 0.67 | 0.21 |
| Berlin | 3800000 | 0.44 | 39000 | 15 | 74 | 2.4 | 0.49 | 0.17 |

## 5.2 `city_collaboration_edges`

### 它是什么？
这是**城市—城市协作边表**。  
每一行表示某一月里两个城市之间是否有协作，以及协作强度多大。

它主要服务：
- **网络分析**
- **GraphSAGE**
- bridge / centrality 指标构造

### 怎么构建？
你先识别项目级或用户级协作事件，再向上聚合到城市对。

例如：
- London 的贡献者和 Berlin 的贡献者共同参与过同一个 prominent project
- 某个 repo 的 owner 在 London，协作者在 Toronto
- 某月内共同贡献次数累计为 18

把这些聚成城市对边。

### 它长什么样？
| source_city | target_city | month | edge_weight | shared_projects | collaboration_events |
|---|---|---|---:|---:|---:|
| London | Berlin | 202502 | 18 | 6 | 42 |
| London | Toronto | 202502 | 9 | 3 | 17 |
| Singapore | Seoul | 202502 | 12 | 4 | 25 |

这里：
- `edge_weight` 可以是你最终给 GraphSAGE 用的权重
- `shared_projects` 和 `collaboration_events` 是构造权重的原始量

## 5.3 `city_project_adoption_events`

### 它是什么？
这是**城市—项目—月度采用事件表**。  
每一行表示：

> 某城市在某月，对某项目是否已采用、是否在这一月首次采用，以及与项目全球首次出现相比晚了多久。

它主要服务：
- **Adoption-lag regression**
- **GraphSAGE 标签构造**
- 扩散时间线与地图

### 怎么构建？
你先定义“adoption”是什么。比如：
- 某城市的用户/组织首次参与某项目
- 某城市首次 fork / download / deploy / create derivative / contribute
- 某城市首次在 HF / GitHub 上出现与该 prominent project 相关的采用信号

然后找出：
- 项目全球首次出现月份 `global_origin_month`
- 城市首次采用月份 `city_first_adoption_month`
- lag = 两者差多少个月份

### 它长什么样？
| city | project_id | month | adopted | first_adoption | global_origin_month | city_first_adoption_month | lag |
|---|---|---|---:|---:|---|---|---:|
| London | proj_A | 202401 | 1 | 1 | 202401 | 202401 | 0 |
| Berlin | proj_A | 202402 | 0 | 0 | 202401 | null | null |
| Berlin | proj_A | 202403 | 1 | 1 | 202401 | 202403 | 2 |

这个表是你做扩散分析时最关键的一张。

# 2. 变量表：变量表的重点是什么？怎么构建？长什么样？

这里的“变量表”不是数据本身，而是一张**解释用的清单**。  
作用是让老师或读者迅速看懂：

- 你模型里到底用了哪些变量
- 每个变量是什么意思
- 是怎么计算出来的
- 属于哪一类

评分标准明确提到，高分的数据部分应有一张表描述所选变量，帮助读者理解分析变量。

### 变量表一般长什么样？
最常见结构是：

| Variable | Level | Type | Description | Construction / Notes |
|---|---|---|---|---|

其中：
- `Variable`：变量名
- `Level`：城市层 / 城市对层 / 城市项目层
- `Type`：数值、二元、类别
- `Description`：变量含义
- `Construction / Notes`：怎么来的、是否标准化

## 下面解释你列出的每一类变量

## 2.1 innovation indicators

### 这是什么？
用来衡量一个城市在 prominent open-AI projects 生态里“创造 / 发起 / 提出新项目”的能力。

### 可以包括哪些？
例如：

- `origination_count`  
  某城市作为项目最早出现地的项目数量

- `origination_rate`  
  上述数量除以人口或开发者规模

- `new_project_release_count`  
  某城市在研究期内发起的新 prominent projects 数量

- `innovation_share`  
  某城市在全球所有 prominent projects 中占的 origination 比例

### 举例
| Variable | Level | Description |
|---|---|---|
| origination_count | city | number of prominent open-AI projects first associated with a city |
| origination_rate | city | origination_count normalised by population |

## 2.2 collaboration indicators

### 这是什么？
用来衡量一个城市在项目生态中的**协作活跃程度**。

### 可以包括哪些？
- `collaboration_count`
- `collaboration_rate`
- `shared_projects_count`
- `cross_city_collaboration_ratio`

### 举例
| Variable | Level | Description |
|---|---|---|
| collaboration_count | city | total number of cross-city collaboration events involving the city |
| collaboration_rate | city | collaboration_count normalised by population |
| shared_projects_count | city | number of prominent projects co-worked on with other cities |

## 2.3 bridge/network indicators

### 这是什么？
用来衡量一个城市在网络中的**位置和桥梁作用**。

### 可以包括哪些？
- `degree`
- `weighted_degree`
- `betweenness`
- `eigenvector_centrality`
- `community_id`
- `bridge_score`

### 举例
| Variable | Level | Description |
|---|---|---|
| weighted_degree | city | sum of collaboration edge weights connected to the city |
| betweenness | city | extent to which the city lies on shortest paths between other cities |
| bridge_score | city | indicator of cross-community linkage role |

这些变量特别重要，因为：
- K-means 会用它们识别 roles
- XGBoost 会用它们解释 innovation/adoption
- GraphSAGE 的图结构也和它们相关

## 2.4 project-level adoption indicators

### 这是什么？
用来衡量某城市对 prominent projects 的采用情况。

注意，这类变量通常是**城市—项目层**或聚合后城市层。

### 可以包括哪些？
- `adopted`
- `first_adoption`
- `adoption_count`
- `adoption_rate`
- `fast_adopter_flag`

### 举例
| Variable | Level | Description |
|---|---|---|
| adopted | city-project-month | whether the city had adopted the project by the month |
| first_adoption | city-project-month | whether the city first adopted the project in that month |
| adoption_count | city | number of prominent projects adopted by the city |
| fast_adopter_flag | city-project | whether the city adopted within the first 1–2 months after project origin |

## 2.5 project-level lag variables

### 这是什么？
这是最直接刻画“扩散速度”的变量。  
它们描述：

> 某个城市相对于某个项目的全球首次出现，晚了多久才采用。

### 可以包括哪些？
- `adoption_lag`
- `log_adoption_lag`
- `relative_lag_percentile`
- `lag_group`

### 举例
| Variable | Level | Description |
|---|---|---|
| adoption_lag | city-project | number of months between global origin and city first adoption |
| log_adoption_lag | city-project | log-transformed adoption lag |
| lag_group | city-project | early / mid / late adopter category |

这类变量主要给：
- **Adoption-lag regression**
- **XGBoost**

## 2.6 city attributes

### 这是什么？
这是城市外部属性变量，用来解释为什么不同城市有不同角色和扩散速度。

### 可以包括哪些？
- `population`
- `education_rate`
- `income_per_capita`
- `research_capacity`
- `digital_infrastructure`
- `timezone`
- `region`

### 举例
| Variable | Level | Description |
|---|---|---|
| population | city | city population |
| education_rate | city | share of population with higher education |
| income_per_capita | city | city-level income or GDP per capita proxy |
| research_capacity | city | proxy for research institutions or R&D strength |

这些变量主要给：
- **XGBoost**
- **Adoption-lag regression** 中的控制变量
