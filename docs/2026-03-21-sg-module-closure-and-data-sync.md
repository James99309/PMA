# SG NAS 模块关闭与数据同步架构重构

**日期：** 2026-03-21
**影响范围：** CN NAS (SP8D) + SG NAS (OVS)

---

## 背景

SG NAS 的产品模板、规格字典、分类/子分类等数据均源自 CN NAS 同步副本。所有新产品从 CN NAS 产生。SG NAS 上这些模块的管理入口造成数据独立维护风险（已出现 3 个 subcategory code_letter 漂移）。

## 架构决策

**CN NAS 为唯一数据主库，SG NAS 为只读消费端。**

## 变更清单

### 1. SG NAS 关闭的模块

| 模块 | 前端 | 后端 API | 原因 |
|---|---|---|---|
| 产品模板 (spec_templates) | 菜单隐藏 | 蓝图不注册 | CN 主库管理 |
| 规格字典 (spec_definition) | 菜单隐藏 | 蓝图不注册 | CN 主库管理 |
| 产品分类管理 (product_code) | 菜单隐藏 | before_request 返回 403 | CN 主库管理 |
| 销售地区管理 | 菜单隐藏 | 同上 | CN 主库管理 |
| 配置版本管理 | 无入口 | 蓝图不注册 | SG 表为空 |

### 2. SG NAS 保留的模块

- 产品库（products + product_specs）— 85 个产品，报价单依赖
- 报价单 — 核心业务
- 分类/子分类数据（只读）— 通过物化视图从 CN 自动同步

### 3. 数据同步架构

```
CN NAS (数据主库)
  product_categories          ← 唯一编辑入口
  product_subcategories       ← 唯一编辑入口
  product_code_fields         ← 唯一编辑入口
        │
        ├─ 方案 B: 分类 CRUD 成功后异步 POST /api/v1/cross-sync/refresh-cache
        └─ 方案 A: SG crontab 每小时整点兜底刷新
        │
        ▼  postgres_fdw (Tailscale: 100.118.231.15 → 100.87.155.40)
SG NAS (只读消费端)
  cn_product_categories       ← fdw 外部表（查 CN）
  mv_product_categories       ← 物化视图（本地缓存, 0.02ms）
  product_categories          ← VIEW → mv（应用代码零改动，只读，写入报错）
        │
  products (85个)             ← SG 本地产品库（正常读写）
```

### 4. Mark1000 模板编码项固化保护

当模板已有活跃配置时：
- 禁止删除已有编码项
- 禁止更改编码项的 display_order
- 禁止取消 use_in_code
- 禁止更改 code_length
- 新增编码项的 display_order 必须 > 已有编码项最大值

违规返回 409 Conflict + `code_protection_error: true`。

### 5. 产品引用信息

配置选卡显示 `product_refs`，包含：
- 本地产品引用（CN NAS，通过 source_configuration_id FK）
- 跨库产品引用（SG NAS，通过 postgres_fdw + mn_code 匹配）

每条引用标注 `database: "cn"` 或 `"sg"`。

### 6. CN name_en 反向对齐

CN 的 product_categories.name_en 和 product_subcategories.name_en 已更新为 SG 产品库使用的英文名称，确保物化视图同步后 SG 产品展示一致。

## 修改的文件

| 文件 | 改动 |
|---|---|
| `app/__init__.py` | OVS 条件跳过 spec_definition_bp / spec_template_bp 注册 |
| `app/routes/product_code.py` | OVS before_request 返回 403 + notify_peer_on_success 装饰器 |
| `app/templates/components/tw_nav_menu.html` | OVS 隐藏产品模板/分类/地区/规格字典菜单 |
| `app/views/spec_template.py` | 编码项固化保护逻辑 |
| `app/models/spec_template.py` | product_refs 跨库查询 + _get_product_refs() |
| `app/services/cross_sync_service.py` | notify_peer_refresh_cache() |
| `app/api/v1/cross_sync.py` | /cross-sync/refresh-cache 端点 |

## 数据库变更（已直接执行，无需迁移）

### CN NAS (pma_synology)
- postgres_fdw 扩展 + sg_nas 外部服务器 + sg_products 外部表
- spec_template_items id=487 options 补全（国标三芯→6, UK Plug→A）
- products #10/#11 source_configuration_id 关联 + code_definition_snapshot 对齐
- product_categories/subcategories name_en 反向对齐 SG 英文名
- postgres 端口暴露 100.118.231.15:5432（Tailscale only）

### SG NAS (pma_sa)
- postgres_fdw 扩展 + cn_nas 外部服务器 + 3 个外部表
- 3 个物化视图（mv_product_categories/subcategories/code_fields）+ 唯一索引
- refresh_cn_cache() 刷新函数
- product_categories/subcategories/code_fields 重命名为 _local，创建同名只读 VIEW
- products #1 code_definition_snapshot 对齐
- postgres 端口暴露 100.87.155.40:5432（Tailscale only）
- docker-compose volume 修正为 external: pma_sa_postgres_data
- crontab 每小时刷新 /volume1/docker/pma/refresh_cn_cache.sh

## 注意事项

- SG NAS 的 `source_configuration_id` 无法设置（跨库 FK 约束），通过 mn_code 匹配替代
- 物化视图刷新耗时 ~4.4 秒（跨国网络），查询 0.02ms（本地）
- 直接 fdw 查询延迟 ~2.5 秒，不适合高频页面渲染
- SG 本地旧表数据保留在 `*_local` 表中作为备份
