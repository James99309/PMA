# PNR2100 终端交互接口文档

> 创建人：小金城武 | 创建时间：2025-11-27 | 最近更新：2026-04-01
>
> 接口状态：开发中 | 基础域名：`https://heyuanyun.com` / `https://heyuan.medmeet.com.cn`

PNR2100 是一款智能对讲终端设备，通过 HTTP REST API 与河源云平台进行交互。接口覆盖设备登录认证、用户信息获取、巡更任务管理、服务工单管理、设备数据上报（蓝牙/GPS/电池）以及短消息/遥开遥闭等平台推送功能。

---

## 1. 全局约定

### 1.1 认证方式

- 大部分接口无需独立认证参数，通过 `sign` 签名校验设备身份。
- 登录成功后获得 JWT `token`，后续需认证的接口在 Header 中携带：`token: <JWT>`。
- 部分接口使用 `Authorization: Bearer <OAuth Token>`（如文件上传）。

### 1.2 签名算法

```
sign = md5(key + createTime + 密钥)
```

示例：`md5(qiwjgioqj2025-12-23T02:01:12.055Zj6KWEfFFFNZuBOp6)`

### 1.3 公共请求字段

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string/number | 是 | 设备 ID |
| sn | string | 是 | 设备序列号 |
| createTime | string | 是 | 当前时间（ISO 8601 格式） |
| key | string | 是 | 随机字符串 |
| sign | string | 是 | 加密签名 |

### 1.4 公共响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

- `code` = 200 表示成功，其他值表示失败。
- 登录类接口额外包含 `sub_code` 细分错误码。

---

## 2. 设备初始化

### 2.1 能力声明（开机上报）

每次开机时终端向平台上报硬件能力信息。

| 项目 | 值 |
|---|---|
| URL | `POST /api/terminal/pnr2100/init` |
| Content-Type | application/json |

**请求参数：**

| 参数名 | 示例值 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| hardwareVersion | PNR2100-1.0 | string | 是 | 硬件版本 |
| firmwareVersion | 1.0.3 | string | 是 | 固件版本 |
| capabilities | {} | object | 是 | 能力声明对象 |
| capabilities.ble | 1 | string | 是 | 蓝牙能力 |
| capabilities.gps | true | string | 是 | GPS 能力 |
| capabilities.remoteAction | true | string | 是 | 远程操作能力 |
| capabilities.recordUpload | true | string | 是 | 录音上传能力 |
| simlCCID | test123 | string | 是 | SIM 卡号 |
| *(公共字段)* | | | | id / sn / createTime / key / sign |

**响应示例：**

```json
{ "code": 200, "message": "success", "data": null }
```

### 2.2 获取服务器基础信息

| 项目 | 值 |
|---|---|
| URL | `GET /api/terminal/pnr2100/get/basic` |
| Content-Type | application/json |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": { "next_second": 2 }
}
```

---

## 3. 登录与认证

### 3.1 账号密码登录

| 项目 | 值 |
|---|---|
| URL | `POST /api/terminal/pnr2100/login` |
| Content-Type | application/json |

**请求参数：**

| 参数名 | 示例值 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| username | pnr2100-001 | string | 是 | 账号 |
| password | 123456 | string | 是 | 密码 |
| qrcodekey | abcd | string | 否 | 绑定二维码唯一标识 |
| id | 201 | string | 否 | 设备 ID（与 qrcodekey 不可同时为空） |
| sn | LSTD4MA25031067 | string | 否 | 设备序列号（与 qrcodekey 不可同时为空） |
| *(公共字段)* | | | | createTime / key / sign |

**响应参数：**

| 参数名 | 说明 |
|---|---|
| data.token | JWT 身份令牌 |
| sub_code | 细分错误码：1=账号已被其他设备绑定，2=设备已绑定其他账号，3=账号禁用，4=设备禁用 |

### 3.2 扫码登录 — 获取二维码地址

| 项目 | 值 |
|---|---|
| URL | `GET /api/terminal/pnr2100/get/qrcode` |
| Content-Type | application/json |

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | 设备 ID |
| sn | string | 是 | 设备序列号 |
| *(公共字段)* | | | createTime / key / sign |

**响应参数：**

| 参数名 | 说明 |
|---|---|
| data.url | 二维码图片 URL |
| data.qrid | 二维码 ID |

**失败示例（设备已绑定）：**

```json
{ "code": 500, "message": "该设备已绑定其他账号！" }
```

### 3.3 扫码登录 — 状态轮询

| 项目 | 值 |
|---|---|
| URL | `POST /api/terminal/pnr2100/get/bind/status` |
| Content-Type | application/json |

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| qrid | string | 是 | 二维码 ID |
| *(公共字段)* | | | id / sn / createTime / key / sign |

**响应参数：**

| 参数名 | 说明 |
|---|---|
| data.status | 0=未绑定，1=已绑定（已绑定时返回 token） |
| data.token | JWT 身份令牌（绑定成功时返回） |

### 3.4 退出登录

| 项目 | 值 |
|---|---|
| URL | `POST /api/terminal/pnr2100/logout` |
| Content-Type | application/json |

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| createTime | string | 是 | 当前时间 |

---

## 4. 用户信息

### 4.1 获取用户信息

| 项目 | 值 |
|---|---|
| URL | `GET /api/terminal/pnr2100/get/info` |
| Header | token: JWT |

**响应参数：**

| 参数名 | 示例值 | 说明 |
|---|---|---|
| data.id | 106 | 人员 ID |
| data.job_number | gonghao002 | 工号 |
| data.real_name | 康刘畅 | 姓名 |
| data.role | 2 | 身份：1=工程人员，2=保安 |
| data.unread_msg | 2 | 云平台未读消息数量 |
| data.projects.id | 41 | 项目 ID |
| data.projects.name | 嘉信科技 | 项目名称 |
| data.projects.project_id | TJ0041 | 项目编号 |
| data.department.id | 121 | 部门 ID |
| data.department.name | 保安部 | 部门名称 |

---

## 5. 巡更任务

### 5.1 巡更任务统计

**响应参数：**

| 参数名 | 说明 |
|---|---|
| data.status_0 | 未开始数量 |
| data.status_1 | 进行中数量 |
| data.status_2 | 已完成数量 |
| data.status_3 | 已结束数量 |

### 5.2 巡更任务列表

| 项目 | 值 |
|---|---|
| URL | `GET /api/terminal/pnr2100/get/patrol/task` |
| Header | token: JWT |

**请求 Query 参数：**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| status | string | 是 | -1=全部，0=待开始，1=进行中，2=已完成，3=已取消，4=未完成 |
| page | string | 是 | 页码 |
| size | string | 是 | 每页数量 |

**响应参数：**

| 参数名 | 说明 |
|---|---|
| data.list[].id | 任务 ID |
| data.list[].serial_number | 任务编号（如 RW000016） |
| data.list[].name | 任务名称 |
| data.list[].start_date | 任务开始时间 |
| data.list[].end_date | 任务结束时间 |
| data.total | 总数 |

### 5.3 巡更任务详情

| 项目 | 值 |
|---|---|
| URL | `GET /api/terminal/pnr2100/get/patrol/task/info/{id}` |
| Header | token: JWT |

**响应数据结构：**

| 参数名 | 类型 | 说明 |
|---|---|---|
| data.id | number | 任务 ID |
| data.name | string | 任务名称 |
| data.status | number | 0=待开始，1=进行中，2=已完成，3=已取消，4=未完成 |
| data.serial_number | string | 任务编号 |
| data.start_date / end_date | string | 任务起止时间 |
| data.path_info_v2 | object | 路线信息 |
| data.path_info_v2.name | string | 路线名称 |
| data.path_info_v2.nums | number | 巡检点数量 |
| data.path_info_v2.path_type | number | 0=无固定顺序，1=顺序巡更 |
| data.path_info_v2.points_info_v2[] | array | 巡检点数组 |
| └ .id | number | 巡检点 ID |
| └ .type | number | 0=蓝牙信标，1=室外定位 |
| └ .name | string | 巡检点名称 |
| └ .user_task_point_status | number | 0=未完成，1=已完成，2=异常 |
| └ .exception_info | object/null | 异常信息（含图片、备注等） |
| └ .beacons_info | object/null | 蓝牙信标信息（含楼层、区域） |

### 5.4 巡更任务异常上报

| 项目 | 值 |
|---|---|
| URL | `POST /api/terminal/pnr2100/set/patrol/task/exception` |
| Header | token: JWT |
| Content-Type | application/json |

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| task_id | integer | 是 | 任务 ID |
| path_points_id | integer | 是 | 巡检点 ID |
| remark | string | 是 | 异常类型说明 |
| remark_desc | string | 是 | 异常详细描述 |
| pic | array | 否 | 异常照片 URL 数组 |

**响应：** 返回更新后的完整任务详情。

### 5.5 测试巡更点

| 项目 | 值 |
|---|---|
| URL | `GET /api/terminal/pnr2100/test/point` |
| Header | token: JWT |

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| project_id | integer | 是 | 项目 ID |
| type | integer | 是 | 类型 |

---

## 6. 服务工单

### 6.1 服务工单统计

**响应参数：**

| 参数名 | 说明 |
|---|---|
| data.status_0 | 未开始数量 |
| data.status_1 | 进行中数量 |
| data.status_2 | 已完成数量 |
| data.status_3 | 已结束数量 |

### 6.2 服务工单列表

| 项目 | 值 |
|---|---|
| URL | `GET /api/terminal/pnr2100/get/service/order` |
| Header | token: JWT |

**请求 Query 参数：**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| status | string | 是 | -1=全部，0=待开始，1=进行中，2=已完成，3=已取消，4=未完成 |
| page | string | 是 | 页码 |
| size | string | 是 | 每页数量 |

**响应参数：**

| 参数名 | 说明 |
|---|---|
| data.list[].id | 服务工单 ID |
| data.list[].name | 工单名称 |
| data.list[].status | 状态 |
| data.list[].no | 工单编号（如 FW000002） |
| data.list[].created_at_str | 创建时间 |
| data.list[].progress | 进度 |
| data.list[].time_diff | 耗时（如 "2天17小时34分"） |
| data.count | 总数 |

### 6.3 服务工单详情

| 项目 | 值 |
|---|---|
| URL | `GET /api/terminal/pnr2100/get/service/order/info/{id}` |
| Header | token: JWT |

**响应参数：**

| 参数名 | 说明 |
|---|---|
| data.id | 工单 ID |
| data.name | 工单名称 |
| data.content | 工单详细内容 |
| data.serial_number | 工单编号 |
| data.status | 状态 |
| data.start_date / end_date | 起止时间 |

### 6.4 服务工单完成

| 项目 | 值 |
|---|---|
| URL | `POST /api/terminal/pnr2100/service/order/complete/{id}` |
| Header | token: JWT |

**请求参数：** 无 Body（`id` 通过路径传递）。

**响应：** 返回工单详情。

---

## 7. 设备数据上报

### 7.1 蓝牙环境上报

| 项目 | 值 |
|---|---|
| URL | `POST /api/terminal/pnr2100/report/surround` |
| Content-Type | application/json |

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| type | string | 是 | 上报类型（如 `blueTooth`） |
| blueToothList | array | 是 | 附近蓝牙信标列表（不少于 3 个） |
| blueToothList[].major | string | 是 | 蓝牙信标 major |
| blueToothList[].minor | string | 是 | 蓝牙信标 minor |
| blueToothList[].rssi | string | 是 | 蓝牙信标 RSSI |
| blueToothList[].uuid | string | 是 | 蓝牙信标 UUID |
| *(公共字段)* | | | id / sn / createTime / key / sign |

**响应：**

```json
{ "code": 200, "message": "success", "data": { "next_second": 2 } }
```

- `next_second`：服务端指示下次上报间隔秒数。

### 7.2 GPS 位置上报

| 项目 | 值 |
|---|---|
| URL | `POST /api/terminal/pnr2100/report/gps` |
| Content-Type | application/json |

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| list | array | 是 | GPS 信息数组（批量上报） |
| list[].lng | string | 是 | 经度（小数点后 6 位） |
| list[].lat | string | 是 | 纬度（小数点后 6 位） |
| list[].altitude | string | 是 | 海拔 |
| list[].speed | string | 是 | 速度 |
| list[].accuracy | string | 是 | 水平精度 |
| list[].satellite_count | string | 是 | 卫星数量 |
| list[].valid | string | 是 | 0=可靠，1=不可靠 |
| list[].createTime | string | 是 | 采集时间 |
| *(公共字段)* | | | id / sn / createTime / key / sign |

**响应：**

```json
{ "code": 200, "message": "success", "data": { "next_second": 2 } }
```

### 7.3 电池信息上报

| 项目 | 值 |
|---|---|
| URL | `POST /api/terminal/pnr2100/report/cell` |
| Content-Type | application/json |

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| cellStatus | string | 是 | 电池状态（见下方字典） |
| cellLevel | string | 是 | 智能电池容量 0-100 |
| cellId | string | 是 | 电池 ID |
| *(公共字段)* | | | id / sn / createTime / key / sign |

**cellStatus 字典：**

| 枚举值 | 编码 | 说明 |
|---|---|---|
| CELL_STATE_INVALID | 0 | 无效 |
| CELL_STATE_FAULT | 1 | 电池故障，电量读取无效 |
| CELL_STATE_CAPLOW | 2 | 电池电量低告警 |
| CELL_STATE_TEMPHIGH | 3 | 温度过高告警 |
| CELL_STATE_TEMPLOW | 4 | 温度过低告警 |
| CELL_STATE_VOLTHIGH | 5 | 电压过高告警 |
| CELL_STATE_VOLTLOW | 6 | 电压过低告警 |

**响应：**

```json
{ "code": 200, "message": "success", "data": null }
```

---

## 8. 公共文件上传

| 项目 | 值 |
|---|---|
| URL | `POST /api/applets/v1/common/uploadImage` |
| Content-Type | multipart/form-data |
| Header | Authorization: Bearer \<OAuth Token\> |

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| file | file | 是 | 图片文件 |

---

## 9. 平台推送接口（待补充）

以下接口由平台主动推送至终端，目前文档中仅列出名称，详细协议待后续补充：

| 功能模块 | 说明 |
|---|---|
| 短消息 — 消息监听 | 平台提供接口，终端监听新消息 |
| 短消息 — 消息列表 | 平台提供接口，获取消息列表 |
| 短消息 — 回复消息 | 平台提供接口，终端回复消息 |
| 遥开遥闭 — 执行开/闭 MQ 消息 | 平台通过 MQ 下发遥控指令 |
| 遥开遥闭 — 执行开/闭结果 MQ 消息 | 终端上报遥控执行结果 |
| 终端对讲机录音上报 | 终端上传录音文件 |

---

## 10. 接口总览

| # | 接口名称 | 方法 | 路径 | 认证 |
|---|---|---|---|---|
| 1 | 能力声明 | POST | /api/terminal/pnr2100/init | sign |
| 2 | 获取服务器基础信息 | GET | /api/terminal/pnr2100/get/basic | 无 |
| 3 | 账号密码登录 | POST | /api/terminal/pnr2100/login | sign |
| 4 | 扫码获取二维码 | GET | /api/terminal/pnr2100/get/qrcode | sign |
| 5 | 扫码状态轮询 | POST | /api/terminal/pnr2100/get/bind/status | sign |
| 6 | 退出登录 | POST | /api/terminal/pnr2100/logout | token |
| 7 | 获取用户信息 | GET | /api/terminal/pnr2100/get/info | token |
| 8 | 巡更任务列表 | GET | /api/terminal/pnr2100/get/patrol/task | token |
| 9 | 巡更任务详情 | GET | /api/terminal/pnr2100/get/patrol/task/info/{id} | token |
| 10 | 巡更异常上报 | POST | /api/terminal/pnr2100/set/patrol/task/exception | token |
| 11 | 服务工单列表 | GET | /api/terminal/pnr2100/get/service/order | token |
| 12 | 服务工单详情 | GET | /api/terminal/pnr2100/get/service/order/info/{id} | token |
| 13 | 服务工单完成 | POST | /api/terminal/pnr2100/service/order/complete/{id} | token |
| 14 | 蓝牙环境上报 | POST | /api/terminal/pnr2100/report/surround | sign |
| 15 | GPS 位置上报 | POST | /api/terminal/pnr2100/report/gps | sign |
| 16 | 电池信息上报 | POST | /api/terminal/pnr2100/report/cell | sign |
| 17 | 文件上传 | POST | /api/applets/v1/common/uploadImage | Bearer |
| 18 | 测试巡更点 | GET | /api/terminal/pnr2100/test/point | token |

## See Also

- [PNR2100 定位功能验收标准与测试方案](pnr2100-positioning-acceptance-test-plan.md)