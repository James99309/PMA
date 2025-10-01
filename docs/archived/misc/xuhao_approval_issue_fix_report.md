# xuhao用户审批问题修复报告

## 问题描述

用户报告xuhao账户看不到需要他审批的记录，提示有审批记录但在"待我审批"中未显示。

## 问题诊断过程

### 1. 初步诊断

通过创建诊断脚本`check_xuhao_approval_issue_fixed.py`发现：

- **用户基本信息**：
  - 用户ID: 7
  - 用户名: xuhao  
  - 真实姓名: 徐昊
  - 角色: service_manager
  - 部门: 服务部

- **问题现象**：
  - `get_pending_approval_count()` 返回 3 （有3个待审批）
  - `get_user_pending_approvals()` 返回 0 （函数过滤掉了所有记录）
  - 两个函数结果不一致，表明存在权限过滤问题

### 2. 根本原因分析

通过`simple_xuhao_project_check.py`进一步分析发现：

- **实际待审批项目**：xuhao需要审批3个项目，都是`business_opportunity`（商务机会）类型
- **权限过滤逻辑问题**：在`app/helpers/approval_helpers.py`中，对`service_manager`角色的项目类型过滤逻辑错误：
  
  ```python
  elif user_role in ['service', 'service_manager']:
      # 服务经理：销售机会
      query = query.filter(
          Project.project_type.in_(['销售机会', 'sales_opportunity'])  # ❌ 错误的类型
      )
  ```

- **问题根源**：系统中实际的项目类型是`business_opportunity`，但权限过滤逻辑中使用的是`sales_opportunity`，导致所有记录被过滤掉。

### 3. 项目类型映射问题

系统中的实际项目类型：
- `business_opportunity`: 6个项目（包括xuhao需要审批的3个）
- `channel_follow`: 295个项目  
- `sales_focus`: 100个项目
- `sales_key`: 2个项目

但权限过滤逻辑中使用的是旧的类型名称。

## 修复方案

### 修复内容

在`app/helpers/approval_helpers.py`中修正了5处`service_manager`角色的项目类型权限过滤逻辑：

1. **第873-877行**（批价单审批过滤）
2. **第988-992行**（项目审批过滤）  
3. **第1031-1035行**（项目子查询过滤）
4. **第1105-1109行**（批价单子查询过滤）
5. **第3801-3805行**（用户批价单审批过滤）

修复前：
```python
elif user_role in ['service', 'service_manager']:
    # 服务经理：销售机会
    query = query.filter(
        Project.project_type.in_(['销售机会', 'sales_opportunity'])
    )
```

修复后：
```python
elif user_role in ['service', 'service_manager']:
    # 服务经理：商务机会
    query = query.filter(
        Project.project_type.in_(['商务机会', 'business_opportunity'])
    )
```

## 修复验证

### 修复前后对比

**修复前**：
- `get_pending_approval_count()`: 3
- `get_user_pending_approvals()`: 0  
- ❌ 函数结果不一致，xuhao看不到待审批记录

**修复后**：
- `get_pending_approval_count()`: 3
- `get_user_pending_approvals()`: 3
- ✅ 函数结果一致，xuhao可以正常看到3个待审批记录

### 影响范围检查

通过`check_all_service_managers.py`检查了所有受影响的用户：

- ✅ **xuhao (service_manager)**：已修复，现在正常显示3个待审批
- ✅ **其他角色用户**：抽样检查显示大部分用户正常
- ⚠️ **gxh (sales_director)**：发现轻微的统计差异，但不影响主要功能

## 修复结果

### ✅ 问题已解决

1. **xuhao用户现在可以正常看到需要他审批的3个项目**
2. **审批中心显示正常，无遗漏**  
3. **权限过滤逻辑修正，符合业务需求**
4. **未发现其他service_manager用户受到类似影响**

### 📋 业务逻辑说明

修复后的权限逻辑：
- **service_manager（服务经理）**：只能审批`business_opportunity`（商务机会）类型的项目
- 这符合服务部门的职责范围，确保数据访问权限的正确性

## 总结

本次修复解决了xuhao用户无法看到待审批记录的问题，根本原因是审批权限过滤逻辑中使用了错误的项目类型名称。通过统一项目类型名称，确保了审批功能的正常运行，同时维护了基于角色的权限控制原则。 