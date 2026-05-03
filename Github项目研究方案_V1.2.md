# 0. 实施进度与执行概况（截至 2026-05-02，含 Step 11 V1.5：XGBoost + IEI + 4-way 敏感性）

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
| 分析 | Step 9: K-means + 参数敏感性 + DBSCAN + GMM | ✅ 已完成（已扩展） | `step9_kmeans.ipynb` |
| 分析 | Step 10: Adoption 回归 (B/C) + 正则化稳健性 | ✅ 已完成（V1.3 精简：删 Model A Logistic + Model B-Beta） | `step10_adoption_regression.ipynb` |
| 分析 | Step 11: 事件级 D-reg（**XGBoost** + SHAP） | ✅ 已完成（**V1.5**：主模型 IEI×17，`log1p(interval)`，**CV R²≈0.307±0.012**；含 4-way 敏感性） | `step11_xgboost_shap.ipynb` |
| 分析 | Step 12: GraphSAGE + MLP 消融 | ✅ 已完成（V1.2 修复泄漏 + 参数优化 + 消融实验） | `step12_graphsage.ipynb` |
| 分析 | Step 13: 技术类型交互回归 (RQ5) | ✅ 已完成（OLS + 54 交互项 + 6 项目控制，R²=0.284） | `step13_tech_type_interaction.ipynb` |
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

### 优化 6：Step 10/11 职责重构（V1.2）

原 Step 11 混合了线性方法（Ridge/Lasso/ElasticNet）和树模型（梯度提升 + SHAP），且 Model E/F（n=148 城市级 GB 回归）与 Step 10 Model B/C 完全重复。V1.2 重构为清晰的方法论分工：
- **Step 10 = 所有线性/参数方法**（OLS、Beta、Ridge、Lasso、ElasticNet 等；**V1.3 已删 Logistic Model A**）→ 推断 + 稳健性
- **Step 11 = 所有非线性方法**（树模型 + SHAP）→ 非线性检验 + 可解释性

具体变更：
1. **Step 10 新增 10.5d**：Ridge/Lasso/ElasticNet 正则化稳健性检验（从 Step 11 移入），对 originator_share、log(adoption)、log(avg_iei) 三个 DV 做 5-fold CV 对比，含系数可视化和 Lasso 特征选择
2. **Step 11 删除 Model E/F**：GB 回归（n=148）严重过拟合（CV R² 为负），与 Step 10 OLS 重复且无独立信息增量
3. **Step 11 精简（V1.3）**：删除 Model D（GB 分类，n=39k），**仅保留 Model D-reg**（事件级 lag 回归，n≈25k）。**V1.5（2026-05-02）**：主模型改为 **IEI（inter-event interval）** + **4-way 敏感性**，详见 **优化 9**

### 优化 7：GraphSAGE 方法论强化（V1.2）

Step 12 进行了全面的方法论审查与优化：

1. **特征泄漏修复**：原版使用全时段 `adoption_count`(r=0.731)、`weighted_degree`(r=0.864) 等来自 `city_attributes.csv` 的特征，包含测试期信息。V1.2 替换为仅从训练期 (≤202406) 计算的 4 个活动特征 (`train_adopt_count`, `train_orig_count`, `train_weighted_degree`, `train_entity_count`)，特征维度从 14 降至 10
2. **数据划分改进**：70/30 随机划分（无验证集）→ 60/20/20 分层划分（基于 `y_cls` 确保高/低采纳者比例均衡）。新增验证集支持 early stopping 与模型选择
3. **参数调优**：三组配置对比实验（dropout=0.5/0.3 × early stopping 有/无 × WD=1e-3/5e-4），最终选择 Config C（dropout=0.3, WD=5e-4, early stopping patience=20），在验证集 R²=0.918 和测试集 R²=0.914 间取得最佳泛化
4. **MLP 消融基线**：新增同构 2 层 MLP（无图传播）对比，量化图结构增量 ΔR²=+0.145
5. **train_weighted_degree 消融**：去掉该主导特征后图结构增量反而从 ΔR²=+0.145 扩大至 ΔR²=+0.367，证明 GraphSAGE 的图传播可部分替代节点度特征
6. **新增 Limitations & Discussion 节 (12.11)**：系统讨论小样本局限、特征主导性、图密度、G2 任务价值、因果解释缺失等 5 项局限

### 优化 8：Robustness Checks 量化已知局限

针对已知局限进行了系统量化检验（详见 §0.6）：

1. **10.4b 内生性检验**：剔除 `log_degree` 后 Model C R² 仅降 0.6%（0.970→0.964），证实 degree 独立解释力极小，循环性核心来自 `entity_count`
2. **10.4c 网络密度检验**：使用 weight≥5 子网络（密度 0.886→0.563）重算 degree/betweenness，Model C R² 仅降 0.3%；原始与子网络 betweenness 相关性 −0.05，证实密网 betweenness 不可靠
3. **11.x 事件级 D-reg（沿革）**：早期仅城市量表 + 少量项目聚合、sklearn GBR 时，事件级 CV R²≈0.02——说明**在缺乏逐项目变化特征时**，城市量表难以解释事件级 lag。**V1.5** 主模型改为 **IEI（inter-event interval）**，改用 **XGBoost**，**CV R²≈0.31**（见优化 9）；4-way 敏感性显示 SHAP 排序稳健，**项目侧变量主导**、城市 `betweenness` 在 IEI 视角下更突出，与 Step 10 Model C 在实质性结论上一致
4. **（新增）9.6 K-Means 参数敏感性**：k=3/4/5 × n_init=50 系统对比三个评估指标（Silhouette/CH/DB），确认 k=4 为理论-统计最佳折衷；n_init 增大不改变结果，证明聚类已稳定
5. **（新增）9.7 DBSCAN 替代模型**：eps×min_samples 网格搜索 → 仅 2 簇 + 14.9% 噪声，silhouette=0.299；确认密度聚类不适合该数据，但噪声点可标记异常城市
6. **（新增）9.8 GMM 替代模型**：BIC/AIC 模型选择 + k=3/4/5 对比 → GMM(k=4) sil=0.278，与 K-Means ARI=0.340；94.6% 城市分配确定，软概率可量化边界城市
7. **（新增）9.9 跨方法综合对比**：7 种聚类配置 × 3 指标 + ARI 热力图 + PCA 投影，系统确认 K-Means k=4 为最优选择
8. **（新增）10.5c Region FE 检验**：对 Models A/B/C 加入 9 类宏观区域固定效应，验证核心结论稳健性。发现：(1) log_entity 和 log_degree 保持显著方向不变；(2) GDP 对 origination 的效应被区域组成完全吸收；(3) 外部属性仍全面不显著；(4) Adj R² 几乎不变，确认主模型（不含 region FE）适当。主模型特征集与 Step 11/12 保持一致以支持跨方法对比
9. **（新增）10.5d Ridge/Lasso/ElasticNet 稳健性检验**：对 n=148 城市级回归做正则化对比。结果：log(adoption) 上 Lasso CV R²=0.62 优于 OLS 的 0.60，确认 OLS 系数基本稳定；originator_share 和 log(avg_iei) 所有方法均 CV R²<0，确认这两个 DV 在城市特征下预测力天花板极低。Lasso 将 betweenness 收缩为零，与 Step 8 EDA 中 betweenness 区分度不足的发现一致

### 优化 9：Step 11 Model D-reg 升级为 XGBoost + IEI + 4-way 敏感性（V1.5, 2026-05-02）

**问题意识**：D-reg 的分析单位是 **城市–项目事件**（每行 = 某城市对某项目的一次采纳，`n≈25,297`，`lag>0`），不是城市截面（148）。同一城市的城市量纲特征在多行中**重复**；若缺少**随项目变化**的协变量，事件级 R² 会被天花板压低——这与「城市特征难以单独阐明采纳时机」并不矛盾，而是**层级与特征设定**问题。

**实际执行**（`step11_xgboost_shap.ipynb`，已 papermill 跑通）：

| 项目 | 内容 |
|---|---|
| **因变量** | `log1p(lag)`（月） |
| **模型** | `XGBRegressor`：`n_estimators=1000`, `max_depth=6`, `learning_rate=0.03`, `subsample=0.8`, `colsample_bytree=0.8`, `tree_method='hist'`, `random_state=42` |
| **CV** | `KFold(n_splits=5, shuffle=True, random_state=42)`，指标 R²（log 空间） |
| **特征（17）** | **城市块（11）**：Step 10 九维 IV + `eigenvector_centrality` + `origination_rate`；**项目聚合（2）**：`log_proj_pop`（采纳城市数）、`proj_origin_idx`（全局创建月份序列索引）；**项目属性（4）**：`log_stars`, `log_forks`, `popularity_pctile`, `fork_star_ratio`（自 `prominent_projects_master.csv` 按 `project_id` 合并；HF 行无 fork/star 比时用中位数填充） |

**主要数值成果**：

- **CV R²（log-lag）= 0.3023 ± 0.0160**
- 全样本拟合 R²（log）≈ 0.56、（raw lag）≈ 0.46（仅作参考，以 CV 为准）
- **SHAP（`shap.TreeExplainer`）全局排序（mean|SHAP| Top-5）**：`proj_origin_idx`, `log_proj_pop`, `log_forks`, `fork_star_ratio`, `popularity_pctile` —— **项目侧占主导**；城市块中 `log_population`, `origination_rate`, `eigenvector_centrality` 等仍有可见贡献

**与 Step 10 的衔接**：Model C（V1.3 改用 `log1p(avg_iei)`）与 Step 11 D-reg-IEI 在因变量定义上统一；Step 10 描述城市截面均值，Step 11 在事件级控制可观测**项目**异质性（R²≈0.30），两处均支持**采纳时机主要由项目（及未观测因素）驱动**，粒度不同但结论一致。

**工程**：`requirements.txt` 已增加 `xgboost`。

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

### K-means 城市角色（Step 9, k=4, silhouette=0.35）+ 参数敏感性 & 替代模型

| 角色 | n | mean orig | mean adopt | mean degree | 典型城市 |
|---|---|---|---|---|---|
| Global Innovation Hub | 27 | 275 | 942 | 6,353 | San Francisco, Beijing, London, Tokyo |
| Active Collaborator | 56 | 15 | 188 | 2,247 | Seoul, Bengaluru, Toronto, LA |
| Emerging Contributor | 44 | 4 | 60 | 793 | Xi'an, Jakarta, Cairo, Rome |
| Peripheral / Late Adopter | 16 | 2 | 22 | 258 | Tallinn, Addis Ababa, Lahore |

**参数敏感性分析（n_init=50）**：

| k | Silhouette | CH Index | DB Index | 结论 |
|---|---|---|---|---|
| k=3 | **0.386** (最优) | 151.8 | **0.869** (最优) | 丢失理论中间层（Active Collaborator），过于粗糙 |
| k=4 | 0.348 | 143.0 | 0.959 | 匹配四角色理论框架，兼顾解释性与指标 |
| k=5 | 0.377 | 140.2 | 0.907 | 拆分 Peripheral 为两组，可解释性下降 |

- 增大 n_init 从 20→50 后聚类结果**完全不变**，证明原始结果已收敛稳定

**替代模型对比**：

| 方法 | 簇数 | Silhouette | 特点 |
|---|---|---|---|
| DBSCAN (eps=0.8, ms=5) | 2 + 22 噪声点 (14.9%) | 0.299 | 仅发现 2 个密度簇；数据无明显密度间隙，DBSCAN 不适用；噪声点可作为异常城市鲁棒性检验 |
| GMM (k=4) | 4 | 0.278 | BIC 最优 k=2，AIC 最优 k=8（分歧大）；与 K-Means ARI=0.340，中等一致；仅 8 城 (5.4%) 分配不确定 (max prob<0.7) |
| **K-Means (k=4)** ← 保留 | 4 | **0.348** | 理论驱动 + 指标稳健 + 结果稳定，作为主模型 |

### Adoption 回归（Step 10, 22 cells，V1.3 精简：删 Model A Logistic + Model B-Beta）

| 模型 | DV | n | R²/Pseudo R² | 最强变量 |
|---|---|---|---|---|
| Model B (OLS) | originator_share | 148 | R²=0.247, Adj R²=0.198 | log_entity (+), log_degree (−) |
| Model C (OLS) | log1p(avg_iei) | 148 | R²=TBD（重算中） | IEI = 城市采纳距上一采纳城市的月数；比 avg_lag 更能控制项目年龄混淆 |

**Model C 重大调整（V1.3）**：原 Model C 的 DV 从 `log(adoption_count)` 改为 `log(avg_lag)`（非 originator 事件的平均采用时滞）。**V1.3 进一步调整**：DV 从 `log(avg_lag)` 改为 `log1p(avg_iei)`（城市级平均 Inter-Event Interval），以消除项目年龄混淆：avg_lag 对老项目天然偏大，IEI 仅衡量该城市相对于前一个采纳城市的响应速度，与 Step 11 Model D-reg-IEI 保持因变量一致性。原 adoption breadth 模型（R²=0.965，存在 tautology）移至 Appendix 10.4b。

**V1.3 精简**：删除 Model A（Logistic 回归，聚类标准误）和 Model B-Beta（Beta 回归鲁棒性检验）。保留 Model B（OLS originator_share，对应 RQ2 创新导向角色）、Model C（OLS adoption speed，对应 RQ3 采纳速度）和 Appendix 10.4b（adoption breadth 同义反复分析，对应 RQ2 采纳广度）。

**Model C（IEI 版）**：DV 改为 `log1p(avg_iei)`（城市级平均 Inter-Event Interval，非发起城市事件，IEI≥0）。IEI 控制项目年龄混淆，与 Step 11 D-reg-IEI 的事件级因变量保持一致。结果待重新运行后更新（预期结论方向与 avg_lag 版相近：城市特征解释力有限，项目异质性主导）。**与 Step 11 相呼应**：两层均以 IEI 为速度指标，确保城市截面（OLS）与事件级（XGBoost）分析在方法论上一致。

**Robustness Checks**：
- **10.3b Beta 回归**：originator_share 为比例变量，Beta 回归结果与 OLS 方向和显著性一致
- **10.4b 内生性检验（Appendix）**：adoption breadth 模型 R²=0.965 主要反映 entity_count ↔ adoption_count 同源循环
- **10.5c Region FE 检验**：加入区域固定效应后核心结论不变，GDP 对 origination 的边际效应被区域组成吸收，但 GDP 对采纳速度有独立负效应；Adj R² 几乎不变，确认不含 region 的主模型适当
- **10.5d 正则化稳健性检验（V1.2 新增）**：Ridge/Lasso/ElasticNet 5-fold CV 对比。log(adoption) 上 Lasso CV R²=0.62 优于 OLS 的 0.60，系数稳定；originator_share 和 log(avg_lag) 所有方法均 CV R²<0，确认预测力天花板极低。Lasso 将 betweenness 收缩为零

### XGBoost + SHAP 事件级分析（Step 11, V1.5）

**V1.3**：删除 Model D（GB 分类），notebook **仅保留 Model D-reg**。

**V1.4**：D-reg 改为 XGBoost + 17 特征，因变量 `log1p(lag)`。

**V1.5（2026-05-02）**：主模型因变量改为 **`log1p(inter-event interval)`**（IEI），增加 4-way 敏感性对比。详情见 **§0.3 优化 9**。

| 模型 | DV | n | CV 表现 | 备注 |
|---|---|---|---|---|
| Model D-reg (XGBoost) | log1p(lag) | 25,297 | **CV R²=0.3023±0.0160** | SHAP 中项目侧主导；城市块为边际信号 |

- **SHAP Top-5（mean|SHAP|）**：proj_origin_idx, log_proj_pop, log_forks, fork_star_ratio, popularity_pctile
- **城市块**（相对领先示例）：log_population, origination_rate, eigenvector_centrality, log_degree, log_entity —— 可与 Step 10 系数/正则化结果对照
- **层级提示**：事件级分析需含**随项目变化**的协变量；仅靠重复的城市量表无法反映跨项目异质性（早期 ~0.02 的设定即属此类）

### GraphSAGE（Step 12）

| 模型 | DV | Test 表现 |
|---|---|---|
| G1 (回归) | log(adoption) | **R²=0.914, RMSE=0.436** |
| G2 (分类) | high/low adopter | **AUC=0.960, F1=0.857** |
| MLP 消融 (回归) | log(adoption) | R²=0.768, RMSE=0.713 |
| MLP 消融 (分类) | high/low adopter | AUC=0.964, F1=0.933 |

- 图结构增量：ΔR²=+0.145（GraphSAGE vs MLP），**图传播在回归任务上提供显著增值**
- 城市排名预测 Spearman ρ=0.960 (p<0.001)
- train_weighted_degree 消融：去掉后 GraphSAGE R² 降至 0.829，MLP 降至 0.463；图结构增量反而扩大至 ΔR²=+0.367，说明图传播可部分替代该特征

## 0.6 已知局限与量化评估

1. **网络密度偏高 (0.886)**：betweenness 区分度有限。**已量化（10.4c）**：使用 weight≥5 子网络（密度 0.563，147 节点，全连通）重算网络特征后，Model C R² 仅降 0.003；原始 betweenness 与子网络 betweenness 相关性仅 −0.05，确认密集网络中 betweenness 不可靠。隶属 Step 5（建边阈值）+ Step 8（EDA 发现）
2. **GB 回归不适合 n=148**：V1.2 已删除 Model E/F（CV R² 为负的城市级 GB 回归），改由 Step 10 Section 10.5d 的 Ridge/Lasso 做正则化稳健性检验。**Step 11（V1.5）** 仅保留 **Model D-reg**：**XGBoost** 事件级回归（n≈25.3k），主模型 IEI×17 **CV R²≈0.31**，含 4-way 敏感性，SHAP 与 Step 10 城市结论可对读。隶属 Step 10 + Step 11
3. **外部属性对 origination 直接解释力弱**：但控制规模后 GDP (partial r=0.266, p=0.002) 和 internet (partial r=0.253, p=0.004) 对 adoption 显著。**性质：研究发现，非方法缺陷**。隶属 Step 8 偏相关 + Step 10 回归
4. **collaboration_count ≡ weighted_degree**：完全冗余，建模已只保留 degree。**已解决**。隶属 Step 5 变量定义
5. **Model C R²=0.965 存在循环性**：**已量化（10.4b）**：剔除 log_degree 后 R² 仅降 0.6%（0.970→0.964），真正的循环性来自 `log_entity` 与 `adoption_count` 的近定义同源关系（log_entity 系数从 0.64 飙升至 1.10）。隶属 Step 10 建模设计
6. **（新增）K-Means k 选择的统计-理论权衡**：k=3 silhouette=0.386 统计最优，但 k=4=0.348 理论最优。**已量化（§9.6）**：参数敏感性分析确认 k=4 在三个指标（Silhouette/CH/DB）上均接近最优，且 n_init=50 不改变结果，证明聚类已稳定。隶属 Step 9
7. **（新增）DBSCAN 不适合该数据**：仅发现 2 个密度簇 + 14.9% 噪声。**已量化（§9.7）**：城市特征空间无明显密度间隙。噪声点可用于异常城市检验。隶属 Step 9
8. **（新增）GMM 与 K-Means 一致性中等（ARI=0.340）**：**已量化（§9.8–9.9）**：GMM 因椭球协方差产生不同划分，但 94.6% 城市分配确定（max prob≥0.7），7 种配置的 ARI 热力图和 PCA 投影确认 K-Means k=4 为最稳健选择。隶属 Step 9
9. **（新增）GDP 效应被区域组成吸收**：不含 region FE 时 GDP 对 origination 边际显著（p=0.057），加入 region 后完全消失（p=0.874）。说明之前观察到的"GDP 效应"实际是区域组成效应——高 GDP 城市集中在 North America/Europe 等本身有高 origination 优势的区域。**10.5c Region FE Robustness Check 已量化**。隶属 Step 10
10. **（新增）采纳速度与 Step 11 事件级模型**：Model C（DV=log_avg_iei，n=148）R²=TBD（重算中）；**Step 11 D-reg-IEI（V1.5，n≈25.3k）** 在控制可观测**项目**属性后 CV R²≈0.31，SHAP **项目侧主导**——两处均以 IEI 为速度因变量，一致支持「采纳时机主要由项目异质性驱动」，城市块为截面或事件上的**边际**信号。**性质：研究发现，非方法缺陷**。隶属 Step 10 + Step 11
11. **（V1.2）GraphSAGE 小样本局限 (n=148 节点)**：仅 30 个测试节点，单次 60/20/20 划分结果可能不稳定。图节点 k-fold CV 存在消息传递跨折泄漏问题，目前采用单次划分 + early stopping。**已通过 Val R²=0.918 ≈ Test R²=0.914 的一致性间接验证泛化**。隶属 Step 12
12. **（V1.2）train_weighted_degree 主导性 (r=0.934)**：该训练期特征与目标极高相关。虽非数据泄漏（严格来自训练期），但模型可能主要学习"过去活跃→未来活跃"的近平凡映射。**已量化（§12.11 消融）**：去掉后 GraphSAGE R² 从 0.914 降至 0.829（ΔR²=−0.084），MLP 降至 0.463（ΔR²=−0.306），同时图结构增量从 ΔR²=+0.145 扩大至 ΔR²=+0.367。隶属 Step 12
13. **（V1.2）图密度 0.886 稀释 GNN 局部性**：2 层 GraphSAGE 感受野覆盖几乎全部节点，邻居聚合趋近全局平均。部分解释了 MLP 分类 AUC(0.964) ≈ GraphSAGE AUC(0.960)。**性质：数据特性限制，非方法缺陷**。隶属 Step 12
14. **（V1.2）G2 分类任务价值有限**：MLP AUC(0.964) ≈ GraphSAGE AUC(0.960)，图结构对二分类无额外贡献。中位数二值化丢失信息、任务过于简单。**G2 已降级为 G1 的附属验证，非独立主模型**。隶属 Step 12
15. **（V1.2）GraphSAGE 为预测模型而非因果模型**：高 R² 不意味城市协作*导致*采纳。城市规模可能同时驱动协作强度和采纳数量（共因混淆）。**性质：方法论边界，在 notebook §12.11 中明确讨论**。隶属 Step 12

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
| `step9_kmeans.ipynb` | 41 | RQ1 | K-means 城市角色聚类 + 参数敏感性 (§9.6) + DBSCAN (§9.7) + GMM (§9.8) + 综合对比 (§9.9) |
| `step10_adoption_regression.ipynb` | 22 | RQ2 | Adoption 回归 (B/C) + Robustness (10.4b Tautology, 10.5c Region FE, 10.5d Ridge/Lasso) |
| `step11_xgboost_shap.ipynb` | 8 | RQ3 | 事件级 D-reg：**XGBoost** + **SHAP**（17 特征，`log1p(lag)`） |
| `step12_graphsage.ipynb` | 10 | RQ4 | GraphSAGE 预测 |
| `step13_tech_type_interaction.ipynb` | 22 | RQ5 | 技术类型分类 + OLS 交互回归（已完成） |

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
2. **Which city characteristics are associated with innovation-oriented roles and project adoption breadth within the ecosystem of prominent open-AI projects?**
3. **Which city characteristics are associated with faster adoption speed of prominent open-AI projects across cities?**
4. **Can the GitHub city collaboration network help predict which cities will become the next adopters of prominent open-AI projects?**
5. **Do the effects of city characteristics on the diffusion speed of prominent open-AI projects vary across technology types (e.g., LLM foundation models, LLM applications, vision, agent, multimodal, speech)?**


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

这些增强变量主要用于回答 RQ2 和 RQ3：

- RQ2：哪些城市特征与 innovation-oriented roles 和 adoption breadth 相关？
- RQ3：哪些城市特征与 faster adoption speed 相关？

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
8. ✅ 检验城市特征对扩散速度的影响是否因技术类型而异 → `step13_tech_type_interaction.ipynb`
9. ❌ 用 1–2 个具体技术家族或代表项目作为 case study 展示扩散路径和可视化 → 待完成

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

**执行文件**：`step9_kmeans.ipynb`（41 个 cells，含 §9.6–9.9 新增参数敏感性与替代模型分析）

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

### ✅ 5.1.4b 聚类特征扩展：变量筛选全记录（V1.3 新增，5→11 维）

原始聚类使用 5 维特征。经系统性特征工程，从内生网络/活动指标、时间维度、协作结构、项目质量四个方向共**探索 40+ 候选变量**，最终新增 7 个通过独立性与数据质量检验的特征。经多重共线性诊断（VIF），移除与 `log_adoption` 近乎完全共线的 `log_degree`（r=0.973, VIF=56.41），聚类输入确定为 **11 维**。

#### 最终保留的 11 个聚类特征

| # | 变量名 | log 变换 | 捕捉维度 | 与其余特征 max\|r\| | 文献依据 |
|---|---|---|---|---|---|
| 1 | `origination_count` | log1p | 创新产出规模 | — (原始) | Wachs et al. (2022) |
| 2 | `adoption_count` | log1p | 采纳广度 | — (原始) | Wachs et al. (2022) |
| 3 | `betweenness` | log1p(×1000) | 桥梁/中介角色 | — (原始) | Balland & Boschma (2021) |
| 4 | `origination_rate_pop` | log1p | 人均创新强度 | — (原始) | Wachs et al. (2022) |
| 5 | **`avg_lag`** | log1p | 采纳速度 | 0.726 (origination) | Rogers (2003); Balland et al. (2020) |
| 6 | **`lag_std`** | log1p | 采纳时间一致性 | 0.728 (avg_lag) | Lamba et al. (2020) |
| 7 | **`cross_region_ratio`** | 无 (已 [0,1]) | 协作地理广度（跨洲占比） | 0.326 (orig_rate_pop) | Balland & Boschma (2021) |
| 8 | **`pop_top25_share`** | 无 (已 [0,1]) | 高影响力项目参与率 | 0.349 (orig_rate_pop) | Nature Global Innovation Hubs (2025) |
| 9 | **`orig_top25_share`** | 无 (已 [0,1]) | 创始项目质量 | 0.135 (adoption) | Feldman & Audretsch (1999) |
| 10 | **`lag_quality_corr`** | 无 (已连续) | 趋势引领 vs 追随 | 0.177 (cross_region) | Rogers (2003) adopter categories |
| 11 | **`avg_fork_star_ratio`** | 无 (已连续) | 项目实用深度 (fork/star) | 0.290 (origination) | 开源软件实用性度量文献 |

#### 5.1.4c 特征构造：五张核心 CSV 数据字典（Variable / Type / Definition）

以下为 Step 5–6 及 Step 1c 产出的 Tabular 模式说明，格式与统计课程中「变量–类型–定义」表一致，供方法与可复现文档引用。

**`city_attributes.csv`（城市级属性表，≈148 行）**

| Variable | Type | Definition |
| :--- | :--- | :--- |
| `city` | Categorical | 标准化城市名，与 `city_list.matched_city` 对齐。 |
| `country` | Categorical | 国家名称。 |
| `lat` | Continuous | 城市纬度（°）。 |
| `lon` | Continuous | 城市经度（°）。 |
| `entity_count` | Count | 该城在目标样本中关联的 GitHub/HF 实体数（来自 `city_list`，作规模/活跃度分母）。 |
| `origination_count` | Count | 城市作为项目创始方的事件条数（`city_project_adoption_events` 中 `is_originator`=1 的行数）。 |
| `origination_rate` | Continuous | `origination_count / entity_count`；按实体规模标准化的创始强度。 |
| `adoption_count` | Count | 该城参与采纳的**不重复** `project_id` 数量。 |
| `adoption_rate` | Continuous | `adoption_count / entity_count`。 |
| `avg_lag` | Continuous | 该城所有采纳事件的平均滞后（月）。 |
| `median_lag` | Continuous | 同上，中位滞后（月）。 |
| `collaboration_count` | Count | 在聚合协作网络上，该城与所有邻居的 `edge_weight` 之和（无向，源+汇）。 |
| `weighted_degree` | Continuous | 协作无向图的加权度（与 `collaboration_count` 在本构造中等价）。 |
| `betweenness` | Continuous | 加权介数中心性。 |
| `eigenvector_centrality` | Continuous | 加权特征向量中心性（网络不收敛时可能为 0 或缺失填 0）。 |
| `population_million` | Continuous | 都市区人口（百万）；Step6 外部表。 |
| `gdp_per_capita` | Continuous | 国家人均 GDP（现价美元，约 2023）；Step6。 |
| `education_tertiary_pct` | Continuous | 国家高等教育毛入学率（%）；Step6。 |
| `internet_users_pct` | Continuous | 国家互联网用户占比（%）；Step6。 |
| `rd_expenditure_pct` | Continuous | 国家研发支出占 GDP（%）；Step6。 |
| `research_capacity` | Count | QS top-500 等高校个数的城市代理；Step6。 |
| `timezone_utc` | Continuous | 由经度粗略推算的 UTC 偏移（小时，0.5 步长）。 |
| `region` | Categorical | 宏观区域（如 East Asia、Europe、North America）。 |
| `origination_rate_pop` | Continuous | 每百万人口的创始事件强度；分母为 `population_million×10⁶`。 |
| `adoption_rate_pop` | Continuous | 每百万人口的采纳项目强度。 |
| `collaboration_rate_pop` | Continuous | 每百万人口的协作边权总和强度。 |
| `cluster` | Ordinal | K-means 等聚类赋予的簇编号（分析阶段写回；非 Step6 默认列）。 |
| `role` | Categorical | 对 `cluster` 的语义标签（如 Global Innovation Hub）；分析阶段写回。 |

**`city_project_adoption_events.csv`（城市–项目采纳事件）**

| Variable | Type | Definition |
| :--- | :--- | :--- |
| `city` | Categorical | 城市名。 |
| `project_id` | Identifier | 项目键：GitHub 为 `owner/repo`，HF 为 `hf_*` 前缀键。 |
| `global_origin_month` | Discrete | 项目全局起源月 `YYYYMM`。 |
| `city_first_adoption_month` | Discrete | 该城首次与该项目的关联月 `YYYYMM`。 |
| `lag` | Count | `city_first_adoption_month` 相对 `global_origin_month` 的滞后月数（≥0）。 |
| `is_originator` | Binary | 该城是否为该项目的创始方（1/0）。 |

**`city_collaboration_edges.csv`（城市对协作边，聚合）**

| Variable | Type | Definition |
| :--- | :--- | :--- |
| `source_city` | Categorical | 无向对中字典序较小（或规则化）的一端城市。 |
| `target_city` | Categorical | 无向对的另一端城市。 |
| `edge_weight` | Count | 两城**共同关联**的“项目单元”数（GitHub：同库多城；HF：每条衍生关系计 1 个命名空间单元）。 |
| `shared_projects` | Count | 与 `edge_weight` 在本流水线中同步累加，数值上与 `edge_weight` 一致。 |

**`city_collaboration_edges_monthly.csv`（城市对 × 月协作快照）**

| Variable | Type | Definition |
| :--- | :--- | :--- |
| `source_city` | Categorical | 同聚合表。 |
| `target_city` | Categorical | 同聚合表。 |
| `month` | Discrete | 该协作边被归因到的日历月 `YYYYMM`（由参与项目的创建月/衍生月进入月度集合）。 |
| `edge_weight` | Binary / Count | 当前实现中对每个 `(source,target,month)` 记为 **1**（该月至少存在一条归因协作）。 |

**`prominent_projects_master.csv`（重要项目主表，`data/processed/`）**

| Variable | Type | Definition |
| :--- | :--- | :--- |
| `project_id` | Identifier | 统一项目主键（如 `gh_*`、`hf_*`）。 |
| `platform` | Categorical | `GitHub` 或 `HuggingFace`。 |
| `full_id` | Identifier | 平台原生全名（repo 全名或 HF id）。 |
| `project_name` | Categorical | 展示用短名。 |
| `hf_type` | Categorical | HF 资源类型；GitHub 行为空。 |
| `tags` | Categorical | 标签字符串（多标签以分号等分隔）。 |
| `metric_stars` | Count | GitHub stars；HF 行常为空或 0。 |
| `metric_forks` | Count | GitHub forks；HF 行常为空或 0。 |
| `metric_downloads` | Count | HF downloads；GitHub 行常为空。 |
| `metric_likes` | Count | HF likes；GitHub 行常为空。 |
| `created_at` | Categorical | ISO8601 创建时间字符串。 |
| `open_ai_related` | Binary | 是否与开放/AI 主题相关（筛选字段）。 |
| `ai_evidence` | Categorical | 主题证据标签串。 |
| `ai_confidence` | Ordinal | 规则/模型给出的置信档位（如 high/medium/low）。 |
| `prominent_flag` | Binary | 本表仅保留 **prominent_flag = 1** 的重要项目。 |

**新增特征构造方法**：
- #5–6：从 `city_project_adoption_events.csv` 按城市聚合 lag 的均值和标准差
- #7：从 `city_collaboration_edges.csv` 计算每个城市跨洲协作权重占总协作权重的比例
- #8：项目流行度在平台内做百分位排名（GitHub 用 stars, HuggingFace 用 downloads），计算每城市参与项目中 top-25% 占比
- #9：同上，但仅限 `is_originator=1` 的事件（origination_count<5 的城市填充全局均值以抑制小样本极端值）
- #10：每个城市内部计算 lag 与 popularity_pctile 的 Pearson 相关系数（负值=趋势引领，正值=趋势追随）
- #11：GitHub 项目的 forks/stars 比值按城市取均值（高值=项目被实际 fork/修改多，实用性强）

#### 多重共线性诊断（VIF）与 `weighted_degree` 移除

初始 12 维特征矩阵存在严重多重共线性：

| 特征 | VIF (12D) | 问题 |
|---|---|---|
| `log_adoption` | **60.85** | 🔴 与 `log_degree` r=0.973 |
| `log_degree` | **56.41** | 🔴 与 `log_adoption` 近乎完全共线 |
| `log_origination` | 12.38 | ⚠️ 与 adoption/degree 强相关 |
| `log_betweenness` | 7.63 | ⚠️ 与 degree r=-0.912 |
| `log_avg_lag` | 6.23 | ⚠️ 与 origination r=-0.726 |
| 其余 7 个新特征 | 全部 < 3.2 | ✅ 无共线性问题 |

**决策**：移除 `weighted_degree`（VIF=56.41）。理由：(1) 与 `adoption_count` 的 Pearson r=0.973，在 K-Means 欧氏距离中等同于对"活动规模"维度赋双倍权重；(2) `adoption_count` 更直接对应 RQ（采纳广度），且概念独立性更强；(3) 移除后 VIF 显著改善（log_adoption 从 60.85 降至 14.10，log_betweenness 从 7.63 降至 4.86）。

移除后 11D 的 VIF：

| 特征 | VIF (11D) | 状态 |
|---|---|---|
| `log_adoption` | 14.10 | ⚠️ 可接受（与 origination 的固有关联） |
| `log_origination` | 11.82 | ⚠️ 可接受 |
| `log_avg_lag` | 5.55 | ⚠️ 可接受 |
| `log_betweenness` | 4.86 | ✅ |
| `log_orig_rate` | 2.94 | ✅ |
| `log_lag_std` | 3.07 | ✅ |
| `cross_region` | 1.30 | ✅ |
| `pop_top25` | 1.50 | ✅ |
| `orig_top25` | 1.10 | ✅ |
| `lag_quality_corr` | 1.21 | ✅ |
| `fork_star` | 1.27 | ✅ |

#### 特征方案对比实验（K-Means k=2-8）

系统对比 6 种特征方案，评估维度扩展对聚类质量的影响：

| 方案 | 维度 | 说明 | k=3 sil | k=4 sil | k=5 sil |
|---|---|---|---|---|---|
| F: 原始 5D | 5 | origination/adoption/degree/betweenness/orig_rate | **0.386** | **0.348** | **0.377** |
| G: 5D+3 best | 8 | F + avg_lag/cross_region/lag_quality_corr | 0.247 | 0.257 | **0.277** |
| B: 11D (无 degree) | 11 | **最终方案** | 0.191 | 0.163 | 0.161 |
| A: 12D full | 12 | 含 degree（VIF 问题） | 0.171 | 0.168 | 0.167 |
| D: 10D (无 deg+betw) | 10 | 过度移除 | 0.208 | 0.148 | 0.164 |
| C: PCA 8D (95%) | 8 | 12D → PCA 保留 95% 方差 | 0.177 | 0.173 | 0.174 |

**分析**：Silhouette 从 5D 的 0.348 降至 11D 的 0.163 是**维度增加的正常代价**（curse of dimensionality 使欧氏距离区分力下降），不代表聚类更差。11D 聚类的关键优势：成功分离出原 5D 中缺失的 **Global Bridge** 角色（cross_region_ratio=0.950），正好对应 RQ1 中预期但 5D 未能识别的 "bridge cities"。

#### 11D DBSCAN & GMM 对比

**DBSCAN（11D）**：
- eps×min_samples 全网格搜索 → 最佳：eps=2.25, ms=3 → 仅 2 个簇 + 17.6% 噪声，silhouette=0.424
- 11D 空间仍无明显密度间隙 → **DBSCAN 不适合此数据**

**GMM（11D）**：
- BIC 最优 k=3（3759.9），AIC 最优 k=6 → 两准则分歧大
- GMM(k=4) silhouette=0.138，远低于 K-Means(k=4) 的 0.163
- **GMM 未提供改善**

**结论**：11D K-Means k=4 作为最终方案。Silhouette=0.163 虽低于 5D 版本的 0.348，但 11D 聚类成功识别出四类角色（Global Hub / Active Collaborator / Global Bridge / Peripheral），其中 Global Bridge 是新增特征带来的重要发现。稳定性检验：10 个随机种子下 ARI 均值 0.725，聚类结果可重复。

#### 探索但排除的候选变量（完整记录）

**A. 内生网络/活动变量**

| 候选变量 | 含义 | 排除原因 | max\|r\| |
|---|---|---|---|
| `weighted_degree` | 加权度中心性 | 与 `adoption_count` r=0.973, VIF=56.41；移除后 VIF 从 60.85 降至 14.10 | 0.973 |
| `collaboration_count` | 协作总量 | 与 `weighted_degree` 完全共线 (ρ=1.0) | 1.000 |
| `eigenvector_centrality` | 特征向量中心性 | Spearman=0.999 与 `weighted_degree`，排序几乎完全一致 | 0.999 (Spearman) |
| `adoption_rate_pop` | 人均采纳率 | 与 `origination_rate_pop` r=0.876，加入后给"人均"维度过高权重 | 0.876 |
| `collaboration_rate_pop` | 人均协作量 | 与 `adoption_rate_pop` r=0.980，三个人均率本质度量同一概念 | 0.980 |
| `origination_rate` | 按 entity_count 的创始率 | 已有按人口的 `origination_rate_pop`，口径不同但高度相关 | — |
| `adoption_rate` | 按 entity_count 的采纳率 | 同上 | — |

**B. 时间维度变量**

| 候选变量 | 含义 | 排除原因 | max\|r\| |
|---|---|---|---|
| `median_lag` | 中位数采纳滞后 | 与 `avg_lag` r=0.909，保留 avg_lag 即可 | 0.909 |
| `active_span_months` | 城市参与时间跨度（月） | 方差极低 (mean=46.7, std=5.3)，绝大多数城市跨度 45–51 月，无区分力 | 0.613 |
| `early_adopt_ratio` | lag≤3 月的采纳占比 | 与 `origination_count` r=0.745，中等偏高冗余 | 0.745 |
| `growth_ratio` | 后期/前期采纳数 | 偏态严重 (raw skew=6.55, log1p=1.43)，小样本城市极端值不稳定；适合作为聚类后 profiling 变量 | 0.375 |

**C. 协作结构变量**

| 候选变量 | 含义 | 排除原因 | max\|r\| |
|---|---|---|---|
| `clustering_coeff` | 局部聚类系数 | 与 `adoption_count` r=0.925，高度冗余 | 0.925 |
| `unique_partners` | 无权度（合作城市数） | 与 `betweenness` r=0.875，高度冗余 | 0.875 |
| `avg_collab_weight` | 每条边平均协作强度 | 与 `weighted_degree` r=0.982，几乎完全冗余 | 0.982 |
| `intl_collab_ratio` | 跨国协作占比 | 与 `cross_region_ratio` r=0.622 且分布左偏 (mean=0.889)，选择后者 | 0.315 |
| `avg_partner_betweenness` | 协作伙伴平均 betweenness | 方差过低 (std=0.0014) | — |
| `avg_partner_degree` | 协作伙伴平均 degree | 方差过低 (std/mean≈13%) | — |
| `weighted_partner_degree` | 加权协作伙伴 degree | 方差过低 (std/mean≈4%) | — |

**D. 项目质量/组合变量**

| 候选变量 | 含义 | 排除原因 | max\|r\| |
|---|---|---|---|
| `total_stars` | 城市参与项目总 star 数 | 与 `weighted_degree` r=0.981，完全冗余 | 0.981 |
| `total_downloads` | 城市参与项目总下载量 | 与 `adoption_count` r=0.798，高度冗余 | 0.798 |
| `max_stars` | 城市最高 star 项目 | 与 `betweenness` r=0.623 | 0.623 |
| `max_popularity_pctile` | 城市最高流行度百分位 | 与 `betweenness` r=0.785 | 0.785 |
| `avg_stars` | 城市参与项目平均 star | 与 `weighted_degree` r=0.440 | 0.440 |
| `avg_downloads` | 城市参与项目平均下载 | 覆盖率仅 69/148 (47%)，HF 城市才有值 | 0.190 |
| `avg_popularity_pctile` | 城市平均流行度百分位 | 与 `pop_top25_share` r=0.888，保留后者 | 0.888 |
| `median_popularity_pctile` | 城市中位流行度百分位 | 与 `pop_top25_share` r≈0.8，同组冗余 | — |
| `avg_engagement_pctile` | 城市平均参与度百分位 | 与 `pop_top25_share` r≈0.8，同组冗余 | — |
| `adopt_avg_popularity` | 采纳项目平均流行度 | 与 `avg_popularity_pctile` r=0.926，同组冗余 | 0.926 |
| `adopt_top25_share` | 采纳项目 top25% 占比 | 与 `pop_top25_share` r=0.929，同组冗余 | 0.929 |
| `eng_top25_share` | 参与度 top25% 占比 | 与 `pop_top25_share` 同组 | 0.354 |
| `eng_top10_share` | 参与度 top10% 占比 | 与 `weighted_degree` r=0.441 | 0.441 |
| `pop_top10_share` | 流行度 top10% 占比 | 与 `avg_lag` r=0.474，且为 top25 同组 | 0.474 |
| `pop_top5_share` | 流行度 top5% 占比 | 与 `weighted_degree` r=0.458 | 0.458 |
| `popularity_spread` | 流行度百分位标准差 | 与 `popularity_gini` r=0.897，镜像指标 | 0.897 |
| `popularity_gini` | 流行度 Gini 系数 | 与 `avg_popularity_pctile` r=0.939 | 0.939 |
| `star_concentration` | top-1 项目 star 集中度 | 与 `betweenness` r=0.817 | 0.817 |
| `adoption_selectivity` | 采纳流行度偏差 | 与 `pop_top25_share` r=0.807，保留后者 | 0.807 |
| `adopt_bottom25_share` | 采纳 bottom25% 占比 | std 仅 0.048，高值城市小样本 (Bogota n=3)，区分力弱 | 0.286 |

**E. 项目属性/行为变量**

| 候选变量 | 含义 | 排除原因 | max\|r\| |
|---|---|---|---|
| `project_diversity` | 项目组合 Shannon 熵 | 与 `adoption_count` r=0.988，退化为 log(项目数) | 0.988 |
| `innovation_balance` | origination/(orig+adopt) | 与 `origination_count` r=0.788 + `avg_lag` r=0.784，多重中度冗余 | 0.788 |
| `orig_top50_rate` | 创始项目 top50% 率 | 与 `orig_top25_share` r=0.614，保留后者 | 0.614 |
| `orig_median_popularity` | 创始项目中位流行度 | 与 `orig_top25_share` r=0.665，保留后者 | 0.665 |
| `engagement_premium` | 参与度-流行度差值 | 与 `adopt_bottom25_share` r=0.721，且 std 仅 0.036 | 0.304 |
| `avg_proj_recency` | 参与项目平均创建时间 | 独立性极好 (max\|r\|=0.158) 但 std≈1.6 月，实质差异太小无区分力 | 0.158 |
| `github_share` | GitHub 平台占比 | 方差≈0 (mean=0.995, std=0.008)，几乎所有城市 99%+ GitHub | — |
| `orig_adopt_overlap` | 创始-采纳项目重叠率 | 全部为 0，无区分力 | — |
| `hf_share` | HuggingFace 占比 | median=0，大多数城市无 HF 参与，太偏态 | 0.674 |
| `platform_count` | 参与平台数 (1 or 2) | 二元变量，K-Means 不适合 | — |
| `lag_quality_corr` (已保留) | — | — | — |
| `avg_fork_star_ratio` (已保留) | — | — | — |

### ✅ 5.1.5 参数敏感性与替代模型对比（Step 9 扩展，§9.6–9.9）

> 注：以下 §9.6–9.9 为 5D 原始聚类时的结果记录。11D 版本的 DBSCAN/GMM/参数敏感性对比见上方 §5.1.4b。

**§9.6 K-Means 参数敏感性（n_init=50，5D）**：

| k | Silhouette | CH Index | DB Index | 解读 |
|---|---|---|---|---|
| k=3 | **0.386** | 151.8 | **0.869** | 统计最优，但合并 Active Collaborator 层，丢失理论中间角色 |
| k=4 | 0.348 | 143.0 | 0.959 | 匹配四角色框架，指标接近 k=3，解释性最佳 |
| k=5 | 0.377 | 140.2 | 0.907 | 拆分 Peripheral 为两组，可解释性下降 |

- 增大 n_init (20→50) 后聚类结果完全不变 → 原始结果已收敛稳定
- k=3 统计指标最优但理论解释力不足；k=5 边际改善有限但增加复杂度 → **k=4 是最佳折衷**

**§9.7 DBSCAN 密度聚类（5D）**：

- k-distance 图 + eps×min_samples 网格搜索 → 最佳配置：eps=0.8, min_samples=5
- 结果：仅 **2 个簇** + 22 个噪声点 (14.9%)，silhouette=0.299
- 数据特征分布平滑、无明显密度间隙 → DBSCAN 不适合该数据集
- 但 22 个噪声城市可作为 **异常值鲁棒性检验**，标记不属于任何密度簇的边缘城市

**§9.8 GMM 高斯混合模型（5D 软聚类）**：

- BIC/AIC 模型选择：BIC 最优 k=2, AIC 最优 k=8 → 两个信息准则分歧较大
- GMM(k=4) silhouette=0.278，低于 K-Means(k=4) 的 0.348
- 仅 8 个城市 (5.4%) 最大分配概率 <0.7 → 绝大多数城市分配确定
- GMM(k=4) vs K-Means(k=4) ARI=0.340, NMI=0.407 → 中等一致性
- GMM 的软分配概率可量化"边界城市"的归属不确定性，用于识别潜在 bridge cities

**§9.9 综合对比（5D）**：

| 方法 | 簇数 | Silhouette | CH Index | DB Index | 噪声% |
|---|---|---|---|---|---|
| K-Means k=3 | 3 | **0.386** | **151.8** | **0.869** | 0 |
| K-Means k=5 | 5 | 0.377 | 140.2 | 0.907 | 0 |
| **K-Means k=4** ← 保留 | **4** | **0.348** | **143.0** | **0.959** | **0** |
| GMM k=3 | 3 | 0.284 | 107.2 | 1.084 | 0 |
| GMM k=4 | 4 | 0.278 | 75.5 | 1.216 | 0 |
| GMM k=5 | 5 | 0.234 | 91.3 | 1.146 | 0 |
| DBSCAN | 2 | 0.299 | — | — | 14.9% |

- 跨方法 ARI 热力图：K-Means 各 k 之间一致性高 (ARI≈0.4–0.7)，GMM 与 K-Means 中等一致，DBSCAN 与其他方法一致性低
- **最终决策（5D 阶段）**：K-Means k=4 作为主模型
- **V1.3 更新（11D）**：扩展至 11 维后，K-Means k=4 仍为最优选择（见 §5.1.4b），新增特征成功分离出 Global Bridge 角色

## 5.2 Method 2: Adoption-lag regression

Purpose: model how quickly cities adopt prominent open-AI projects after each project’s first global appearance

Addresses: RQ2（城市特征与创新导向角色、项目采纳广度），对应 Step10 Model B/C 及附录模型

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

**执行文件**：`step10_adoption_regression.ipynb`（28 个 cells，全部已执行，含多轮优化 + V1.2 新增 10.5d 正则化检验）

**实际建模策略调整**：由于 adoption lag 的分布特征（mean=6.28, median=2, 大量 lag=0 的 originator 事件），将原方案的连续 lag 回归调整为三个互补模型：

| 模型 | DV | 分析单位 | n | 方法 | 核心结果 |
|------|-----|---------|---|------|----------|
| **Model A** | `is_originator` (0/1) | 城市×项目 | 39,158 | Logistic (clustered SE) | Pseudo R²=0.090 |
| **Model B** | `originator_share` | 城市 | 148 | OLS (HC1) + Beta 回归 | R²=0.247, Adj R²=0.198 |
| **Model C** | `log1p(avg_iei)` | 城市 | 148 | OLS (HC1) + Region FE | R²=TBD（重算中） |

**Model C DV 调整说明（V1.3 优化）**：原 Model C 的 DV 经两次调整：(1) V1.2 从 `log(adoption_count)` 改为 `log(avg_lag_nonorig)` 以消除 tautology；(2) **V1.3 进一步从 `log(avg_lag)` 改为 `log1p(avg_iei)`**（城市级平均 Inter-Event Interval），原因：avg_lag 对老项目天然偏大（项目年龄混淆），IEI 仅衡量该城市相对于前一个采纳城市的响应速度，与 Step 11 Model D-reg-IEI 保持因变量一致，方法论层次更清晰。IEI 计算：按 project_id + 采纳月份排序，取相邻采纳城市的月数差，过滤 lag>0 & interval≥0 事件后按城市取均值。原 adoption breadth 模型降级为 Appendix 10.4b。

**关键发现**：
- **Models A/B（origination）**：`log_entity`（开发者基数）和 `log_degree`（网络中心性）是最强预测变量。`log_degree` 对 origination 为负效应 → 高连接城市更善于采用而非发起
- **Model C（IEI 速度）**：结果待重算，预期方向与 avg_lag 版相近；DV 改为 IEI 后消除了项目年龄混淆，与 **Step 11 V1.5**（事件级 XGBoost + IEI，**CV R²≈0.31**，SHAP 项目侧主导）在因变量定义和结论层面更一致。两层均支持：采纳时机**主要由项目异质性驱动**，城市特征为边际信号
- 外部属性（education、internet、R&D、research_capacity）在所有主模型中均不显著 → 网络结构比城市静态属性更重要
- **Adoption speed null finding 的学术价值**：开放 AI 项目在全球城市间的扩散在速度维度上是相对平等的，即使在广度和发起能力上高度集中

**9 个自变量**：log_degree, log_population, log_gdp, education_tertiary_pct, internet_users_pct, rd_expenditure_pct, research_capacity, betweenness, log_entity。特征集与 Step 11/12 完全一致。

**Robustness Checks**：
- **10.3b Beta 回归**：originator_share 为 [0,1] 比例变量，Beta 回归确认 OLS 结论稳健（系数方向一致）
- **10.4b Tautology 量化（Appendix）**：adoption breadth model R²=0.970；仅用外生变量 R²=0.737 → 循环变量贡献 24.0% R²。证实速度模型更合理
- **10.5b 局限性讨论**：内生性/tautology、截面因果限制、样本量约束、网络密度对 betweenness 的影响、adoption speed null finding
- **10.5c Region FE 检验**：加入区域固定效应后核心结论不变
- **10.5d 正则化稳健性检验（V1.2 新增）**：Ridge/Lasso/ElasticNet 5-fold CV 对比 OLS。log(adoption) Lasso CV R²=0.62 优于 OLS 的 0.60，系数稳定；originator_share 和 log(avg_iei) 所有方法均 CV R²<0（与 avg_lag 版结论一致）。Lasso 特征选择将 betweenness 收缩为零。含 Ridge/Lasso 系数对比可视化

**已删除的冗余模块（V1.2 精简）**：
- ~~10.2b 项目固定效应~~：Conditional Logit with project FE 核心结论与 pooled Model A 完全一致，但 85% 的项目因无 outcome 变异被排除
- ~~10.4c 网络密度检验~~：该检验验证的是旧 DV（adoption_count），与新 Model C（IEI）无关

**与方案对比**：方案预期连续 lag 回归 + project FE。实际执行调整为三模型策略（logistic + share OLS/Beta + speed OLS），并将 DV 从 adoption breadth 调整为 adoption speed 以避免 tautology。V1.2 新增正则化稳健性检验（10.5d），从 Step 11 接收 Ridge/Lasso 代码，确保所有线性方法集中在 Step 10。

## 5.3 Method 3: XGBoost

Purpose: explain how city characteristics relate to adoption speed in the ecosystem of prominent open-AI projects, using non-linear tree-based methods

Addresses: RQ3（城市特征与项目采纳速度），对应 Step11 Model D-reg

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

### ✅ 5.3.5 实际执行结果（Step 11, **V1.5**）

**执行文件**：`step11_xgboost_shap.ipynb`（约 8 个代码单元；**papermill 已跑通**）

**职责划分**：
- **Step 10** = 线性/参数方法（OLS、Beta、Ridge、Lasso、ElasticNet 等）→ 推断 + 稳健性
- **Step 11** = **XGBoost + SHAP** → **城市–项目事件**层面 adoption **速度**（`log1p(lag)`）的非线性可解释建模

**模型与验证**：`XGBRegressor`（`n_estimators=1000`, `max_depth=6`, `learning_rate=0.03`, `subsample=0.8`, `colsample_bytree=0.8`, `tree_method=hist`）；`KFold(5)`；**CV R²（log-lag）= 0.3023 ± 0.0160**（`n≈25,297`, `lag>0`）。

**特征（17）**：11 城市 + `log_proj_pop` + `proj_origin_idx` + `log_stars` + `log_forks` + `popularity_pctile` + `fork_star_ratio`（项目表见 `prominent_projects_master.csv`）。

**SHAP**：`TreeExplainer`；全局 mean|SHAP| **Top-5** 为 **项目侧**：`proj_origin_idx`, `log_proj_pop`, `log_forks`, `fork_star_ratio`, `popularity_pctile`；城市块中 `log_population`, `origination_rate`, `eigenvector_centrality` 等仍有边际贡献。

**沿革**：V1.2 删 E/F；V1.3 删 **Model D（分类）**，仅保留 D-reg；**V1.4** 将 D-reg 升级为 **XGBoost** 并加入**事件级项目属性**（见 §0.3 **优化 9**）。`requirements.txt` 已加入 `xgboost`。

**与方案对比**：城市级 n=148 不适合树回归；Step 11 定为**大样本事件级** XGBoost + SHAP，与 Step 10 分工。

## 5.4 Method 4: GraphSAGE

Purpose: predict which cities are likely to become the next adopters of prominent open-AI projects

Addresses: RQ4（协作网络预测下一波 adopter 城市），对应 Step12 GraphSAGE

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

**执行文件**：`step12_graphsage.ipynb`（16 个 code cells，含 MLP 消融基线 + 消融实验）

**实际任务定义调整**：由于所有 148 个活跃城市都有采用事件（无"未采用"城市），将二分类 next-adopter 任务调整为 **adoption intensity prediction**：

| 模型 | DV | 方法 | Test 表现 |
|------|-----|------|-----------|
| **G1** (回归) | `log(adoption_count)` 后半期 | GraphSAGE 2-layer | **R²=0.914, RMSE=0.436** |
| **G2** (分类) | high/low adopter (中位数分割) | GraphSAGE 2-layer | **AUC=0.960, F1=0.857** |
| MLP 消融 (回归) | 同 G1 | MLP 2-layer (无图) | R²=0.768, RMSE=0.713 |
| MLP 消融 (分类) | 同 G2 | MLP 2-layer (无图) | AUC=0.964, F1=0.933 |

**图结构**：
- 148 节点，9,297 无向边，10 维节点特征（6 外生 + 4 训练期活动，已修复特征泄漏）
- 时间分割：train ≤ 202406，test > 202406
- 分层划分：Train 88 / Val 30 / Test 30

**关键发现**：
- 城市排名预测 Spearman ρ=0.960 (全部) / ρ=0.956 (test only)，p<0.001
- GraphSAGE 回归 ΔR²=+0.145 (vs MLP)，证明协作网络结构确实为采用预测提供了增量信息
- 去掉 train_weighted_degree 后，图结构增量反而扩大至 ΔR²=+0.367，说明图传播可部分替代该特征
- 分类任务上 MLP AUC ≈ GraphSAGE AUC，说明二分类过于简单，图结构无额外增益

**与方案对比**：方案原定预测"是否成为新 adopter"的二分类；实际调整为"采用强度"的回归+分类双任务 + MLP 消融基线，避免了全城市均为 adopter 导致的标签无区分问题。V1.2 版本修复了特征泄漏（全时段 adoption_count 等改为训练期活动特征）、增加了验证集与 early stopping、并通过 MLP 消融实验量化了图结构的增量贡献。

## 5.5 Method 5: 技术类型交互回归（Step 13, RQ5）

Purpose: examine whether the effects of city characteristics on adoption speed vary across AI technology types

Addresses: RQ5（城市特征对扩散速度的影响是否因技术类型而异），对应 Step 13

### 5.5.1 前置：技术类型分类

基于项目已有的 `ai_evidence`（GitHub）和 `tags` / `pipeline_tag`（HuggingFace）字段，对 23,481 个 prominent 项目进行规则化分类。原 LLM/NLP 占比 76.5%，拆分为 3 子类后最大类降至 30.3%。

**分类规则**（优先级从高到低：越稀有越优先，避免大类"吞噬"小类）：

| 优先级 | 类别 | 判定规则 | 概念定义 |
|--------|------|---------|---------|
| 1 | **Multimodal** | multimodal, image-text-to-text, visual-question-answering, document-question-answering, image-to-text, any-to-any, clip, vision-language | 跨模态融合项目 |
| 2 | **Vision/Image** | computer-vision, diffusion, stable-diffusion, text-to-image, image-classification, object-detection, image-segmentation, image-to-image, depth-estimation, text-to-video, video-classification | 视觉/图像/视频生成与理解 |
| 3 | **Speech/Audio** | tts, text-to-speech, whisper, automatic-speech-recognition, audio-classification, text-to-audio, voice-activity-detection | 语音/音频处理 |
| 4 | **Agent** | agent, ai-agent | AI Agent 框架与工具 |
| 5 | **NLP-Traditional** | text-classification, token-classification, summarization, translation, fill-mask, sentence-similarity, question-answering, zero-shot-classification, table-question-answering | 传统 NLP 下游任务（预 LLM 范式） |
| 6 | **LLM-Foundation** | 含具体模型族名 llama, qwen, deepseek, mistral, gemma, falcon, bloom, chatglm, rwkv, mamba, gpt-neox, phi, large-language-model, language-model；或 HF model 类型 + text-generation 标签 | 基础模型权重、预训练/微调模型（需算力、科研） |
| 7 | **LLM-Application** | 含 chatgpt, gpt, rag, prompt, prompt-engineering, embedding, langchain, openai, chatbot；或仅含泛化标签（llm, generative-ai, transformer, deep-learning, conversational 等） | 基于 LLM 的工具、框架、应用（门槛低、依赖网络生态） |

多标签冲突时按上述优先级分配唯一主类别。`conversational` 标签从 NLP-Traditional 移除（93% 与 LLM 重叠）。Video (84 项目) / RL (204 项目) 归入 Other 排除出回归。

**LLM 拆分标准**：

| 子类 | 判定逻辑 | 对应"项目类型" |
|------|---------|---------------|
| **LLM-Foundation** | 含特定模型族名（llama, qwen, deepseek 等）或 HF model + text-generation | 基础模型权重、预训练/微调 |
| **LLM-Application** | 含应用层标签（chatgpt, rag, prompt 等）或仅含泛化 AI 标签 | 基于 LLM 的工具、框架、应用 |
| **NLP-Traditional** | 含下游任务标签（classification, summarization 等） | 传统 NLP 任务，预 LLM 范式延续 |

**拆分理由**：Foundation 需算力与科研能力；Application 门槛低、依赖开发者网络生态传播；NLP-Traditional 是前 LLM 时代延续——三者扩散机制本质不同。

### ✅ 5.5.2 实测分类结果

**全部 Prominent 项目 (n=23,481)**

| 类别 | 项目数 | 占比 |
|------|--------|------|
| LLM-Foundation | 5,842 | 24.9% |
| LLM-Application | 5,552 | 23.6% |
| Vision | 3,440 | 14.7% |
| NLP-Traditional | 2,319 | 9.9% |
| Agent | 2,240 | 9.5% |
| Multimodal | 1,926 | 8.2% |
| Speech/Audio | 1,217 | 5.2% |
| Unclassified | 670 | 2.9% |
| Other (RL/robotics/mlops) | 275 | 1.2% |

**采用事件 (n=39,158)**

| 类别 | 事件数 | 占比 |
|------|--------|------|
| LLM-Application | 11,863 | 30.3% |
| Agent | 9,081 | 23.2% |
| LLM-Foundation | 7,431 | 19.0% |
| Vision | 3,997 | 10.2% |
| Multimodal | 2,854 | 7.3% |
| Speech/Audio | 1,414 | 3.6% |
| NLP-Traditional | 1,290 | 3.3% |
| Unclassified | 858 | 2.2% |
| Other | 370 | 0.9% |

排除 Unclassified + Other 后有效事件：**37,930**（96.9%），覆盖率充足。

**观察**：Agent 在采用事件中占比 23.2%（高于项目占比 9.5%）→ Agent 项目平均被更多城市采纳，传播广泛。NLP-Traditional 在采用事件中仅 3.3%（低于项目占比 9.9%）→ 传统 NLP 项目平均被更少城市采纳。

### 5.5.3 回归设定

```
log1p(IEI)_ij = β₀ + β₁·Z_city_i + β₂·D_tech_j + β₃·(Z_city_i × D_tech_j) + γ·Proj_controls_j + ε_ij
```

- i = 城市 (148), j = 项目, ij = 城市-项目采用事件 (n = 24,434, lag > 0)
- DV：`log1p(inter-event interval)`（与 Step 11 §11.2 一致的扩散速度定义）
- `Z_city_i`：9 个城市特征（z-scored，与 Step 10/11 一致：log_degree, log_entity, log_population, log_gdp, education_tertiary_pct, internet_users_pct, rd_expenditure_pct, research_capacity, betweenness）
- `D_tech_j`：6 个技术类型虚拟变量（LLM-Application 为参照组）
- `β₃`：**核心兴趣**——54 个交互项（9 特征 × 6 dummy），检验城市特征效应的技术类型异质性
- `Proj_controls_j`：6 个项目层控制变量（log_proj_pop, proj_origin_idx, log_stars, log_forks, popularity_pctile, fork_star_ratio，与 Step 11 一致）
- 方法：**OLS**（普通最小二乘法）

### 5.5.4 交互项矩阵（9 特征 × 6 dummy = 54 项）

| 城市特征 \ 技术类型 | D1: LLM-Found | D2: NLP-Trad | D3: Vision | D4: Agent | D5: Multimodal | D6: Speech |
|-------------------|:---:|:---:|:---:|:---:|:---:|:---:|
| X1: log_degree | #1 | #2 | #3 | #4 | #5 | #6 |
| X2: log_entity | #7 | #8 | #9 | #10 | #11 | #12 |
| X3: log_population | #13 | #14 | #15 | #16 | #17 | #18 |
| X4: log_gdp | #19 | #20 | #21 | #22 | #23 | #24 |
| X5: education | #25 | #26 | #27 | #28 | #29 | #30 |
| X6: internet | #31 | #32 | #33 | #34 | #35 | #36 |
| X7: rd_expenditure | #37 | #38 | #39 | #40 | #41 | #42 |
| X8: research_cap | #43 | #44 | #45 | #46 | #47 | #48 |
| X9: betweenness | #49 | #50 | #51 | #52 | #53 | #54 |

总参数：9 (城市主效应) + 6 (tech dummy) + 54 (交互) + 6 (项目控制) + 1 (截距) = 76；参数/样本比 1:321。

### ✅ 5.5.5 实际执行结果（Step 13）

**执行文件**：`step13_tech_type_interaction.ipynb`（22 cells，已完成执行）

**模型表现**：

| 指标 | 值 |
|------|-----|
| R² | 0.284 |
| Adj R² | 0.282 |
| F-stat | 128.67 (p ≈ 0) |
| 观测数 | 24,434 |
| 参数数 | 76 |

**问题 1 结论：不同技术类型传播速度显著不同**

tech_type 主效应（相对 LLM-Application 参照组）：

| 技术类型 | 系数 | p 值 | 含义 |
|---------|------|------|------|
| LLM-Foundation | −0.010 | 0.486 | 与 LLM-App 无显著差异 |
| NLP-Traditional | +0.083 | 0.127 | 传播略慢（不显著） |
| **Vision** | **−0.049** | **0.004** | **传播显著更快** |
| **Agent** | **+0.029** | **0.015** | **传播显著更慢** |
| Multimodal | +0.009 | 0.643 | 无显著差异 |
| **Speech** | **+0.048** | **0.046** | **传播显著更慢** |

Vision 在城市间传播最快；Agent 和 Speech 传播最慢。

**问题 2 结论：城市特征效应因技术类型而异**

联合 F 检验（54 个交互项 = 0）：**F = 1.388, p = 0.031**（显著）

显著交互项（7/54, p < .10; 5/54, p < .05）：

| # | 交互项 | 系数 | p | 解读 |
|---|--------|------|---|------|
| 1 | log_entity × LLM-Foundation | +0.184 | **0.003** | 开发者多的城市，基础模型反而传播更慢（vs LLM-App） |
| 2 | log_degree × LLM-Foundation | −0.166 | **0.013** | 网络中心性高的城市，基础模型传播更快 |
| 3 | log_population × Vision | −0.060 | **0.022** | 大城市中 Vision 项目传播更快 |
| 4 | log_population × Multimodal | −0.073 | **0.028** | 大城市中 Multimodal 项目传播更快 |
| 5 | log_population × Speech | −0.084 | **0.033** | 大城市中 Speech 项目传播更快 |
| 6 | rd_expenditure × LLM-Foundation | −0.038 | 0.058† | 高 R&D 城市，基础模型传播更快 |
| 7 | log_population × LLM-Foundation | −0.040 | 0.074† | 大城市中基础模型传播更快 |

Block F 检验（技术类型是否调节各城市特征）：

| 城市特征 | F | p | 显著性 |
|---------|---|---|--------|
| **log_population** | **2.223** | **0.038** | **\*** |
| log_entity | 1.908 | 0.076 | † |
| research_capacity | 1.307 | 0.250 | |
| log_degree | 1.262 | 0.271 | |
| rd_expenditure_pct | 1.121 | 0.347 | |
| education_tertiary_pct | 0.795 | 0.574 | |
| betweenness | 0.521 | 0.793 | |
| internet_users_pct | 0.419 | 0.867 | |
| log_gdp | 0.226 | 0.968 | |

**城市规模（log_population）是唯一被技术类型显著调节的城市特征**：非文本类技术（Vision/Multimodal/Speech）在大城市的传播优势比文本类技术（LLM-App/Agent）更强。

**稳健性检验**（DV = log(1+lag)）：R² = 0.152；交互项系数符号一致率 66.7%（36/54），Spearman ρ = 0.493，核心结论稳健。

### 5.5.6 核心发现与 Step 10-12 的对话

| 现有发现 | RQ5 追问 | Step 13 回答 |
|---------|---------|-------------|
| Step 10: 网络指标 > 城市静态属性 | 对所有技术类型都成立？ | **不完全成立**：log_degree 对 LLM-Foundation 有显著额外加速效应（p=.013），但对其他类型无差异 |
| Step 10: education 全样本不显著 | 是否被 LLM-App 淹没？ | education 交互项在所有类型中**均不显著**（最高 |t|=1.59），非被淹没，而是真的不重要 |
| Step 10: GDP 对速度有负效应 | 资源密集型技术 GDP 效应更强？ | GDP 交互项**全部不显著**（最高 |t|=0.76），GDP 效应不因技术类型而异 |
| Step 11: 城市特征解释力低 (R²=0.302) | 加入交互后解释力提升？ | R² = 0.284（交互模型含项目控制），**交互项增量贡献极小**，项目控制变量是主要贡献者 |
| 新发现 | — | **城市规模对非文本技术的传播有额外加速作用**，LLM-Foundation 更依赖网络中心性 |

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
2. **Which city characteristics are associated with innovation-oriented roles and project adoption breadth within the ecosystem of prominent open-AI projects?**
3. **Which city characteristics are associated with faster adoption speed of prominent open-AI projects across cities?**
4. **Can the GitHub city collaboration network help predict which cities will become the next adopters of prominent open-AI projects?**
5. **Do the effects of city characteristics on the diffusion speed of prominent open-AI projects vary across technology types (e.g., LLM foundation models, LLM applications, vision, agent, multimodal, speech)?**

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

#### 6.4.2.3 Step 3. K-means for city roles ✅ 已完成（已扩展参数敏感性 + 替代模型）

1. 使用城市层指标识别 roles
2. 输出 originators、collaboration hubs、bridge cities、late adopters 等 cluster

**实际执行（`step9_kmeans.ipynb`，41 cells）**：

**§9.1–9.5 主 K-Means 模型**：
- 聚类特征：log1p(origination_count), log1p(adoption_count), log1p(weighted_degree), log1p(betweenness×1000), log1p(origination_rate_pop) → z-score
- k=4, silhouette=0.35
- 四角色：Global Innovation Hub (27城) / Active Collaborator (56城) / Emerging Contributor (44城) / Peripheral (16城)
- 输出 Silhouette 图、Radar 雷达图、全球地图、箱线图、区域组成图

**§9.6 参数敏感性（新增）**：
- k=3/4/5 × n_init=50 对比 → k=4 在理论解释性与指标间最佳折衷
- n_init 增大不改变结果 → 原始聚类已稳定

**§9.7 DBSCAN 替代模型（新增）**：
- k-distance 图指导 eps 选择 + eps×min_samples 网格搜索
- 最佳 eps=0.8, ms=5 → 仅 2 簇 + 22 噪声 (14.9%), sil=0.299
- 不适合本数据，但噪声点可作鲁棒性检验

**§9.8 GMM 替代模型（新增）**：
- BIC/AIC 模型选择 + k=3/4/5 对比
- GMM(k=4) sil=0.278, 仅 8 城分配不确定
- 与 K-Means ARI=0.340，中等一致
- 软概率可量化边界城市不确定性

**§9.9 综合对比（新增）**：
- 7 种配置×3 指标对比表 + ARI 热力图 + PCA 投影
- 结论：K-Means k=4 作为主模型，GMM 补充不确定性，DBSCAN 标记异常

#### 6.4.2.4 Step 4. Adoption-lag regression ✅ 已完成

1. 在 城市—项目 层面计算 adoption lag
2. 分析哪些因素与更快项目采用相关
3. 可加入项目固定效应或项目控制变量

**实际执行（`step10_adoption_regression.ipynb`，28 cells）**：
- 三模型策略：Model A (Logistic, n=39,158), Model B (OLS originator_share, n=148), Model C (OLS log1p(avg_iei), n=148)
- Model C DV 经两次调整：adoption breadth → log(avg_lag) → **log1p(avg_iei)**，消除项目年龄混淆，与 Step 11 IEI 因变量一致
- 核心发现：log_entity 是最强预测因子；log_degree 对 adoption 正效应、对 originator 概率负效应；采纳速度仅与 GDP 显著相关（速度主要受项目异质性驱动）
- **Robustness Checks**：(10.3b) Beta 回归；(10.4b) 内生性检验（Appendix）；(10.5c) Region FE；**(10.5d) Ridge/Lasso/ElasticNet 正则化稳健性（V1.2 新增，从 Step 11 移入）** → 核心结论稳健

#### 6.4.2.5 Step 5. XGBoost for explanatory modelling ✅ 已完成

1. 解释哪些城市特征与 innovation-oriented roles 和 faster adoption 相关
2. 用 SHAP 做辅助解释

**实际执行（`step11_xgboost_shap.ipynb`，**V1.5**，papermill 已跑通）**：
- **职责划分**：Step 10 = 线性/参数方法（推断）；Step 11 = **XGBoost + SHAP**（事件级 **RQ3** 补充）
- **主模型 D-reg-IEI**：**城市–项目事件**，`log1p(inter-event interval)`，`XGBRegressor`（1000 棵树，depth=6，lr=0.03），**5-fold CV R²=0.3072±0.0122**，`n≈25,297`
- **17 特征**：11 城市 + 2 项目聚合 + 4 项目属性（stars/forks/流行度分位/fork-star 比，见 `prominent_projects_master.csv`）
- **4-way 敏感性**：lag/IEI × 17/15 特征，SHAP 排序稳健
- **SHAP**：`TreeExplainer`；主模型 Top-5：`log_proj_pop`, `proj_origin_idx`, `popularity_pctile`, `log_forks`, `log_stars`；城市 `betweenness` 在 IEI 下升至第 6（见 §0.3 优化 9）
- **沿革**：V1.2 删 E/F；V1.3 删 Model D（分类）；V1.4 升级 XGBoost；**V1.5 IEI + 4-way 敏感性**；`requirements.txt` 含 `xgboost`

#### 6.4.2.6 Step 6. GraphSAGE for next-wave adopter prediction ✅ 已完成

1. 基于城市协作网络与节点特征
2. 预测哪些城市会在下一期成为 prominent project 的新 adopter

**实际执行（`step12_graphsage.ipynb`）**：
- 时间分割：train ≤ 202406, test > 202406
- Model G1 (回归): Test R²=0.914, RMSE=0.436
- Model G2 (分类 high/low adopter): Test AUC=0.960, F1=0.857
- MLP 消融基线 (回归): Test R²=0.768 → 图结构增量 ΔR²=+0.145
- 城市排名 Spearman ρ=0.960 → 图结构显著提升预测能力

#### 6.4.2.7 Step 7. Technology-type interaction regression (RQ5) ✅ 已完成

1. 基于 `ai_evidence` + `tags` / `pipeline_tag` 对项目进行 7 类技术分类
2. 将 `tech_type` merge 进采用事件表
3. OLS 交互回归：`log1p(IEI) ~ Z_city + D_tech + Z_city × D_tech + Proj_controls`，76 个参数，n = 24,434
4. 稳健性：DV = log(1+lag) 替代检验

**实际执行（`step13_tech_type_interaction.ipynb`，22 cells）**：
- R² = 0.284, Adj R² = 0.282
- 3/6 tech dummy 显著：Vision 传播最快 (p=.004)，Agent (p=.015) 和 Speech (p=.046) 传播最慢
- 54 个交互项联合 F 检验 p = 0.031（显著）；5 个交互项 p < .05
- **核心发现**：城市规模（log_population）是唯一被技术类型显著调节的城市特征（block F p=.038）——非文本类技术在大城市传播优势更强；LLM-Foundation 更依赖网络中心性

#### 6.4.2.8 Step 8. Optional case-study visualisation

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

**✅ 参数敏感性与替代模型对比（新增 §9.6–9.9）**：
- k=3 统计最优 (sil=0.386) 但丢失中间角色层；k=5 拆分 Peripheral 但可解释性下降 → **k=4 最佳折衷**
- n_init 20→50 不改变结果 → 聚类已稳定收敛
- DBSCAN 仅发现 2 个密度簇 + 14.9% 噪声 → 不适合此数据，但噪声点可检验异常城市
- GMM(k=4) sil=0.278，与 K-Means ARI=0.340；仅 5.4% 城市分配不确定 → 软概率可量化边界城市
- 7 种方法配置综合对比（Silhouette / CH / DB / ARI 热力图）确认 K-Means k=4 为最优选择

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

**✅ 实际结论（V1.5 更新）**：Step 10 仍以 OLS 等描述**城市截面**上的创新/速度；**Step 11** 在**事件级**用 **XGBoost + SHAP**（主模型 `log1p(IEI)`），**CV R²≈0.31**，SHAP **项目属性与项目聚合**占主导，**城市块**中 `betweenness`（IEI 下第 6）、`origination_rate`（第 7）更突出。4-way 敏感性确认排序稳健。与传统经济/教育偏相关结论可同时写入：控制规模后 GDP / 互联网对 **adoption 广度**仍显著（Step 8/10）。

**Step 11（V1.3–V1.5）摘要**：
- **V1.3**：删除 notebook 内 **Model D（GB 分类）**，避免与已删 Step 10 Logistic 重复；**仅保留 D-reg**
- **V1.4**：D-reg 改为 **XGBoost** + 事件级项目协变量 → CV R²≈0.30
- **V1.5**：主模型因变量改为 **IEI（inter-event interval）**，CV R²≈0.31；增加 4-way 敏感性（lag/IEI × 17/15 特征）；**实质性结论不变**：采纳时机**项目驱动为主**，城市 `betweenness` 在 IEI 视角下更突出
- 城市级树回归（Model E/F）保持删除；**Ridge/Lasso** 仍在 Step 10 **§10.5d**

### 6.5.6 小节 5：Predicting next-wave adopters

预期展示：

1. GraphSAGE 的性能
2. 哪些城市在下一期最可能 adopted 新的 prominent projects
3. 预测正确与错误的案例

**✅ 实际结论**：GraphSAGE 表现优异——回归 Test R²=0.914, 分类 Test AUC=0.960/F1=0.857。城市排名 Spearman ρ=0.960 (p<0.001)。MLP 消融基线回归 R²=0.768，图结构增量 ΔR²=+0.145。进一步消融实验显示去掉 train_weighted_degree 后图结构增量扩大至 ΔR²=+0.367，证明图传播可部分替代节点度特征。图结构 + 节点特征联合建模显著优于纯特征方法，验证了协作网络对预测下一波 adopter 的价值。

### 6.5.7 小节 6：Technology-type heterogeneity in diffusion mechanisms（RQ5, Step 13）

预期展示：

1. 技术类型分类结果与采用事件分布
2. 交互回归系数表（54 个交互项）
3. 交互项森林图 / 系数对比热力图（9 城市特征 × 7 技术类型）
4. 哪些城市特征的效应因技术类型而显著不同

**✅ 实际结论**：

1. **不同技术传播速度显著不同**：Vision 传播最快（coef=−0.049, p=.004），Agent (coef=+0.029, p=.015) 和 Speech (coef=+0.048, p=.046) 传播最慢
2. **城市特征效应因技术类型而异**：54 个交互项联合 F 检验 p=0.031（显著），但个别效应有限（5/54 p<.05）
3. **城市规模是唯一被技术类型显著调节的城市特征**（block F p=.038）：非文本类技术（Vision/Multimodal/Speech）在大城市的传播优势比 LLM 类更强
4. **LLM-Foundation 更依赖网络中心性**（log_degree × LLM-Found p=.013）但在开发者多的城市反而更慢（log_entity × LLM-Found p=.003）
5. **预期假说对照**：知识门槛假说（education/research_capacity 调节）**未获支持**；GDP 门槛假说**未获支持**；网络依赖假说**部分支持**（仅 LLM-Foundation）；城市规模假说**获支持**
6. R² = 0.284（含项目控制），交互项本身增量极小——与 Step 10/11 "项目异质性主导" 结论一致

### 6.5.9 小节 8：Case-study visualisation

预期展示：

1. 1–2 个具体技术家族或代表项目的扩散时间线
2. 地图、网络图或 Sankey / timeline 图
3. 用于更直观地演示传播过程

**状态**：🔲 待完成

### 6.5.10 小节 9：Critical reflection

建议主动讨论：

1. prominent projects 的筛选规则可能引入平台偏差
2. 不同类型项目的扩散机制并不完全相同
3. adoption lag 在跨项目比较时受项目异质性影响
4. GraphSAGE 预测的是 adopter，而不是 originator emergence
5. **树回归不适合 n=148（V1.2 已解决）**；**Step 11（V1.5）** 仅保留 **Model D-reg**：**XGBoost** 事件级回归（n≈25.3k，主模型 IEI×17 **CV R²≈0.31**，含 4-way 敏感性）。线性方法归 Step 10，事件级非线性 + SHAP 归 Step 11
6. **collaboration_count ≡ weighted_degree (ρ=1.0)**：完全冗余，建模已只保留 degree
7. **Model C R²=0.965 存在循环性**：Robustness check (10.4b) 显示剔除 log_degree 后 R² 仅降 0.6%，真正的循环性来自 `entity_count` ↔ `adoption_count` 的近定义同源关系（两者在数据构建层面高度关联）。Discussion 中应明确标注 Model C 的 R² 主要反映构建循环而非因果解释力，推断应以 Model A/B 为准
8. **网络密度 0.886 导致 betweenness 不可靠**：Robustness check (10.4c) 使用 weight≥5 子网络（密度降至 0.563）重算 betweenness，发现原始与子网络 betweenness 相关性仅 −0.05（近乎零相关），确认密集网络中 betweenness 是数学伪影而非真实的桥梁效应
9. **外部属性对 origination 无直接效应**：这是一个研究发现而非方法缺陷——网络结构（degree, betweenness）比城市静态属性（GDP, education）对创新角色的解释力更强，可引用 technological relatedness 文献支持
10. **（新增）K-Means k=4 vs k=3 的 silhouette 差距 (0.348 vs 0.386)**：k=3 统计指标更优但丢失理论中间层（Active Collaborator 被合并），k=4 在理论解释性与指标间取得最佳折衷。参数敏感性分析（§9.6）完整记录了这一权衡过程
11. **（新增）DBSCAN 仅发现 2 个密度簇**：城市特征空间中无明显密度间隙，DBSCAN 不适合此类平滑分布数据。但其识别的 22 个噪声城市（14.9%）可作为异常值鲁棒性检验
12. **（新增）GMM 与 K-Means 中等一致（ARI=0.340）**：两种方法捕捉到部分重叠但有差异的结构，GMM 因允许椭球协方差而产生不同划分。GMM 软概率显示 94.6% 城市分配确定（max prob≥0.7），验证了聚类边界的清晰性
13. **（V1.2）GraphSAGE 特征泄漏修复后指标下降**：原版 G1 R²=0.902（含全时段 adoption_count 等泄漏特征）→ 修复后 R²=0.914（仅训练期特征 + 参数优化）。修复泄漏降低了约 2% R²，但参数优化（dropout 0.5→0.3）弥补了差距。新结果更可靠
14. **（V1.2）train_weighted_degree 主导预测**：该特征 r=0.934，去掉后 GraphSAGE R² 降至 0.829。但图结构增量反而从 ΔR²=+0.145 扩大至 ΔR²=+0.367——说明 GraphSAGE 的图传播可有效替代该标量特征捕获的网络信息
15. **（V1.2）GraphSAGE 分类 (G2) 不优于 MLP**：MLP AUC=0.964 ≈ GraphSAGE AUC=0.960。中位数二值化使分类退化为"大城市 vs 小城市"的平凡判断。G2 已降级为辅助验证
16. **（V1.2）GraphSAGE 预测 vs 因果**：高 R² (0.914) 是预测能力而非因果证据。城市规模可能同时驱动协作强度和采纳数量（共因混淆）。Discussion 中应明确区分预测与解释的边界

## 6.6 Expected Conclusion ❌ 待撰写

### 6.6.1 中文说明

Expected Conclusion 现在应围绕“高影响 open-AI 项目生态”来收束。

### 6.6.2 第一层：城市角色

全球城市在 prominent open-AI projects 的生态中并不扮演同质角色。
有些城市更像 originators，有些是 collaboration hubs，有些是 bridge cities，而更多城市是 late adopters。

> **✅ 实际验证**：K-means (k=4) 确认了角色异质性—27 个 Global Innovation Hub（San Francisco, Beijing, London 等）主导创新发起（mean origination=275），16 个 Peripheral 城市仅 mean=2。与预期基本一致，但“bridge cities”未作为独立 cluster 出现（网络密度 0.886 导致 betweenness 区分度不足）。**（新增）** 参数敏感性分析（k=3/4/5, n_init=50）和替代模型（DBSCAN, GMM）的系统对比进一步验证了 k=4 选择的稳健性：k=3 统计最优 (sil=0.386) 但丢失理论中间层；DBSCAN 仅发现 2 个密度簇；GMM(k=4) 与 K-Means ARI=0.340 且 94.6% 城市分配确定。

### 6.6.3 第二层：扩散速度

高影响 open-AI 项目的扩散并不是随机发生的。
不同城市对这些项目的 adoption lag 有明显差异，说明传播速度在全球城市体系中高度不均衡。

> **✅ 实际验证**：Adoption lag 范围 0–50 个月，mean=6.28, median=2。Top 创新城市 avg_lag=5.98 vs Bottom 城市=10.25 (Mann-Whitney p<0.001)。East Asia 最快 (6.60)、Latin America 最慢 (10.87)。确认传播速度高度不均。

### 6.6.4 第三层：解释因素

城市的教育、收入、科研能力、数字基础设施和网络位置等因素，可能与 innovation-oriented roles 和 faster adoption 相关。

> **✅ 实际验证（需修正预期）**：传统属性（education、income）对 origination 无直接效应（偏相关 p>0.4），但 GDP (partial r=0.266, p=0.002) 和 internet (partial r=0.253, p=0.004) 控制规模后对 adoption 显著。**网络位置**（degree, betweenness）是最强解释变量（SHAP Top-3），远超静态城市属性。发现修正了预期——“网络结构比城市自身属性更重要”。

### 6.6.5 第四层：预测价值

GitHub 城市协作网络对“下一波 adopter 城市”的识别具有预测价值，因此网络结构不仅能描述协作关系，也能帮助理解技术扩散。

> **✅ 实际验证**：GraphSAGE Test R²=0.914, AUC=0.960, 城市排名 Spearman ρ=0.960 (p<0.001) → 强烈支持协作网络的预测价值。MLP 消融基线 R²=0.768，图结构增量 ΔR²=+0.145，证明图结构 + 节点特征联合建模显著优于纯特征方法。

### 6.6.6 第五层：技术类型异质性（RQ5, Step 13）

不同技术类型的 prominent open-AI 项目在全球城市间的传播速度显著不同，且城市特征的效应因技术类型而异。

> **✅ 实际验证**：Step 13 交互回归（OLS，n=24,434，R²=0.284）发现：(1) Vision 传播最快，Agent 和 Speech 传播最慢——不同技术的扩散速度确实存在显著差异；(2) 城市规模是唯一被技术类型显著调节的城市特征（block F p=.038）——非文本类技术（Vision/Multimodal/Speech）在大城市的传播优势比 LLM 类更强；(3) LLM-Foundation 更依赖网络中心性传播（p=.013）。预期的知识门槛假说（education/research_capacity 调节）和 GDP 门槛假说均未获支持——education 不显著并非被 LLM 淹没，而是对所有技术类型都不重要。

### 6.6.7 第六层：future work

1. 可进一步把 PatentsView 引入为 formal innovation validation layer
2. 可把 case-study 技术家族扩展成系统性对比研究
3. 可进一步比较不同项目类型的扩散机制差异
4. 尝试 edge-level GNN 或 link prediction 预测新协作关系的形成
5. 扩大城市样本（当前 n=148 限制了 tree-based 方法泛化能力）
6. 引入更精细的空间变量（如到最近 Innovation Hub 的网络距离）
7. **（新增）** 使用时间滞后策略（t−1 期网络特征 → t 期 adoption）打破 degree-adoption 同期循环性，实现更可靠的因果推断
8. **（新增）** 引入项目层面控制变量（项目 popularity、age、type）降低事件级 lag 回归中的项目异质性噪声，提升城市特征的边际解释力
9. **（新增）** 使用分层阈值（如 weight≥5/10/20）系统检验网络稀疏化对 betweenness 和 GNN embedding 质量的影响
