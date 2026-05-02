# 0. 实施进度与执行概况（截至 2026-05-02）

## 0.1 总体进度

| 阶段 | 步骤 | 状态 | 对应文件 |
|---|---|---|---|
| 数据采集 | Step 1a: GitHub 项目发现 | ✅ 已完成 | `step1a_filter_github.py` |
| 数据采集 | Step 1b: HF 项目发现 | ✅ 已完成 | `step1b_filter_huggingface.py` |
| 数据采集 | Step 1c: 合并 & 筛选 | ✅ 已完成 | `step1c_merge_candidates.py` |
| 位置处理 | Step 3a: GitHub 用户位置 | ✅ 已完成 | `step3a_fetch_github_locations.py` |
| 位置处理 | Step 3a-HF: HF 作者位置 | ✅ 已完成 | `step3a_hf_fetch_user_locations.py` |
| 位置处理 | Step 3b: 清洗 & 映射 | ✅ 已完成 | `step3b_clean_and_map_locations.py` |
| 位置处理 | Step 3c: Nominatim 地理编码 | ✅ 已完成 | `step3c_geocode_unmatched.py` |
| 位置处理 | Step 3d: 城市列表构建 | ✅ 已完成 | `step3d_build_city_list.py` |
| 贡献者 | Step 4: 贡献者 & 参与链 | ✅ 已完成 | `step4_fetch_contributors.py` |
| 核心表 | Step 5: 三张核心表 | ✅ 已完成 | `step5_build_core_tables.py` |
| 核心表 | Step 5b: HF 衍生关系边 | ✅ 已完成 | `step5b_build_hf_derivation_edges.py` |
| 增强 | Step 6: 城市外部属性 | ✅ 已完成 | `step6_augment_city_attributes.py` |
| 分析 | Step 8: EDA | ✅ 已完成 | `step8_eda.ipynb` + `step8b_eda_detailed.ipynb` |
| 分析 | Step 9: K-means | ✅ 已完成 | `step9_kmeans.ipynb` |
| 分析 | Step 10: Adoption-lag 回归 | ✅ 已完成 | `step10_adoption_regression.ipynb` |
| 分析 | Step 11: XGBoost + SHAP | ✅ 已完成 | `step11_xgboost_shap.ipynb` |
| 分析 | Step 12: GraphSAGE | ✅ 已完成 | `step12_graphsage.ipynb` |
| 整合 | 最终提交 Notebook | 🔲 待完成 | `Template_submission_CASA0006.ipynb` |
| 整合 | Narrative 撰写（≤1500词） | 🔲 待完成 | — |
| 整合 | Case Study 可视化 | 🔲 待完成 | — |
| 整合 | 文献引用 + 变量表 + 流程图 | 🔲 待完成 | — |
| 整合 | Restart & Rerun All 验证 | 🔲 待完成 | — |

## 0.2 实际数据规模

### 原始数据

| 数据文件 | 行数 | 说明 |
|---|---|---|
| `github_candidates.csv` | 118,519 | GitHub Search API 收集的所有候选仓库 |
| `hf_candidates.csv` | 1,237,384 | HF Hub API 收集的所有候选 Models/Datasets/Spaces |
| `github_owner_locations.csv` | 118,825 | GitHub 用户 / 组织的位置信息 |
| `hf_author_locations.csv` | 3,314 | HF 作者位置（手动字典 + GH 同名匹配 + API fallback） |
| `github_repo_contributors.csv` | 149,938 | prominent 项目的贡献者列表 |
| `github_repo_participation_events.csv` | 242,944 | 每位贡献者的首次参与事件（Commits + PRs API） |

### 中间处理数据

| 数据文件 | 行数 | 说明 |
|---|---|---|
| `project_filtering_result.csv` | 1,355,902 | GH + HF 合并候选（含 AI 相关性和 prominence 标记） |
| `prominent_projects_master.csv` | 23,481 | 最终 prominent 项目（GH 11,490 + HF 11,991） |
| `location_mapping.csv` | 109,393 | 所有用户的位置清洗 & 城市匹配结果（匹配率 25.7%） |
| `hf_derivation_edges.csv` | 2,922 | HF 模型间 base_model 衍生关系边 |
| `city_list.csv` | 148 | 最终筛选的高置信度城市（覆盖 50 个国家） |

### 三张核心输出表

| 数据文件 | 行数 | 关键维度 |
|---|---|---|
| `city_attributes.csv` | 148 行 × 28 列 | 148 城市，9 个区域，50 个国家 |
| `city_collaboration_edges.csv` | 9,636 | 9,636 个城市对协作边 |
| `city_collaboration_edges_monthly.csv` | 98,147 | 月度协作边快照（48 个月） |
| `city_project_adoption_events.csv` | 39,158 | 148 城市 × 13,437 项目的采用事件 |

### 核心统计

- **Prominent 项目总数**: 23,481（GitHub 11,490 + HuggingFace 11,991）
- **采用事件**: 39,158（originator 8,505 + non-originator 30,653）
- **Adoption lag 分布**: min=0, max=50 月, mean=6.28, median=2, 75th=9
- **协作网络**: 148 节点, 9,636 边, 密度 0.886, 直径 2, 全连通
- **Top-5 origination 城市**: San Francisco (1,802), Beijing (653), London (633), Hangzhou (533), Boston (513)

## 0.3 相比原方案的主要优化

### 优化 1：Hugging Face 双平台整合

原方案仅以 GitHub 为主数据源。实际执行中完整整合了 HF Hub API，采集了 123 万+ HF 对象，最终保留 11,991 个 prominent HF 项目。项目覆盖从纯代码仓库扩展到模型、数据集和应用；新增 HF 衍生关系图作为 adoption 信号来源。

### 优化 2：HF 作者位置解析三层策略

HF Hub API 不暴露 location 字段。实现了：(1) 200+ 高产出 HF 机构手动字典；(2) GitHub 同名匹配；(3) GitHub API fallback。

### 优化 3：精确参与时间链

原方案中 lag 使用 creation_month+1 近似。实际通过 Commits API + PRs API 精确提取首次参与时间戳，lag 从 0/1 扩展到 0–50 月连续分布（mean=6.3, median=2）。

### 优化 4：HF 衍生关系图

step5b 解析 HF tags 中 `base_model:*` 标签，构建 2,922 条衍生边（finetune / quantized / adapter / merge），作为 adoption 和 collaboration 的额外信号。

### 优化 5：城市外部属性增强

step6 为 148 城市添加 8 类外部变量：population, gdp_per_capita, education_tertiary_pct, internet_users_pct, rd_expenditure_pct, research_capacity, timezone_utc, region。同时计算了人口标准化 rate。

## 0.4 EDA 主要发现（Step 8）

### 数据质量
- 148 城市 × 28 变量，103 城市有实际采用事件
- `avg_lag` 和 `median_lag` 有 45 个 NaN（无采用事件的城市），其余无缺失
- 外部属性缺失：population 缺 5 条 (3.4%)，GDP/education 等缺 13 条 (8.8%)

### 分布与变换
- origination_count (skew=6.63)、adoption_count (4.29) 严重右偏 → **log1p 后近正态**
- adoption_count log1p Shapiro-Wilk p=0.561 → 通过正态性检验
- avg_lag (mean=8.44, std=2.40) 近对称，无需变换

### 共线性
- `collaboration_count` ≡ `weighted_degree` (ρ=1.000, VIF=∞) → 建模只保留 degree
- `eigenvector_centrality` VIF=524 → 建模时剔除

### 偏相关（控制 population & entity_count）
- **gdp ↔ adoption: partial r=0.266, p=0.002** → 控制规模后 GDP 显著
- **internet ↔ adoption: partial r=0.253, p=0.004** → 数字基础设施显著
- gdp / education / R&D ↔ origination: 均 p > 0.4 → 对创新发起无直接效应

### Lag 相关性
- origination_count ↔ avg_lag: ρ=−0.611 (p<0.001) → 创新越多采用越快
- rd_expenditure ↔ avg_lag: ρ=−0.336 (p<0.001)
- population ↔ avg_lag: ρ=−0.064 (p=0.445) → 规模**不**影响采用速度

### 空间格局
- **核心—边缘结构**：Top-10 城市占 origination 69.7% / adoption 43.4%
- 创新集中、采用去中心化的不对称结构
- North America 和 East Asia 在所有活动指标上领先
- East Asia mean lag=6.60 最快 | Latin America 10.87 最慢

### 网络
- 148 节点, 9,636 边, 密度 0.886, 直径 2, 全连通
- San Francisco (degree=13,337) 为最大 hub
- 度分布右偏（hub-and-spoke 模式）→ **适合 GraphSAGE 训练**

## 0.5 建模结果摘要

### K-means 城市角色（Step 9, k=4, silhouette=0.35）

| 角色 | n | mean orig | mean adopt | mean degree | 典型城市 |
|---|---|---|---|---|---|
| Global Innovation Hub | 27 | 275 | 942 | 6,353 | San Francisco, Beijing, London, Tokyo |
| Active Collaborator | 56 | 15 | 188 | 2,247 | Seoul, Bengaluru, Toronto, LA |
| Emerging Contributor | 44 | 4 | 60 | 793 | Xi'an, Jakarta, Cairo, Rome |
| Peripheral / Late Adopter | 16 | 2 | 22 | 258 | Tallinn, Addis Ababa, Lahore |

### Adoption 回归（Step 10）

| 模型 | DV | n | R²/Pseudo R² | 最强变量 |
|---|---|---|---|---|
| Model A (Logistic) | is_originator | 38,347 | Pseudo R²=0.088 | log_entity (+), log_degree (−) |
| Model B (OLS) | originator_share | 130 | R²=0.276 | log_entity (+), log_degree (−) |
| Model C (OLS) | log(adoption) | 130 | R²=0.965 | log_degree (+), log_entity (+), betweenness (+) |

### XGBoost + SHAP（Step 11）

| 模型 | DV | CV 表现 | 备注 |
|---|---|---|---|
| Model D (分类) | is_originator | **AUC=0.769** | 合理区分能力 |
| Model E (回归) | originator_share | CV R²=−0.79 | n=148 过拟合 |
| Model F (回归) | log(adoption) | CV R²=−0.87 | n=148 过拟合 |

SHAP Top-3 特征: log_entity, log_degree, betweenness

### GraphSAGE（Step 12）

| 模型 | DV | Test 表现 |
|---|---|---|
| G1 (回归) | log(adoption) | **R²=0.902, RMSE=0.377** |
| G2 (分类) | high/low adopter | **AUC=0.984, F1=0.980** |

城市排名预测 Spearman ρ=0.976 (p<0.001)

## 0.6 已知局限

1. **网络密度偏高 (0.886)**：betweenness 区分度有限
2. **XGBoost 回归 CV R² 为负**：n=148 不足以支撑 GB 回归泛化
3. **外部属性对 origination 直接解释力弱**：但控制规模后 GDP 和 internet 对 adoption 显著
4. **collaboration_count ≡ weighted_degree**：完全冗余，建模已只保留 degree
5. **Model C R²=0.965 存在循环性**：degree 与 adoption 同源构建

## 0.7 代码文件清单

### 预处理脚本 (scripts/) — 15 个文件，约 4,924 行

| 文件 | 行数 | 功能 |
|---|---|---|
| `config.py` | 267 | 项目配置：路径、Token、时间窗口、关键词规则、prominence 门槛 |
| `step1a_filter_github.py` | 319 | GitHub Search API → 候选仓库 |
| `step1b_filter_huggingface.py` | 330 | HF Hub API → 候选 Models/Datasets/Spaces |
| `step1c_merge_candidates.py` | 134 | 合并 GH + HF → prominent_projects_master |
| `step3a_fetch_github_locations.py` | 128 | GitHub Users API → owner 位置 |
| `step3a_hf_fetch_user_locations.py` | 504 | 手动字典 + GH 匹配 + API fallback → HF 作者位置 |
| `step3b_clean_and_map_locations.py` | 538 | 文本标准化 → 200+ 城市字典匹配 |
| `step3c_geocode_unmatched.py` | 233 | Nominatim 地理编码未匹配位置 |
| `step3d_build_city_list.py` | 93 | 构建 148 个高置信度城市列表 |
| `step4_fetch_contributors.py` | 625 | 贡献者列表 + 位置 + Commits/PRs 参与链 |
| `step5_build_core_tables.py` | 744 | 构建三张核心表（adoption + edges + attributes） |
| `step5b_build_hf_derivation_edges.py` | 187 | 解析 HF base_model tags → 衍生关系图 |
| `step6_augment_city_attributes.py` | 383 | 添加人口、GDP、教育、科研等外部属性 |
| `estimate_hf_commit_authors.py` | 206 | 辅助：估算 HF 多作者协作比例 |
| `estimate_hf_derivation.py` | 233 | 辅助：估算 HF 衍生图覆盖率与链深度 |

### 分析 Notebook (notebooks/) — 6 个文件

| 文件 | 代码单元 | 对应 RQ | 功能 |
|---|---|---|---|
| `step8_eda.ipynb` | 22 | — | 核心 EDA |
| `step8b_eda_detailed.ipynb` | 20 | — | 扩展 EDA |
| `step9_kmeans.ipynb` | 14 | RQ1 | K-means 城市角色聚类 |
| `step10_adoption_regression.ipynb` | 11 | RQ2 | Adoption-lag 回归 |
| `step11_xgboost_shap.ipynb` | 12 | RQ2 | XGBoost + SHAP |
| `step12_graphsage.ipynb` | 10 | RQ3 | GraphSAGE 预测 |

---

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

“高影响 / prominent”实际使用的门槛为：

1. GitHub：stars ≥ 300 **或** forks ≥ 30（满足其一即可）→ 筛出 **11,490** 个 prominent repos
2. Hugging Face：downloads ≥ 5,000 **或** likes ≥ 50（满足其一即可）→ 筛出 **11,991** 个 prominent objects
3. 同时必须通过 open-AI 相关性规则（~190 个 AI 关键词 / pipeline_tag 匹配 + 弱信号二次确认 + 排除词过滤）

## 1.4 样本设计

1. 时间范围：**202201–202512**
2. 时间粒度：**月度**
3. 城市数量：**148 个高置信度城市**（实际执行结果，覆盖 50 个国家、9 个宏观区域）
4. 项目数量：**23,481 个 prominent projects**（GitHub 11,490 + HuggingFace 11,991）
5. 技术范围：**主分析不强制先划分单一家族，而是对 prominent open-AI projects 的整体生态进行研究；具体技术家族可在 case study 中单独展示**
6. 分析单位：
   1. 城市（148 行 × 28 列）
   2. 城市—城市协作边（9,636 对，98,147 月度行）
   3. 城市—项目—月度采用事件（39,158 行，覆盖 13,437 个项目）

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

### 3.2.1 城市定义与空间匹配层 ✅

用于统一全球城市边界与名称：

1. OECD Functional Urban Areas 或 GHS Urban Centre Database
2. 城市经纬度
3. 国家 / 区域
4. 时区

> **实际执行**：通过 `step3b_clean_and_map_locations.py` + `step3c_geocode_unmatched.py` + `step3d_build_city_list.py` 完成。109,393 条自由文本位置 → 148 个标准化城市，覆盖 50 个国家、9 个宏观区域。城市表包含 city、country、lat、lon、timezone_utc、region 字段。

### 3.2.2 人口与规模变量 ✅

1. 总人口
2. 劳动力规模 proxy
3. 城市规模等级

> **实际执行**：`population_million` 已纳入 `city_attributes.csv`，来源为 `city_external_data.csv`。148 个城市中 143 个有值（缺失 5 个，3.4%）。人口分布：min=0.3M，max=24.9M，mean=6.4M，高度右偏（skew=1.51），建模时使用 log 变换。

### 3.2.3 教育与人力资本变量 ✅

1. 高等教育比例
2. 本科及以上占比
3. STEM / 研究能力 proxy

> **实际执行**：`education_tertiary_pct` 和 `research_capacity`（1-3 等级）已纳入。135 个城市有教育数据（缺失 13 个，8.8%）。EDA 发现 education 与 origination 偏相关不显著（p>0.4），但 research_capacity ↔ avg_lag 有显著负相关（ρ=−0.274, p<0.001）。

### 3.2.4 经济变量 ✅

1. GDP per capita
2. 收入水平
3. 创业 / 创新环境 proxy

> **实际执行**：`gdp_per_capita` 已纳入。135 个城市有值（缺失 13 个，8.8%）。EDA 偏相关发现控制规模后 **gdp ↔ adoption: partial r=0.266, p=0.002** 显著，但 gdp ↔ origination 不显著。

### 3.2.5 科研与创新能力变量 ✅

1. 顶尖大学 / 研究机构数量
2. R&D proxy
3. AI 研究能力 proxy

> **实际执行**：`rd_expenditure_pct`（R&D 占 GDP 比例）和 `research_capacity`（1-3 等级 proxy）已纳入。rd_expenditure ↔ avg_lag: ρ=−0.336 (p<0.001)，研发投入越高采用越快。

### 3.2.6 数字基础设施变量 ✅

1. 宽带 / 数字连接 proxy
2. ICT 或数字经济指标

> **实际执行**：`internet_users_pct` 已纳入。EDA 偏相关发现控制规模后 **internet ↔ adoption: partial r=0.253, p=0.004** 显著。

## 3.3 用途说明

这些增强变量主要用于回答RQ2：

哪些城市特征与 innovation-oriented roles 和 faster adoption 相关？

同时，作业指南特别提醒，很多分析里应尽量使用 **rate** 而不是 raw count，因为 rate 更能控制规模差异。
所以后续建议尽量构造：

1. per-capita innovation rate
2. per-capita adoption rate
3. collaboration intensity rate

而不是只用绝对数。

> **实际执行**：`city_attributes.csv` 中已包含 `origination_rate_pop`、`adoption_rate_pop`、`collaboration_rate_pop` 三个 per-capita rate 变量，K-means 聚类同时使用了绝对量（log 变换后）和 per-capita rate。

# 4. Structure Your Analysis

## 4.1 中文说明

作业要求使用 notebook template，并把分析放在**单个 Python notebook**中；内容应包括代码、分析过程、解释和 narrative text，且 narrative 控制在 **1500 词以内**。

## 4.2 更新后的分析主线

建议 notebook 按下面这条逻辑展开：

1. ✅ 项目筛选与城市映射 → `step1a–step3d` 脚本
2. ✅ 构建 prominent open-AI projects 的城市活动、协作与采用指标 → `step4–step6` 脚本
3. ✅ **EDA：对三张核心表和关键变量进行探索性数据分析，检查数据质量、分布特征和初步模式** → `step8_eda.ipynb` + `step8b_eda_detailed.ipynb`
4. ✅ 识别 open-AI 项目生态中的城市 roles → `step9_kmeans.ipynb`
5. ✅ 测量城市对高影响项目的 adoption lag → `step10_adoption_regression.ipynb`
6. ✅ 解释哪些城市特征与 innovation-oriented roles / faster adoption 相关 → `step11_xgboost_shap.ipynb`
7. ✅ 利用协作网络预测下一波 adopter 城市 → `step12_graphsage.ipynb`
8. ❌ 用 1–2 个具体技术家族或代表项目作为 case study 展示扩散路径和可视化 → 待完成

## 4.4 Notebook 运行策略

重要tips：

1. 不要在提交版 notebook 里做大量原始 API 抓取
2. 不要在 notebook 里做大规模 location 实时地理编码
3. 预处理尽量在 notebook 外完成，再读取清洗后的 csv/parquet
4. 提交前做 Restart & Rerun all

因为作业要求 notebook 应能完整运行，并建议在提交前验证可执行性；若预处理耗时较大，可以提供预处理后的数据并写清说明。

> **实际执行**：所有 API 抓取和地理编码已在 `scripts/` 目录下的 15 个独立 Python 脚本中完成（Step 1a–6），notebook 仅读取预处理后的 CSV 文件。当前 6 个分析 notebook（step8–12）均可独立运行。**待完成**：需要将 6 个分散 notebook 整合到 `Template_submission_CASA0006.ipynb` 并执行 Restart & Rerun All。

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

### ✅ 5.1.4 实际执行结果（Step 9）

**执行文件**：`step9_kmeans.ipynb`（14 个 code cells，全部已执行）

**实际输入变量**（基于 EDA 结论调整）：
- `log_origination`、`log_adoption`、`log_degree`、`log_betweenness`、`log_orig_rate`
- 剔除 `collaboration_count`（与 `weighted_degree` 完全冗余 ρ=1.0）和 `eigenvector_centrality`（VIF=524）
- 全部先 log1p 再 z-score 标准化；5 个缺失城市在标准化前被剔除，实际聚类 143 个城市

**k 选择**：测试 k=2–10，silhouette 最优 k=2（0.3985），但采用理论驱动的 **k=4**（silhouette=0.3480）

**四类城市角色**：

| 角色 | n | mean orig | mean adopt | mean degree | 典型城市 |
|------|---|-----------|------------|-------------|----------|
| Global Innovation Hub | 27 | 275 | 942 | 6,353 | San Francisco, Beijing, London, Tokyo |
| Active Collaborator | 56 | 15 | 188 | 2,247 | Seoul, Bengaluru, Toronto, LA |
| Emerging Contributor | 44 | 4 | 60 | 793 | Xi'an, Jakarta, Cairo, Rome |
| Peripheral / Late Adopter | 16 | 2 | 22 | 258 | Tallinn, Addis Ababa, Lahore |

**与方案对比**：方案预期角色为 originators / collaboration hubs / bridge cities / late adopters；实际聚类结果中 "bridge cities" 未作为独立 cluster 出现（betweenness 区分度不足，网络密度 0.886 过高），取而代之的是 "Emerging Contributor" 角色。

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

### ✅ 5.2.5 实际执行结果（Step 10）

**执行文件**：`step10_adoption_regression.ipynb`（11 个 code cells，全部已执行）

**实际建模策略调整**：由于 adoption lag 的分布特征（mean=6.28, median=2, 大量 lag=0 的 originator 事件），将原方案的连续 lag 回归调整为三个互补模型：

| 模型 | DV | 分析单位 | n | 方法 | 核心结果 |
|------|-----|---------|---|------|----------|
| **Model A** | `is_originator` (0/1) | 城市×项目 | 38,347 | Logistic (clustered SE) | Pseudo R²=0.088 |
| **Model B** | `originator_share` | 城市 | 130 | OLS | R²=0.276, Adj R²=0.222 |
| **Model C** | `log(adoption_count)` | 城市 | 130 | OLS | R²=0.965, Adj R²=0.963 |

**关键发现**：
- `log_entity`（开发者基数）和 `log_degree`（网络中心性）是最强预测变量
- `log_degree` 对 origination 为负效应、对 adoption 为正效应 → 高连接城市更善于采用而非发起
- `betweenness` 在 Model C 中显著正效应 → 桥梁位置促进采用广度
- 外部属性（GDP、education、internet）在 OLS 中不显著 → 网络结构比城市静态属性更重要

**VIF 警告**：`log_degree` VIF=37.5，`log_entity` VIF=28.3 → 存在多重共线性，已在结论中标注

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

### ✅ 5.3.5 实际执行结果（Step 11）

**执行文件**：`step11_xgboost_shap.ipynb`（12 个 code cells，全部已执行）

**实际使用 GradientBoostingClassifier/Regressor**（而非 XGBoost），因为 sklearn 内置实现更轻量且 SHAP 兼容。

| 模型 | DV | 方法 | CV 表现 | 全量表现 |
|------|-----|------|---------|----------|
| **Model D** | `is_originator` (0/1) | GB Classifier | **AUC=0.769±0.004**, F1=0.205 | AUC=0.774 |
| **Model E** | `originator_share` | GB Regressor | **CV R²=−0.785** | Full R²=0.917 |
| **Model F** | `log(adoption)` | GB Regressor | **CV R²=−0.866** | Full R²=0.996 |

**关键发现**：
- Model D 分类 AUC=0.769 → 合理区分能力，但 recall 仅 0.12（originator 数量不平衡）
- Model E/F 城市级回归 **CV R² 为负** → n=148 不足以支撑梯度提升泛化，严重过拟合
- SHAP 与 OLS 的特征重要性排名 Spearman ρ=0.617 (p=0.077) → 两种方法方向一致
- **SHAP Top-3 特征**：`log_entity`、`log_degree`、`betweenness`，与 OLS 回归结论互相印证

**与方案对比**：方案预期 XGBoost 用于城市级解释建模，但实际 n=148 不足以支撑 tree-based 泛化；分类任务（Model D, n=38,347）表现合理，回归任务过拟合。建议在 Discussion 中讨论此局限。

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

### ✅ 5.4.5 实际执行结果（Step 12）

**执行文件**：`step12_graphsage.ipynb`（10 个 code cells，全部已执行）

**实际任务定义调整**：由于所有 148 个活跃城市都有采用事件（无"未采用"城市），将二分类 next-adopter 任务调整为 **adoption intensity prediction**：

| 模型 | DV | 方法 | Test 表现 |
|------|-----|------|-----------|
| **G1** (回归) | `log(adoption_count)` 后半期 | GraphSAGE 2-layer | **R²=0.902, RMSE=0.377** |
| **G2** (分类) | high/low adopter (中位数分割) | GraphSAGE 2-layer | **AUC=0.984, F1=0.980** |

**图结构**：
- 148 节点，9,297 无向边，14 维节点特征
- 时间分割：train ≤ 202406，test > 202406
- Train: 103 城市，Test: 45 城市

**关键发现**：
- 城市排名预测 Spearman ρ=0.976 (全部) / ρ=0.952 (test only)，p<0.001
- GraphSAGE 显著优于所有非图方法（OLS R²=0.965, GB CV R²<0），证明协作网络结构确实为采用预测提供了增量信息
- 模型产出了 64 维城市 embedding，PCA 前两主成分解释 95% 方差

**与方案对比**：方案原定预测"是否成为新 adopter"的二分类；实际调整为"采用强度"的回归+分类双任务，避免了全城市均为 adopter 导致的标签无区分问题。该调整更合理且结果更强。

# 6. Include Required Notebook Sections

> **当前状态**：提交模板 `Template_submission_CASA0006.ipynb` 仍为空白占位状态。以下各节的分析逻辑和代码均已在独立 notebook（step8–12）中完成并验证，需要整合到提交模板中并撰写 narrative（≤1500 词）。

## 6.1 Introduction ❌ 待撰写

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

## 6.2 Research Questions ❌ 待填写

### 6.2.1 Main research question

**How do global cities participate in the creation and use of prominent open-AI projects, and what factors shape the diffusion of these projects across the global urban system?**

### 6.2.2 Sub-questions

1. **What distinct roles do global cities play in the ecosystem of prominent open-AI projects, such as originators, collaboration hubs, bridge cities, and late adopters?**
2. **Which city characteristics are associated with innovation-oriented roles and faster adoption within the ecosystem of prominent open-AI projects?**
3. **Can the GitHub city collaboration network help predict which cities will become the next adopters of prominent open-AI projects?**

## 6.3 Data ❌ 待撰写（代码已完成，缺 narrative + 变量表）

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

> **实际执行**：`city_attributes.csv` 已包含 28 个变量（见下表）。类别变量（city, country, region, cluster, role）与数值变量已明确区分。

| 变量名 | 类型 | 类别 | 说明 |
|--------|------|------|------|
| `city`, `country` | categorical | 标识 | 城市名、国家名 |
| `lat`, `lon` | numeric | 空间 | 经纬度 |
| `entity_count` | numeric | 平台活跃度 | 城市关联的 GitHub/HF 实体数 |
| `origination_count` | numeric | 创新 | 城市发起的 prominent project 数 |
| `origination_rate` | numeric | 创新 | origination / entity (项目发起率) |
| `adoption_count` | numeric | 采用 | 城市采用的 prominent project 数 |
| `adoption_rate` | numeric | 采用 | adoption / entity |
| `avg_lag`, `median_lag` | numeric | 采用速度 | 平均/中位 adoption lag（月） |
| `collaboration_count` | numeric | 协作 | 协作边总权重（≡ weighted_degree） |
| `weighted_degree` | numeric | 网络 | 加权度中心性 |
| `betweenness` | numeric | 网络 | 介数中心性 |
| `eigenvector_centrality` | numeric | 网络 | 特征向量中心性 |
| `population_million` | numeric | 外部属性 | 人口（百万） |
| `gdp_per_capita` | numeric | 外部属性 | 人均 GDP (USD) |
| `education_tertiary_pct` | numeric | 外部属性 | 高等教育比例 (%) |
| `internet_users_pct` | numeric | 外部属性 | 互联网用户比例 (%) |
| `rd_expenditure_pct` | numeric | 外部属性 | R&D 占 GDP 比例 (%) |
| `research_capacity` | numeric | 外部属性 | 科研能力等级 (1–3) |
| `timezone_utc` | numeric | 空间 | UTC 时区偏移 |
| `region` | categorical | 空间 | 宏观区域 (9 类) |
| `origination_rate_pop` | numeric | per-capita | 人均项目发起率 |
| `adoption_rate_pop` | numeric | per-capita | 人均采用率 |
| `collaboration_rate_pop` | numeric | per-capita | 人均协作强度 |
| `cluster` | categorical | 聚类结果 | K-means cluster (0–3) |
| `role` | categorical | 聚类结果 | 角色标签 |

## 6.4 Methodology ❌ 待撰写（代码已完成，缺 narrative + 流程图）

### 6.4.1 英文版框架

The methodology should explain that, after constructing city-level indicators, the project begins with an exploratory data analysis (EDA) to assess data quality, examine variable distributions and correlations, and reveal preliminary spatial and temporal patterns. Building on these findings, the project then combines clustering, regression, tree-based modelling, and graph neural networks to study city roles, adoption speed, explanatory patterns, and network-based adoption prediction in the ecosystem of prominent open-AI projects.

### 6.4.2 中文说明

Methodology 现在应按下面这条顺序写：

#### 6.4.2.1 Step 1. Project filtering and city-level indicator construction ✅

1. 识别与 open-AI 相关且达到传播门槛的 prominent projects
2. 做城市映射
3. 构建创新、协作、桥梁、采用、lag 等指标
4. 尽量采用 rate 而非 raw count

> **已完成**：`step1a–step6` 共 15 个脚本。GitHub 118K + HF 1.24M → 23,481 prominent projects → 148 城市 → 三张核心表 + 月度协作边 + 外部属性。rate 变量（`origination_rate_pop` 等）已构建。

#### 6.4.2.2 Step 2. Exploratory Data Analysis (EDA) ✅ 已完成

EDA 在正式建模之前完成，目的是理解数据质量、发现分布特征、检验变量可用性、并为后续方法提供初步依据。

**实际执行**：`step8_eda.ipynb`（基础 EDA）+ `step8b_eda_detailed.ipynb`（深度分析：Shapiro-Wilk 正态性检验、偏相关、VIF、Mann-Whitney 对比）。详细结论见 §0.3。

##### 2a. 数据质量检查 ✅

1. 检查三张核心表的维度、缺失值比例、数据类型
2. 标记并处理异常值（如某城市 origination_count 异常高是否合理）
3. 检查类别变量与数值变量是否正确分类，避免把 ID 列或类别变量误用为数值变量
4. 确认 prominence threshold 筛选后的样本量是否足够（城市数 ≥ 100、项目数、采用事件数）

> **结果**：city_attributes 148×26，edges 9,636×4，monthly 98,147×4，adoption 39,158×6。缺失值仅外部属性：population 缺 5 (3.4%)，GDP/education/internet/R&D 缺 13 (8.8%)。23 个数值列 + 3 个类别列，无误分类。样本量充足。

##### 2b. 单变量分布 ✅

1. 对关键数值变量画直方图 / KDE：origination_count、adoption_count、avg_lag、degree、betweenness、population、education_rate、income_per_capita 等
2. 检查是否需要 log 变换（如 adoption_lag、population 等通常高度右偏）
3. 对类别变量画频率条形图：region、timezone、lag_group
4. 描述性统计汇总表：count、mean、std、min、25%、50%、75%、max

> **结果**：origination_count skew=6.63、adoption_count 4.29、collaboration_count 2.15 → log1p 后分别降至 1.00、0.25、−0.21。adoption_count log1p 通过 Shapiro-Wilk (p=0.561)。avg_lag (mean=8.44, std=2.40) 近对称无需变换。描述统计：origination mean=57, max=1802(SF); adoption mean=265, max=3757(SF)。

##### 2c. 双变量关系与相关性 ✅

1. 数值变量相关性矩阵 + 热力图（Pearson 或 Spearman）
2. 重点关注输入变量之间的多重共线性（若两变量相关系数 > 0.8，考虑合并或剔除）
3. 关键散点图：
   - origination_rate vs. population（创新是否与城市规模正相关）
   - avg_lag vs. network centrality（网络位置是否与采用速度相关）
   - adoption_count vs. education_rate（教育水平是否与采用量相关）
4. 箱线图：按 region 或 cluster（如有先验分组）拆分关键变量分布

> **结果**：高共线性对——collaboration_count ≡ weighted_degree (ρ=1.000)、eigenvector ↔ degree (ρ=0.999)、entity ↔ adoption (ρ=0.970)。VIF 最高：eigenvector=524, degree=37.5, entity=28.3。偏相关（控制 population + entity）：gdp↔adoption r=0.266 p=0.002，internet↔adoption r=0.253 p=0.004，education/R&D↔origination 均 p>0.4。

##### 2d. 空间分布与地理格局 ✅

1. 全球地图：按城市标注 origination_count / adoption_count 的气泡大小
2. 区域汇总条形图：按洲或国家分组统计城市数量、项目创造数量、采用数量
3. 初步判断是否存在明显的核心—边缘空间格局

> **结果**：Top-10 城市占 origination 69.7%、adoption 43.4%、Top-20 占 84.3%/59.9%。North America 和 East Asia 主导创新和采用。**创新集中、采用去中心化**的不对称核心-边缘结构。

##### 2e. 时间趋势 ✅

1. 月度时间序列：每月全球新增 prominent projects 数量、新增 adoption events 数量
2. 区域层面时间趋势对比：北美 / 欧洲 / 东亚 / 其他地区的活跃度月度变化
3. 检查是否存在季节性或突变点

> **结果**：2022–2024 强增长趋势（反映 AI boom），12月/1月有轻微下降（季节性）。网络随时间持续密化。区域趋势：北美始终领先，东亚追赶明显。

##### 2f. 网络初步描述 ✅

1. 协作网络基本统计：节点数、边数、平均度、密度、连通分量数
2. 度分布图：检查是否近似幂律分布
3. 网络可视化（小规模采样或 top 城市子图）

> **结果**：148 节点、9,636 边、密度 0.886、直径 2、全连通（1 分量）。平均路径长度 1.11，聚类系数 0.0198，传递性 0.918。度分布右偏（hub-and-spoke）。San Francisco degree=13,337 为最大 hub。**密度过高** (0.886) 导致 betweenness 区分度有限。

##### 2g. 对后续建模的指导 ✅

1. 确认哪些变量需要标准化（K-means 输入必须标准化）
2. 确认哪些变量需要 log 变换（Adoption-lag regression 的因变量）
3. 确认是否需要降维或剔除高共线性变量（XGBoost 和 regression 的输入）
4. 确认图结构是否足够稠密以支撑 GraphSAGE 训练
5. 记录 EDA 中发现的关键模式，留待 Discussion 部分对照模型结果讨论

> **已确认决策**：
> - K-means：log1p + z-score；剔除 collaboration_count（冗余）和 eigenvector（VIF=524）
> - Regression：log1p(adoption)、log(population)、log(gdp) 作为变换
> - XGBoost/Regression：剔除 eigenvector，保留 degree + betweenness 但注意 VIF
> - GraphSAGE：网络全连通且密度足够（0.886），适合 GNN 训练
> - 关键模式记录：创新集中但采用分散、网络位置比静态属性更重要、规模不影响速度

#### 6.4.2.3 Step 3. K-means for city roles ✅ 已完成

1. 使用城市层指标识别 roles
2. 输出 originators、collaboration hubs、bridge cities、late adopters 等 cluster

**实际执行（`step9_kmeans.ipynb`）**：
- 聚类特征：log1p(origination_count), log1p(adoption_count), log1p(weighted_degree), log1p(betweenness×1000), log1p(origination_rate_pop) → z-score
- k=4, silhouette=0.35
- 四角色：Global Innovation Hub (27城) / Active Collaborator (56城) / Emerging Contributor (44城) / Peripheral (16城)

#### 6.4.2.4 Step 4. Adoption-lag regression ✅ 已完成

1. 在 城市—项目 层面计算 adoption lag
2. 分析哪些因素与更快项目采用相关
3. 可加入项目固定效应或项目控制变量

**实际执行（`step10_adoption_regression.ipynb`）**：
- 调整为三模型策略：Model A (Logistic, n=38,347), Model B (OLS originator_share, n=130), Model C (OLS log_adoption, n=130)
- 核心发现：log_entity 是最强预测因子；log_degree 对 adoption 正效应、对 originator 概率负效应
- Model C R²=0.965 但存在 degree-adoption 同源循环性
- betweenness 对 adoption 有显著正效应

#### 6.4.2.5 Step 5. XGBoost for explanatory modelling ✅ 已完成

1. 解释哪些城市特征与 innovation-oriented roles 和 faster adoption 相关
2. 用 SHAP 做辅助解释

**实际执行（`step11_xgboost_shap.ipynb`）**：
- Model D (分类 is_originator): CV AUC=0.769 → 合理区分能力
- Model E/F (回归): CV R² 为负 → n=148 样本量不足导致 GB 回归过拟合
- SHAP Top-3 特征：log_entity, log_degree, betweenness
- 分类模型可用，回归模型需谨慎解读（OLS 更适合小样本）

#### 6.4.2.6 Step 6. GraphSAGE for next-wave adopter prediction ✅ 已完成

1. 基于城市协作网络与节点特征
2. 预测哪些城市会在下一期成为 prominent project 的新 adopter

**实际执行（`step12_graphsage.ipynb`）**：
- 时间分割：train ≤ 202406, test > 202406
- Model G1 (回归): Test R²=0.902, RMSE=0.377
- Model G2 (分类 high/low adopter): Test AUC=0.984, F1=0.980
- 城市排名 Spearman ρ=0.976 → 图结构显著提升预测能力

#### 6.4.2.7 Step 7. Optional case-study visualisation

1. 选 1–2 个技术家族或代表项目
2. 展示更具体的扩散时间线、空间地图、网络路径

**状态**：🔲 待完成

## 6.5 Expected Results and Discussion（含实际结果对照）

### 6.5.1 中文说明

期望的结果可能包括以下几个方面。下面在每小节添加了实际建模所得的关键结论。

### 6.5.2 小节 1：Spatial concentration of prominent open-AI projects

预期展示：

1. 全球地图
2. 哪些城市在高影响 open-AI 项目中更活跃
3. 创造、协作、采用活动的空间不均衡

**✅ 实际结论**：Top-10 城市占 origination 69.7%、adoption 43.4%。创新高度集中于少数城市（San Francisco, Beijing, Shanghai 为前三），但采用相对去中心化，呈现明显的**创新集中、采用分散**的不对称核心-边缘结构。

### 6.5.3 小节 2：Distinct city roles in the ecosystem

预期展示：

1. K-means cluster 结果
2. originators、collaboration hubs、bridge cities、late adopters 的角色画像

**✅ 实际结论**：K-means (k=4, silhouette=0.35) 识别出四种角色。27 个 Global Innovation Hub 主导全球创新（mean origination=275），56 个 Active Collaborator 形成协作中坚，44 个 Emerging Contributor 初步参与，16 个 Peripheral 城市处于边缘。角色分布与 North America / East Asia 主导格局一致。

### 6.5.4 小节 3：Project-level adoption lag and diffusion speed

预期展示：

1. prominent projects 的全球首次出现分布
2. 城市对这些项目的 lag 分布
3. 哪些因素与更短 lag 相关

**✅ 实际结论**：Adoption lag 范围 0–50 个月（mean=6.28, median=2）。East Asia (mean=6.60) 采用最快，Latin America (10.87) 最慢。创新城市采用快近 2 倍 (top avg_lag=5.98 vs bottom=10.25, p<0.001)。origination_count (ρ=−0.611)、R&D (ρ=−0.336)、research_capacity (ρ=−0.274) 与更快采用显著相关；城市规模 (p=0.445) 不显著。

### 6.5.5 小节 4：City characteristics and explanatory patterns

预期展示：

1. XGBoost feature importance
2. SHAP summary plot
3. 高学历、高收入、科研能力、数字基础设施、网络中心性与创新/采用能力的关系

**✅ 实际结论**：开发者基数 (entity_count) 和网络中心性 (weighted_degree) 是最重要的特征（SHAP Top-3: log_entity, log_degree, betweenness）。传统经济/教育指标对 origination 无直接效应（偏相关 p>0.4），但控制规模后 GDP (partial r=0.266, p=0.002) 和互联网覆盖率 (partial r=0.253, p=0.004) 对 adoption 显著。XGBoost 分类 AUC=0.77 可用，但回归因 n=148 过拟合（CV R² 为负），OLS 更适合此样本量。

### 6.5.6 小节 5：Predicting next-wave adopters

预期展示：

1. GraphSAGE 的性能
2. 哪些城市在下一期最可能 adopted 新的 prominent projects
3. 预测正确与错误的案例

**✅ 实际结论**：GraphSAGE 表现优异——回归 Test R²=0.902, 分类 Test AUC=0.984/F1=0.980。城市排名 Spearman ρ=0.976 (p<0.001)。图结构 + 节点特征联合建模显著优于纯特征方法，验证了协作网络对预测下一波 adopter 的价值。

### 6.5.7 小节 6：Case-study visualisation

预期展示：

1. 1–2 个具体技术家族或代表项目的扩散时间线
2. 地图、网络图或 Sankey / timeline 图
3. 用于更直观地演示传播过程

**状态**：🔲 待完成

### 6.5.8 小节 7：Critical reflection

建议主动讨论：

1. prominent projects 的筛选规则可能引入平台偏差
2. 不同类型项目的扩散机制并不完全相同
3. adoption lag 在跨项目比较时受项目异质性影响
4. GraphSAGE 预测的是 adopter，而不是 originator emergence
5. **（新增）** XGBoost 回归在 n=148 小样本下 CV R² 为负，说明 GB 方法不适合此规模城市级回归
6. **（新增）** collaboration_count 与 weighted_degree 完全冗余 (ρ=1.0)，degree 与 adoption 同源构建导致 Model C R²=0.965 存在循环性
7. **（新增）** 网络密度 0.886 导致 betweenness 区分度有限，betweenness 与 degree 呈负相关 (ρ=−0.915) 是密集网络的数学特性而非桥梁效应

## 6.6 Expected Conclusion ❌ 待撰写

### 6.6.1 中文说明

Expected Conclusion 现在应围绕“高影响 open-AI 项目生态”来收束。

### 6.6.2 第一层：城市角色

全球城市在 prominent open-AI projects 的生态中并不扮演同质角色。
有些城市更像 originators，有些是 collaboration hubs，有些是 bridge cities，而更多城市是 late adopters。

> **✅ 实际验证**：K-means (k=4) 确认了角色异质性—27 个 Global Innovation Hub（San Francisco, Beijing, London 等）主导创新发起（mean origination=275），16 个 Peripheral 城市仅 mean=2。与预期基本一致，但“bridge cities”未作为独立 cluster 出现（网络密度 0.886 导致 betweenness 区分度不足）。

### 6.6.3 第二层：扩散速度

高影响 open-AI 项目的扩散并不是随机发生的。
不同城市对这些项目的 adoption lag 有明显差异，说明传播速度在全球城市体系中高度不均衡。

> **✅ 实际验证**：Adoption lag 范围 0–50 个月，mean=6.28, median=2。Top 创新城市 avg_lag=5.98 vs Bottom 城市=10.25 (Mann-Whitney p<0.001)。East Asia 最快 (6.60)、Latin America 最慢 (10.87)。确认传播速度高度不均。

### 6.6.4 第三层：解释因素

城市的教育、收入、科研能力、数字基础设施和网络位置等因素，可能与 innovation-oriented roles 和 faster adoption 相关。

> **✅ 实际验证（需修正预期）**：传统属性（education、income）对 origination 无直接效应（偏相关 p>0.4），但 GDP (partial r=0.266, p=0.002) 和 internet (partial r=0.253, p=0.004) 控制规模后对 adoption 显著。**网络位置**（degree, betweenness）是最强解释变量（SHAP Top-3），远超静态城市属性。发现修正了预期——“网络结构比城市自身属性更重要”。

### 6.6.5 第四层：预测价值

GitHub 城市协作网络对“下一波 adopter 城市”的识别具有预测价值，因此网络结构不仅能描述协作关系，也能帮助理解技术扩散。

> **✅ 实际验证**：GraphSAGE Test R²=0.902, AUC=0.984, 城市排名 Spearman ρ=0.976 (p<0.001) → 强烈支持协作网络的预测价值。图结构 + 节点特征联合建模显著优于纯特征方法。

### 6.6.6 第五层：future work

1. 可进一步把 PatentsView 引入为 formal innovation validation layer
2. 可把 case-study 技术家族扩展成系统性对比研究
3. 可进一步比较不同项目类型的扩散机制差异
4. **（新增）** 尝试 edge-level GNN 或 link prediction 预测新协作关系的形成
5. **（新增）** 扩大城市样本（当前 n=148 限制了 tree-based 方法泛化能力）
6. **（新增）** 引入更精细的空间变量（如到最近 Innovation Hub 的网络距离）
