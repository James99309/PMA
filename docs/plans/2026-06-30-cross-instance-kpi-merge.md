# 跨实例 KPI 合并设计(CN + SG 双真实账号)

**日期**: 2026-06-30 ｜ **状态**: 设计已定,待实现 ｜ **分支**: `feat/cross-instance-kpi-merge`

## 1. 目标
有些人(如 **liuwei**,方案经理:CN id12「刘威」/ SG id10「liuwei」)在 **CN 和 SG 都有真实账号、两边都做业务**。
其季度 KPI **实际值**应为 **CN + SG 合并**(SG 金额按汇率换算 CNY),在 **CN 端**体现;计分用合并值。

> 与"镜像用户"(`is_mirror`,影子号,仅为跨系统聊天@可见、无业务数据)**不同**——本功能是**两个真实账号**的业绩合并。

## 2. 现有基建(复用,Federation Lite)
- **对端连接**:env `CROSS_SYNC_ENABLED` / `CROSS_SYNC_PEER_URL` / `CROSS_SYNC_API_KEY` / `CROSS_SYNC_SELF_LABEL`;HTTP 调 `/api/v1/cross-sync/*`,鉴权头 `X-API-Key`(见 `cross_sync_service.py`)。
- **身份映射字段**:`users.source_system`('sp8d'/'ovs')+ `source_user_id`(对端 user.id)— 现用于镜像。
- **KPI 单一来源**:`app/services/kpi_actual_service.py` `_KPI_ACTUAL_FNS[code](user,s,e)`(见 [[project_kpi_actual_single_source]])。
- ⚠️ **现状单向**:SG→CN 已配(SG 有 PEER=CN);**CN→SG 未配**(CN env 全空)。本功能要 CN 拉 SG → **必须先开通 CN→SG**。

## 3. 设计决策(已与用户确认)
| 项 | 决策 |
|---|---|
| 身份绑定 | 用户编辑页 `cross_team` 区:勾选"绑定对端账号" + 下拉选对端真实账号 → 存 `peer_user_id`(+`peer_system`) |
| 金额类合并 | SG 原币 → CNY(`exchange_rate_service`/`MultiCurrencyAggregationService`)后**相加** |
| 计数类合并 | 直接**相加** |
| 率类合并 | 按**合并后分子/分母重算**(不简单相加) |
| 档位类(tiered,方案经理 `se_confirm_quality` 植入品质) | **CN+SG 已确认报价合到一起,算整体"推荐产品系数"均值,再套同一档位**(3→50%/5→100%/7) |
| 计分 | 用合并值 |
| 拆分显示 | **仅仪表盘卡 hover tooltip**(合并总额 hover → `CN x · SG y`);绩效页/个人配置只显示合并总额 |

## 4. 架构
```
CN 算 liuwei KPI(有 peer_user_id):
  本地实际值(各 metric)
  + 调 SG /cross-sync/kpi-actuals?user_id=10&start&end → 各 metric 实际值(率/档位附 分子分母/原始系数序列)
  → 按类型合并(金额换CNY+加 / 计数加 / 率重算 / tiered 合并系数序列再套档)
  → 计分用合并值;仪表盘卡 tooltip 用 {cn, sg} 拆分
```

### 4.1 SG 新增端点(`app/api/v1/cross_sync.py`,X-API-Key 鉴权)
- `GET /cross-sync/list-users` → 供 CN 绑定下拉:`[{id, username, real_name, role}]`。
- `GET /cross-sync/kpi-actuals?user_id=&start=&end=` → 复用 `_KPI_ACTUAL_FNS`,返回:
  - 每个 metric_code 的实际值(金额=原币+币种 或 已换算 USD;计数=int;率=value);
  - **率/档位类附原始量**:率→`{num, denom}`;`se_confirm_quality`→该期已确认报价的**系数序列**(供 CN 合并后求均值再套档)。

### 4.2 CN 合并层(`kpi_actual_service`)
- 新 helper:`_merge_peer_actuals(user, code, local_val, s, e)`:若 `user.peer_user_id`,拉对端、按 code 类型合并。
- 类型判定复用 `scoring_modes`(target/inverse/cumulative/tiered/rate)。
- 货币换算复用现有服务(SG 多币种 → CNY)。
- 返回 `{total, cn, sg}`;`_KPI_ACTUAL_FNS` 对外仍给 `total`(兼容计分);拆分另走一个 `get_actual_breakdown(user,code,s,e)` 供仪表盘卡。

### 4.3 身份绑定(CN)
- `User` 加 `peer_user_id`(Integer,nullable)+ `peer_system`(String(20),'ovs')— **迁移**。
- 编辑页 `user/edit.html` cross_team 区:勾选 → JS 调 `/api/v1/cross-instance/peer-users`(CN 代理 → SG `/cross-sync/list-users`)→ 下拉选 → 保存。

### 4.4 仪表盘卡 tooltip
- `at_dashboard_helpers` 的"我的 KPI"卡:实际值元素加 `title`/tooltip,内容 `CN x · SG y`(仅绑定用户、有拆分时)。

## 5. 阶段
- **前置**:开通 CN→SG(CN `.env`:`CROSS_SYNC_ENABLED=true`、`CROSS_SYNC_PEER_URL=http://100.87.155.40:5002/api/v1`、`CROSS_SYNC_API_KEY=<key>`)。
- **阶段1**:`peer_user_id` 迁移 + SG `/cross-sync/list-users` + CN 绑定 UI。
- **阶段2**:SG `/cross-sync/kpi-actuals` + CN 合并层 + 仪表盘卡 tooltip。
- **阶段3**:CN/SG 实测(先 liuwei)+ 部署两站。

## 6. 风险/注意
- **跨实例失败处理**:SG 不可达时,CN 应降级为"仅本地值"(不阻断绩效页),并标注未取到对端。
- **延迟**:实时拉对端有 HTTP 延迟;先实时,后续可加短缓存。
- **测试**:本地单库无法测跨实例 → 必须 CN/SG 实测。
- **货币**:SG 可能 USD/MYR 混合,统一换 CNY;汇率来源与现有报销/KPI 一致。

## 7. 待定
- CN→SG 的 **API_KEY**:复用 SG 现有 / 新生成一把(建议新生成,仅 cross-sync 用)。
