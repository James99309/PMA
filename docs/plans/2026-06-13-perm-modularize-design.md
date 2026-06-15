# 账户/个人配置/配置管理 纳入权限系统 设计

2026-06-13 确认。把账户列表、个人配置各 tab、配置管理各 tab 纳入 role_permissions 权限矩阵,
用标准四级数据范围(系统/公司/部门/个人)替代「上级看下属」等硬编码。

## 用户确认
- tab 过滤:**每个 tab 一个独立权限模块**(view + 四级数据范围)。
- 数据范围:**标准四级**(和其他业务模块一致),不用 Affiliation 硬编码;
  「部门下属可见 / 上级可见下属」= permission_level=department + get_viewable_data(User)。

## 新增权限模块(module_metadata)
- 账户列表:复用现有 `user_management`(view/create/edit/delete + 数据范围)
- 个人配置 tab:`person_permission` / `person_affiliation` / `person_budget` /
  `person_performance` / `person_salary` / `person_ai`
- 配置管理 tab:`config_permission` / `config_budget` / `config_performance` /
  `config_flow` / `config_salary`

## 安全迁移(防锁死)
- admin 恒全开(has_permission 已内置)。
- 种子迁移:按当前可访问角色灌默认 role_permissions —— 
  凡角色有 `config_management.can_view` → 给 config_* + person_* 各 view=true(scope 沿用其级别);
  薪资 tab(person_salary/config_salary)仅 admin/ceo/hr_manager 默认 view。
- **回退兜底**:页面/路由检查 `has_permission(新模块,'view')`,新模块在该角色无任何配置行时,
  回退旧逻辑(config_management/user_management view),避免种子漏配即锁死。

## 落地点
1. module_metadata 增模块 + 种子迁移(基础)
2. 账户列表:at_list/at_detail/create/edit/delete 路由按 user_management 动作鉴权 +
   列表 get_viewable_data(User) 按数据范围过滤
3. 个人配置:at_person_layout 按 person_* view 显示 tab;各路由按对应模块鉴权 +
   数据范围(get_viewable_data(User))决定可选/可见人员;移除 is_supervisor_of 硬编码
4. 配置管理:at_config_layout 按 config_* view 显示 tab;各路由按对应模块鉴权

## 阶段
- P1 模块定义 + 种子迁移 + 鉴权 helper(回退兜底)
- P2 账户列表鉴权 + 数据范围
- P3 个人配置 tab 鉴权/可见性 + 数据范围(替代硬编码)
- P4 配置管理 tab 鉴权/可见性
每阶段本地测稳再进下一阶段。
