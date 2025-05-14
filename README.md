# 项目管理系统 - 中文项目名称相似度检测功能

## 功能简介

针对项目申请授权时的重复检查功能进行了优化，特别是对中文项目名称的相似度计算算法进行了增强，使系统能够更准确地检测潜在的重复项目。

## 新增特性

1. **优化的中文项目名称相似度算法**
   - 结合了字符级别的编辑距离(Levenshtein)和基于jieba分词的关键词匹配
   - 针对中文项目命名特点进行了专门优化
   - 对行业关键词（如"半导体"、"数据中心"等）提供更高的匹配权重
   - 支持共同短语识别，提高相似项目的发现率

2. **降低了相似度阈值**
   - 从原来的70%降低到60%，可以发现更多潜在的相似项目
   - 对于"半导体"等特定行业关键词进行了加权处理

3. **更详细的相似度计算分析**
   - 在日志中提供详细的相似度计算过程
   - 包括Levenshtein距离、关键词匹配、地名匹配、行业加权等多个维度

## 使用示例

以下是算法优化前后对比示例：

| 项目名称A | 项目名称B | 原始算法(fuzz.ratio) | 优化后算法 |
|---------|---------|-------------------|---------|
| 半导体中心 | 上海半导体场改造 | 46% | 51.25% |
| 成都半导体厂房 | 成都半导体生产基地 | 62% | 79.5% |
| 杭州数据中心 | 杭州数据中心二期 | 86% | 100% |

## 安装依赖

需要安装以下依赖：

```bash
pip install fuzzywuzzy python-Levenshtein jieba
```

或者通过requirements.txt安装：

```bash
pip install -r requirements.txt
```

## 测试方法

可以使用提供的测试脚本验证相似度算法效果：

```bash
python test_similarity.py
```

## 调整参数

如需调整相似度阈值或算法权重，可修改以下文件：

1. `app/utils/text_similarity.py` - 调整算法权重和相关参数
2. `app/views/project.py` - 修改相似度判断阈值(默认为60%) 

# 企业类型字段标准化更新说明

## 问题描述

在客户管理模块中，企业类型（`company_type`）字段当前使用中文值存储在数据库中，如"用户"、"经销商"等，导致：

1. 与标准化字典映射（`COMPANY_TYPE_LABELS`）不一致
2. 在项目新增页面中，"直接用户"下拉菜单无法正确加载"客户类型为用户（users）"的企业名称
3. 可能出现中英文混用的情况，影响系统一致性

## 已完成修复

1. 已修改 `app/views/project.py` 中的 `get_company_data()` 函数，将企业类型筛选从中文改为标准英文 key，并使用字典推导式从集中定义的 `COMPANY_TYPE_LABELS` 生成：
   ```python
   def get_company_data():
       from app.utils.dictionary_helpers import COMPANY_TYPE_LABELS
       company_query = get_viewable_data(Company, current_user)
       return {
           key: company_query.filter_by(company_type=key).all()
           for key in COMPANY_TYPE_LABELS.keys()
       }
   ```

   这种实现方式确保了代码的一致性和可维护性：
   - 后端公司类型键与 `COMPANY_TYPE_LABELS` 保持一致
   - 统一使用英文单数形式的键名（如 `user`、`designer` 等）
   - 减少了冗余和硬编码，便于未来扩展与修改

2. 确认模板中已正确使用过滤器：
   ```html
   <!-- 在 customer/list.html 等页面中 -->
   {{ company.company_type|company_type_label }}
   ```

3. 确认 `company_type_label` 过滤器已在 `app/__init__.py` 中正确注册

## 运行数据迁移脚本

要完成修复，需要运行附带的数据迁移脚本，将数据库中现有的中文企业类型值更新为标准英文 key。

### 迁移步骤

1. **备份数据库**（重要！）

2. **执行迁移脚本**：
   ```bash
   cd /path/to/project
   python migrations/company_type_fix.py
   ```

3. **验证结果**：
   - 检查"直接用户"下拉菜单是否正确显示所有 `company_type='user'` 的企业
   - 确认客户列表页中企业类型显示正常（应显示中文名称）

### 映射关系

此次迁移将进行以下映射转换：

| 原中文值 | 标准英文key |
|---------|------------|
| 用户 | user |
| 经销商 | dealer |
| 系统集成商 | integrator |
| 设计院及顾问 | designer |
| 总承包单位 | contractor |

## 后续注意事项

1. 请确保所有对企业类型的筛选查询都使用英文 key
2. 前端展示时应统一使用 `company_type_label` 过滤器
3. 如后续需要添加新的企业类型，应在 `app/utils/dictionary_helpers.py` 中的 `COMPANY_TYPE_LABELS` 字典中添加相应映射 