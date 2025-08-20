# 函数生命周期分析报告

**生成时间**: {{timestamp}}  
**分析范围**: {{project_root}}  
**分析模式**: {{analysis_mode}}  

---

## 📊 执行摘要

### 总体统计
- **总文件数**: {{total_files}}
- **已分析文件**: {{analyzed_files}}  
- **跳过文件数**: {{skipped_files}}
- **总函数数**: {{total_functions}}
- **Python函数**: {{python_functions}}
- **JavaScript函数**: {{javascript_functions}}

### 变更统计
- **新增函数**: {{new_functions_count}}
- **修改函数**: {{modified_functions_count}}  
- **删除函数**: {{deleted_functions_count}}
- **未变更函数**: {{unchanged_functions_count}}

---

## 🆕 新增函数分析

{% if new_functions %}
{% for func in new_functions %}
### `{{func.name}}` 
**文件**: `{{func.file_path}}`  
**行数**: {{func.line_start}}-{{func.line_end}}  
**语言**: {{func.language}}  
**是否为类方法**: {{func.is_method|yesno:"是,否"}}

{% if func.docstring %}
**文档字符串**: 
```
{{func.docstring}}
```
{% endif %}

{% if func.args %}
**参数**: `{{func.args|join:', '}}`
{% endif %}

{% if func.decorators %}
**装饰器**: `{{func.decorators|join:', '}}`
{% endif %}

#### 🔍 重复性分析
{{func.duplication_analysis|default:"待分析..."}}

#### 🔄 可重用性评估
{{func.reusability_assessment|default:"待评估..."}}

#### 💡 优化建议
{{func.optimization_suggestions|default:"无特定建议"}}

---
{% endfor %}
{% else %}
*本次分析中未发现新增函数*
{% endif %}

---

## 🔧 修改函数分析

{% if modified_functions %}
{% for change in modified_functions %}
### `{{change.current.name}}` 
**文件**: `{{change.current.file_path}}`  
**修改类型**: {% if change.signature_changed %}签名变更{% endif %}{% if change.body_changed %}函数体变更{% endif %}

#### 变更对比
| 属性 | 修改前 | 修改后 |
|------|--------|--------|
| 行数 | {{change.previous.line_start}}-{{change.previous.line_end}} | {{change.current.line_start}}-{{change.current.line_end}} |
| 参数 | {{change.previous.args|join:', '|default:'无'}} | {{change.current.args|join:', '|default:'无'}} |
| 装饰器 | {{change.previous.decorators|join:', '|default:'无'}} | {{change.current.decorators|join:', '|default:'无'}} |

#### 🎯 影响范围分析
{{change.impact_analysis|default:"待分析..."}}

#### 🔄 向后兼容性
{{change.compatibility_analysis|default:"待评估..."}}

#### 💡 重构建议
{{change.refactoring_suggestions|default:"无特定建议"}}

---
{% endfor %}
{% else %}
*本次分析中未发现修改的函数*
{% endif %}

---

## 🗑️ 删除函数记录

{% if deleted_functions %}
{% for func in deleted_functions %}
### `{{func.name}}` (已删除)
**原文件**: `{{func.file_path}}`  
**原行数**: {{func.line_start}}-{{func.line_end}}  
**语言**: {{func.language}}  

#### 🔍 依赖检查
{{func.dependency_check|default:"需要检查是否有其他代码依赖此函数"}}

#### ⚠️ 风险评估
{{func.deletion_risk|default:"低风险"}}

---
{% endfor %}
{% else %}
*本次分析中未发现删除的函数*
{% endif %}

---

## 🔄 重复函数识别

### 高相似度函数组

{% if duplicate_groups %}
{% for group in duplicate_groups %}
#### 函数组 {{forloop.counter}}
**相似度**: {{group.similarity_score}}%

{% for func in group.functions %}
- `{{func.name}}` ({{func.file_path}}:{{func.line_start}})
{% endfor %}

**建议操作**: {{group.consolidation_suggestion|default:"考虑合并或重构"}}

---
{% endfor %}
{% else %}
*未发现高相似度的重复函数*
{% endif %}

---

## 📦 未使用函数建议

### 建议归档的函数

{% if unused_functions %}
{% for func in unused_functions %}
#### `{{func.name}}`
**文件**: `{{func.file_path}}`  
**最后使用**: {{func.last_used|default:"未知"}}  
**未使用天数**: {{func.unused_days|default:"N/A"}}  

**归档建议**: {{func.archival_suggestion|default:"移至archive目录"}}  
**风险级别**: {{func.risk_level|default:"低"}}

{% endfor %}
{% else %}
*所有函数都有使用记录*
{% endif %}

---

## 💡 重构建议

### 高优先级建议

{% if high_priority_suggestions %}
{% for suggestion in high_priority_suggestions %}
#### {{suggestion.title}}
**影响范围**: {{suggestion.scope}}  
**预期收益**: {{suggestion.benefits}}  
**实施难度**: {{suggestion.difficulty}}  

{{suggestion.description}}

**实施步骤**:
{% for step in suggestion.steps %}
{{forloop.counter}}. {{step}}
{% endfor %}

---
{% endfor %}
{% else %}
*暂无高优先级重构建议*
{% endif %}

### 中优先级建议

{% if medium_priority_suggestions %}
{% for suggestion in medium_priority_suggestions %}
- **{{suggestion.title}}**: {{suggestion.description}}
{% endfor %}
{% else %}
*暂无中优先级建议*
{% endif %}

---

## 🧪 测试建议

### 需要增加测试的函数

{% if functions_need_tests %}
{% for func in functions_need_tests %}
- `{{func.name}}` ({{func.file_path}})
  - 复杂度: {{func.complexity}}
  - 建议测试类型: {{func.suggested_tests}}
{% endfor %}
{% else %}
*函数测试覆盖率良好*
{% endif %}

---

## 📈 质量指标

### 代码质量得分

| 指标 | 得分 | 说明 |
|------|------|------|
| 函数复用率 | {{reuse_score}}/100 | 函数重用程度 |
| 代码重复率 | {{duplication_score}}/100 | 重复代码比例 |
| 文档覆盖率 | {{documentation_score}}/100 | 函数文档完整性 |
| 测试覆盖率 | {{test_coverage}}/100 | 函数测试覆盖程度 |
| 整体质量 | {{overall_score}}/100 | 综合质量评分 |

### 趋势分析

{% if has_historical_data %}
- 📈 函数数量变化: {{function_count_trend}}
- 📊 代码复用率变化: {{reuse_trend}}
- 🧹 重复率改善: {{duplication_trend}}
{% else %}
*暂无历史数据对比*
{% endif %}

---

## 🎯 行动计划

### 即时行动 (1-3天)
{% if immediate_actions %}
{% for action in immediate_actions %}
- [ ] {{action}}
{% endfor %}
{% else %}
- [ ] 无紧急行动项
{% endif %}

### 短期改进 (1-2周)
{% if short_term_actions %}
{% for action in short_term_actions %}
- [ ] {{action}}
{% endfor %}
{% else %}
- [ ] 继续监控函数使用情况
{% endif %}

### 长期优化 (1-3月)
{% if long_term_actions %}
{% for action in long_term_actions %}
- [ ] {{action}}
{% endfor %}
{% else %}
- [ ] 建立定期函数生命周期审查机制
{% endif %}

---

## 📋 附录

### 分析配置
```json
{{analysis_config|default:"{}"}}
```

### 工具版本信息
- Function Detector: {{detector_version|default:"1.0.0"}}
- Python版本: {{python_version}}
- 分析引擎: {{analysis_engine|default:"AST + Regex"}}

### 数据文件
- 原始分析数据: `{{raw_data_file}}`
- 变更对比数据: `{{changes_data_file}}`
- 历史趋势数据: `{{trend_data_file}}`

---

*该报告由function-lifecycle-manager代理自动生成*  
*生成时间: {{timestamp}}*  
*报告版本: 1.0*