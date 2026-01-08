# 项目成功率预测模型设计文档

> **版本**: 1.0
> **创建日期**: 2025-01-09
> **数据来源**: SP8D云端数据库
> **状态**: 设计完成，待实现

---

## 1. 背景与目标

### 1.1 背景

PMA系统积累了大量项目数据，包括项目基本信息、阶段历史、报价单、批价单等。通过分析历史数据，可以识别出影响项目成功的关键因素，为销售团队提供决策支持。

### 1.2 目标

1. **预测项目成功概率** - 基于项目早期特征，预测最终签约的可能性
2. **识别风险项目** - 提前发现可能失败的项目
3. **优化资源分配** - 帮助销售聚焦高潜力项目
4. **评估销售能力** - 基于历史数据量化销售成功率

---

## 2. 数据分析结果

### 2.1 数据概况（截至2025年1月）

| 指标 | 数值 |
|-----|-----|
| 总项目数 | 731 |
| 签约项目 | 123 (16.8%) |
| 失败项目 | 145 (19.8%) |
| 进行中项目 | 463 (63.3%) |

### 2.2 年度数据分布

| 年份 | 总项目 | 签约 | 失败 | 结案率 |
|-----|-------|-----|-----|-------|
| 2025 | 439 | 71 | 61 | 30.1% |
| 2024 | 136 | 27 | 46 | 53.7% |
| 2023 | 53 | 14 | 18 | 60.4% |
| 2022 | 24 | 6 | 11 | 70.8% |

> **说明**: 2024年数据结案率较高(53.7%)，更适合用于模型验证。2025年数据大部分仍在进行中。

### 2.3 关键特征分析（2024年数据）

| 特征 | 签约项目 | 失败项目 | 差异 | 预测价值 |
|-----|---------|---------|-----|---------|
| **有报价金额** | 100.0% | 47.8% | **+52.2%** | ⭐⭐⭐ 最强 |
| **有最终用户** | 7.4% | 2.2% | **+5.2%** | ⭐⭐⭐ 强相关 |
| 有报价单 | 100.0% | 47.8% | +52.2% | ⭐⭐ 中等 |
| 有系统集成商 | - | - | ~0% | ❌ 无区分度 |

### 2.4 跟进记录现状

```
总跟进记录: 163条
关联项目的跟进: 11条 (仅1.5%的项目有跟进)

结论: 跟进记录使用率极低，暂不纳入预测模型
未来: 当跟进数据积累足够后，可加入跟进频率、拜访次数等特征
```

---

## 3. 成功定义

### 3.1 项目成功判定标准

```python
def is_project_successful(project):
    """
    判断项目是否成功

    规则:
    1. 阶段达到'签约(signed)' → 成功
    2. 2025年启用批价单后: 有已批准批价单 也算成功
    """
    if project.current_stage == 'signed':
        return True

    # 2025年后，有已批准批价单也算成功
    if project.report_time and project.report_time.year >= 2025:
        if has_approved_pricing_order(project):
            return True

    return False
```

### 3.2 项目失败判定标准

```python
def is_project_failed(project):
    """
    判断项目是否失败

    规则:
    1. 阶段为'失败(lost)' → 失败
    2. 阶段为'搁置(paused)' → 失败
    """
    return project.current_stage in ['lost', 'paused']
```

### 3.3 业绩统计维度

项目成功有两个业绩维度：

| 维度 | 说明 | 计算方式 |
|-----|------|---------|
| **成功数量** | 签约项目数 | COUNT(current_stage='signed') |
| **成功金额** | 签约项目总额 | SUM(quotation_customer WHERE current_stage='signed') |

> **注意**: 批价单金额是业绩指标，不是预测特征。批价单是项目接近成功时才会有的，不能用来预测成功。

---

## 4. 预测特征定义

### 4.1 特征列表

以下特征均为项目早期可获取的信息：

| 特征名 | 字段 | 类型 | 权重 | 说明 |
|-------|------|-----|------|------|
| 有报价金额 | quotation_customer > 0 | Boolean | 30分 | 最强预测特征 |
| 有最终用户 | end_user IS NOT NULL | Boolean | 15分 | 决策能力强 |
| 有报价单 | EXISTS(quotation) | Boolean | 10分 | 报价意向 |
| 当前阶段 | current_stage | Enum | 0-25分 | 阶段越高越好 |
| 销售加成 | owner_id → 成功率 | Float | 0-20分 | 销售历史表现 |

### 4.2 特征计算规则

#### 4.2.1 有报价金额 (30分)

```python
def calc_quotation_amount_score(project):
    """有报价金额得分"""
    if project.quotation_customer and project.quotation_customer > 0:
        return 30
    return 0
```

#### 4.2.2 有最终用户 (15分)

```python
def calc_end_user_score(project):
    """有最终用户得分"""
    if project.end_user and project.end_user.strip():
        return 15
    return 0
```

#### 4.2.3 有报价单 (10分)

```python
def calc_quotation_score(project):
    """有报价单得分"""
    if Quotation.query.filter_by(project_id=project.id).count() > 0:
        return 10
    return 0
```

#### 4.2.4 当前阶段得分 (0-25分)

```python
STAGE_SCORES = {
    'discover':     0,    # 发现 - 初期
    'embed':        5,    # 植入 - 早期
    'pre_tender':   10,   # 标前 - 中期
    'tendering':    15,   # 标中 - 关键期
    'awarded':      20,   # 中标 - 后期
    'quoted':       25,   # 批价 - 准成功
    'signed':       25,   # 签约 - 已成功
    'lost':         0,    # 失败
    'paused':       0,    # 搁置
}

def calc_stage_score(project):
    """当前阶段得分"""
    return STAGE_SCORES.get(project.current_stage, 0)
```

---

## 5. 销售加成计算

### 5.1 销售成功率定义

```python
def calc_sales_success_rate(owner_id, year=None):
    """
    计算销售的结案成功率

    公式: 成功率 = 签约项目数 / (签约项目数 + 失败项目数)

    参数:
        owner_id: 销售用户ID
        year: 指定年份，默认为当前年份

    返回:
        float: 成功率 (0.0 - 1.0)
    """
    if year is None:
        year = datetime.now().year

    query = Project.query.filter(
        Project.owner_id == owner_id,
        extract('year', Project.report_time) == year
    )

    signed_count = query.filter(Project.current_stage == 'signed').count()
    failed_count = query.filter(Project.current_stage.in_(['lost', 'paused'])).count()

    closed_count = signed_count + failed_count
    if closed_count == 0:
        return 0.0

    return signed_count / closed_count
```

### 5.2 销售加成得分 (0-20分)

```python
def calc_sales_bonus(owner_id, year=None):
    """
    计算销售加成得分

    基于销售该年度的结案成功率:
    - 成功率 >= 80%: 20分 (顶级销售)
    - 成功率 >= 60%: 15分 (优秀销售)
    - 成功率 >= 40%: 10分 (良好销售)
    - 成功率 >= 20%: 5分  (普通销售)
    - 成功率 < 20%:  0分  (待提升)
    """
    rate = calc_sales_success_rate(owner_id, year)

    if rate >= 0.80:
        return 20
    elif rate >= 0.60:
        return 15
    elif rate >= 0.40:
        return 10
    elif rate >= 0.20:
        return 5
    else:
        return 0
```

### 5.3 2025年销售成功率参考

| 销售 | 结案成功率 | 加成得分 |
|-----|----------|---------|
| 方玲 | 97.0% | 20分 |
| 李华伟 | 66.7% | 15分 |
| 杨俊杰 | 57.1% | 10分 |
| 郭小会 | 44.4% | 10分 |
| 范敬 | 28.6% | 5分 |
| 周裔锦 | 20.0% | 5分 |
| 李冬 | 16.7% | 0分 |

---

## 6. 总分计算与等级划分

### 6.1 总分计算公式

```python
def calc_success_probability(project):
    """
    计算项目成功概率得分

    总分 = 基础特征分 + 阶段分 + 销售加成
    满分 = 100分
    """
    score = 0

    # 基础特征分 (0-55分)
    score += calc_quotation_amount_score(project)  # 0-30分
    score += calc_end_user_score(project)          # 0-15分
    score += calc_quotation_score(project)         # 0-10分

    # 阶段分 (0-25分)
    score += calc_stage_score(project)

    # 销售加成 (0-20分)
    year = project.report_time.year if project.report_time else datetime.now().year
    score += calc_sales_bonus(project.owner_id, year)

    return min(score, 100)
```

### 6.2 成功概率等级

| 总分范围 | 等级 | 说明 | 建议 |
|---------|-----|------|------|
| 75-100分 | **高** | 成功概率很高 | 重点跟进，优先分配资源 |
| 50-74分 | **中** | 成功概率中等 | 正常跟进，关注进展 |
| 25-49分 | **低** | 成功概率较低 | 分析原因，考虑调整策略 |
| 0-24分 | **很低** | 成功概率很低 | 评估是否继续投入 |

### 6.3 等级判定函数

```python
def get_probability_level(score):
    """
    获取成功概率等级

    返回: (等级名称, 等级颜色, 建议)
    """
    if score >= 75:
        return ('高', 'success', '重点跟进，优先分配资源')
    elif score >= 50:
        return ('中', 'warning', '正常跟进，关注进展')
    elif score >= 25:
        return ('低', 'secondary', '分析原因，考虑调整策略')
    else:
        return ('很低', 'danger', '评估是否继续投入')
```

---

## 7. 示例计算

### 7.1 高潜力项目示例

```
项目: XX医院智能化项目
├─ 有报价金额 (500万): +30分
├─ 有最终用户 (XX医院): +15分
├─ 有报价单: +10分
├─ 当前阶段 (awarded中标): +20分
└─ 销售 (方玲, 97%成功率): +20分
──────────────────────────────
总分: 95分 → 等级: 高
```

### 7.2 低潜力项目示例

```
项目: YY项目
├─ 无报价金额: +0分
├─ 无最终用户: +0分
├─ 无报价单: +0分
├─ 当前阶段 (embed植入): +5分
└─ 销售 (李冬, 17%成功率): +0分
──────────────────────────────
总分: 5分 → 等级: 很低
```

---

## 8. 实施计划

### 8.1 第一阶段：核心功能

- [ ] 创建 `ProjectSuccessPredictor` 类
- [ ] 实现各特征评分函数
- [ ] 创建销售成功率缓存表
- [ ] 在项目详情页显示成功概率

### 8.2 第二阶段：前端展示

- [ ] 项目列表添加成功概率列
- [ ] 项目卡片显示概率等级标签
- [ ] 仪表盘添加项目健康度分布图

### 8.3 第三阶段：持续优化

- [ ] 收集预测准确率数据
- [ ] 调整特征权重
- [ ] 引入跟进记录特征（当数据足够时）
- [ ] 机器学习模型升级（XGBoost等）

---

## 9. 数据表设计

### 9.1 销售成功率缓存表

```sql
CREATE TABLE sales_success_rate_cache (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    year INTEGER NOT NULL,
    total_projects INTEGER DEFAULT 0,
    signed_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4) DEFAULT 0.0,
    bonus_score INTEGER DEFAULT 0,
    calculated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, year)
);
```

### 9.2 项目成功概率缓存表（可选）

```sql
CREATE TABLE project_success_score_cache (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) UNIQUE,
    total_score INTEGER DEFAULT 0,
    quotation_amount_score INTEGER DEFAULT 0,
    end_user_score INTEGER DEFAULT 0,
    quotation_score INTEGER DEFAULT 0,
    stage_score INTEGER DEFAULT 0,
    sales_bonus INTEGER DEFAULT 0,
    probability_level VARCHAR(10),
    calculated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 10. API设计

### 10.1 获取项目成功概率

```
GET /api/project/{id}/success-probability

Response:
{
    "project_id": 123,
    "total_score": 75,
    "probability_level": "高",
    "probability_percent": 75,
    "breakdown": {
        "quotation_amount_score": 30,
        "end_user_score": 15,
        "quotation_score": 10,
        "stage_score": 20,
        "sales_bonus": 0
    },
    "suggestion": "重点跟进，优先分配资源",
    "calculated_at": "2025-01-09T12:00:00Z"
}
```

### 10.2 获取销售成功率

```
GET /api/user/{id}/success-rate?year=2025

Response:
{
    "user_id": 5,
    "user_name": "方玲",
    "year": 2025,
    "total_projects": 50,
    "signed_count": 32,
    "failed_count": 1,
    "in_progress_count": 17,
    "success_rate": 0.970,
    "bonus_score": 20,
    "rank": 1
}
```

---

## 11. 未来优化方向

### 11.1 跟进记录特征（待数据积累）

当跟进记录使用率提升后，可加入以下特征：

| 特征 | 计算方式 | 预期权重 |
|-----|---------|---------|
| 跟进频率 | 月均跟进次数 | 5-10分 |
| 拜访次数 | work_type='customer_visit' | 5-10分 |
| 技术支持次数 | work_type='technical_support' | 3-5分 |
| 出差投入 | is_business_trip=true计数 | 3-5分 |

### 11.2 机器学习升级

数据量足够后（建议500+已结案项目），可升级为机器学习模型：

```python
# 推荐算法
from sklearn.ensemble import GradientBoostingClassifier
from xgboost import XGBClassifier

# 特征工程
features = [
    'has_quotation_amount',    # 有报价金额
    'has_end_user',            # 有最终用户
    'has_quotation',           # 有报价单
    'stage_numeric',           # 阶段编码
    'sales_success_rate',      # 销售历史成功率
    'days_since_report',       # 项目年龄
    'followup_count',          # 跟进次数（未来）
]

# 目标变量
target = 'is_signed'  # 是否签约
```

---

## 12. 附录

### 12.1 阶段中文映射

```python
STAGE_NAMES = {
    'discover': '发现',
    'embed': '植入',
    'pre_tender': '标前',
    'tendering': '标中',
    'awarded': '中标',
    'quoted': '批价',
    'signed': '签约',
    'lost': '失败',
    'paused': '搁置',
}
```

### 12.2 概率等级颜色

```python
LEVEL_COLORS = {
    '高': '#28a745',      # 绿色
    '中': '#ffc107',      # 黄色
    '低': '#6c757d',      # 灰色
    '很低': '#dc3545',    # 红色
}
```

### 12.3 相关文档

- 项目模型定义: `app/models/project.py`
- 报价单模型: `app/models/quotation.py`
- 批价单模型: `app/models/pricing_order.py`
- 用户模型: `app/models/user.py`

---

**文档维护记录**

| 日期 | 版本 | 修改内容 | 修改人 |
|-----|------|---------|-------|
| 2025-01-09 | 1.0 | 初始版本 | Claude |
