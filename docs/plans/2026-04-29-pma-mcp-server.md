# PMA MCP Server 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 Mac mini 上部署 MCP Server，让团队成员通过 Claude Desktop 用自然语言查询 PMA 数据，权限完全复用 PMA 现有体系。

**Architecture:**
- Mac mini 运行 MCP Server（Python + uvicorn SSE），通过 Cloudflare Tunnel 对外暴露
- 鉴权复用现有 `cliproxy/oat_proxy.py` 的 Token + `Cf-Warp-Tag-Id` 设备绑定机制
- MCP Server 以用户身份调用 PMA 内部 API，由 PMA 做权限过滤

**Tech Stack:** Python 3.9, `mcp[cli]`, `uvicorn`, `starlette`, `httpx`, macOS LaunchAgent, Cloudflare Tunnel

---

## 总览

```
用户 Claude Desktop
  → Bearer Token + Cf-Warp-Tag-Id (CF Tunnel)
  → Mac mini MCP Server (port 8765)
    → 验证 Token → 查 devices.json → 得到 pma_user_id + pma_server
    → 调用 CN/SG NAS PMA 内部 API (X-Internal-Token + X-User-ID)
      → PMA get_viewable_data() 按权限过滤
      → 返回数据给 Claude
```

---

## Task 1: devices.json 添加 PMA 用户映射

**文件:** `~/cliproxy/data/devices.json`（Mac mini 上直接编辑）

**Step 1: 查看现有 devices.json**
```bash
ssh jing@100.110.41.83 "cat ~/cliproxy/data/devices.json"
```

**Step 2: 为每个 Token 类型的设备添加 PMA 字段**

在现有每条 token 记录里加两个字段：
```json
{
  "token-xxx": {
    "name": "用户姓名",
    "enabled": true,
    "locked_device_id": "...",
    "pma_user_id": 3,
    "pma_server": "cn"
  }
}
```

`pma_server` 可选值: `"cn"` (CN NAS) 或 `"sg"` (SG NAS)

**Step 3: 确认 PMA user_id 对应关系**

在 CN NAS 查询：
```bash
ssh -p 72 james.sh@100.118.231.15 "sudo /usr/local/bin/docker exec -i pma-postgres psql -U pma pma_synology -c 'SELECT id, username, real_name FROM \"user\" WHERE is_active=true ORDER BY id;'"
```

---

## Task 2: PMA 内部 API Blueprint

**文件:** `app/routes/internal_api.py`（新建）
**注册:** `app/__init__.py`

这是 PMA 新增的内部 API，只允许来自 Mac mini 的调用。

**Step 1: 新建文件 `app/routes/internal_api.py`**

```python
from flask import Blueprint, jsonify, request, g
from app.utils.access_control import get_viewable_data
from app.models import User, Quotation, Project, Company
from sqlalchemy import or_
import os

internal_bp = Blueprint('internal_api', __name__, url_prefix='/internal/api')

INTERNAL_TOKEN = os.environ.get('INTERNAL_API_TOKEN', '')

def require_internal_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Internal-Token', '')
        if not INTERNAL_TOKEN or token != INTERNAL_TOKEN:
            return jsonify({'error': 'Unauthorized'}), 401
        user_id = request.headers.get('X-User-ID', '')
        if not user_id:
            return jsonify({'error': 'Missing X-User-ID'}), 400
        user = User.query.get(int(user_id))
        if not user or not user.is_active:
            return jsonify({'error': 'User not found'}), 404
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


@internal_bp.route('/quotations')
@require_internal_auth
def list_quotations():
    status = request.args.get('status')
    search = request.args.get('search', '').strip()
    limit = min(int(request.args.get('limit', 20)), 100)

    query = get_viewable_data(Quotation, g.current_user,
                              [Quotation.is_deleted == False])
    if status:
        query = query.filter(Quotation.status == status)
    if search:
        query = query.filter(
            or_(Quotation.quotation_number.ilike(f'%{search}%'),
                Quotation.title.ilike(f'%{search}%'))
        )
    items = query.order_by(Quotation.created_at.desc()).limit(limit).all()

    return jsonify([{
        'id': q.id,
        'number': q.quotation_number,
        'title': q.title,
        'status': q.status,
        'total_amount': q.total_amount,
        'created_at': q.created_at.isoformat() if q.created_at else None,
        'owner': q.owner.real_name if q.owner else None,
    } for q in items])


@internal_bp.route('/projects')
@require_internal_auth
def list_projects():
    status = request.args.get('status')
    search = request.args.get('search', '').strip()
    limit = min(int(request.args.get('limit', 20)), 100)

    query = get_viewable_data(Project, g.current_user,
                              [Project.is_deleted == False])
    if status:
        query = query.filter(Project.status == status)
    if search:
        query = query.filter(Project.name.ilike(f'%{search}%'))
    items = query.order_by(Project.updated_at.desc()).limit(limit).all()

    return jsonify([{
        'id': p.id,
        'name': p.name,
        'status': p.status,
        'stage': p.stage if hasattr(p, 'stage') else None,
        'owner': p.owner.real_name if p.owner else None,
        'updated_at': p.updated_at.isoformat() if p.updated_at else None,
    } for p in items])


@internal_bp.route('/customers')
@require_internal_auth
def list_customers():
    search = request.args.get('search', '').strip()
    limit = min(int(request.args.get('limit', 20)), 100)

    query = get_viewable_data(Company, g.current_user,
                              [Company.is_deleted == False])
    if search:
        query = query.filter(Company.name.ilike(f'%{search}%'))
    items = query.order_by(Company.updated_at.desc()).limit(limit).all()

    return jsonify([{
        'id': c.id,
        'name': c.name,
        'industry': c.industry if hasattr(c, 'industry') else None,
        'owner': c.owner.real_name if c.owner else None,
    } for c in items])


@internal_bp.route('/approvals/pending')
@require_internal_auth
def pending_approvals():
    from app.models import ApprovalInstance, ApprovalNode
    nodes = ApprovalNode.query.join(ApprovalInstance).filter(
        ApprovalNode.approver_id == g.current_user.id,
        ApprovalNode.status == 'pending',
        ApprovalInstance.status == 'pending'
    ).order_by(ApprovalNode.created_at.asc()).limit(20).all()

    return jsonify([{
        'instance_id': n.instance_id,
        'object_type': n.instance.object_type if hasattr(n.instance, 'object_type') else None,
        'object_id': n.instance.object_id if hasattr(n.instance, 'object_id') else None,
        'created_at': n.created_at.isoformat() if n.created_at else None,
    } for n in nodes])


@internal_bp.route('/stats/summary')
@require_internal_auth
def stats_summary():
    from datetime import datetime, date
    from sqlalchemy import func
    now = datetime.now()
    month_start = date(now.year, now.month, 1)

    q_query = get_viewable_data(Quotation, g.current_user,
                                [Quotation.is_deleted == False,
                                 Quotation.created_at >= month_start])
    total = q_query.count()
    pending = q_query.filter(Quotation.status == 'pending').count()

    return jsonify({
        'month': now.strftime('%Y-%m'),
        'quotations_total': total,
        'quotations_pending': pending,
    })
```

**Step 2: 注册 Blueprint，修改 `app/__init__.py`**

找到其他 blueprint 注册的位置，添加：
```python
from app.routes.internal_api import internal_bp
app.register_blueprint(internal_bp)
```

**Step 3: 添加环境变量 `INTERNAL_API_TOKEN`**

在 CN NAS 的 `.env` 文件中添加（生成一个随机字符串）：
```bash
# 生成随机 token
python3 -c "import secrets; print(secrets.token_hex(32))"
```

把生成的值加入 CN NAS 和 SG NAS 的环境变量。

**Step 4: 本地测试**
```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
export INTERNAL_API_TOKEN=your_token_here
python run.py &
curl -s -H "X-Internal-Token: your_token_here" \
     -H "X-User-ID: 1" \
     "http://localhost:5000/internal/api/quotations?limit=3" | python3 -m json.tool
```

预期：返回 JSON 列表

**Step 5: 部署到 CN NAS**
```bash
# 按现有部署流程
cd /Users/nijie/Documents/PMA
git add app/routes/internal_api.py app/__init__.py
git commit -m "feat: add internal API for MCP server"
# 然后走 update.sh 部署流程
```

---

## Task 3: Mac mini 安装依赖

**Step 1: 安装 Python 包**
```bash
ssh jing@100.110.41.83 "pip3 install 'mcp[cli]' uvicorn starlette httpx"
```

**Step 2: 验证安装**
```bash
ssh jing@100.110.41.83 "python3 -c 'import mcp; import uvicorn; import httpx; print(\"ok\")'"
```
预期：输出 `ok`

---

## Task 4: MCP Server 主文件

**文件:** `~/cliproxy/pma_mcp_server.py`（Mac mini 上新建）

**Step 1: 创建 MCP Server 文件**

```python
#!/usr/bin/env python3
"""PMA MCP Server — 通过 CF Tunnel 鉴权，以用户身份查询 PMA 数据"""
import json, os, re, threading
from contextvars import ContextVar
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# ── 配置 ──────────────────────────────────────────────────────────────────────
PORT           = 8765
DEVICES_FILE   = os.path.join(os.path.dirname(__file__), "data", "devices.json")
INTERNAL_TOKEN = os.environ.get("INTERNAL_API_TOKEN", "")
CN_PMA_URL     = os.environ.get("CN_PMA_URL", "http://100.118.231.15:5000")
SG_PMA_URL     = os.environ.get("SG_PMA_URL", "http://100.87.155.40:5000")

_lock = threading.Lock()
current_device: ContextVar[Optional[dict]] = ContextVar("current_device", default=None)

# ── devices.json 工具 ─────────────────────────────────────────────────────────

def _load_devices():
    try:
        with open(DEVICES_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def _save_devices(data):
    tmp = DEVICES_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, DEVICES_FILE)

# ── 鉴权（复用 oat_proxy.py 逻辑）────────────────────────────────────────────

def _validate_request(headers) -> tuple[Optional[dict], Optional[str]]:
    """返回 (device_info, error_message)"""
    auth = headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None, "Missing Bearer token"

    token = auth[7:].strip()
    devices = _load_devices()
    if token not in devices:
        return None, "Invalid token"

    device = devices[token]
    if not device.get("enabled", True):
        return None, "Device disabled"

    # pma_user_id 必须配置
    if not device.get("pma_user_id"):
        return None, "Token not linked to PMA user"

    # 设备绑定（Cf-Warp-Tag-Id）
    warp_id = headers.get("cf-warp-tag-id", "").strip()
    locked = device.get("locked_device_id")
    if locked is None and warp_id:
        with _lock:
            devs = _load_devices()
            devs[token]["locked_device_id"] = warp_id
            _save_devices(devs)
    elif locked and warp_id and warp_id != locked:
        return None, "Device not authorized for this token"

    return device, None


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        device, error = _validate_request(request.headers)
        if device is None:
            return JSONResponse({"error": error}, status_code=401)
        token = current_device.set(device)
        try:
            return await call_next(request)
        finally:
            current_device.reset(token)


# ── PMA API 客户端 ─────────────────────────────────────────────────────────────

def _pma_url(server: str) -> str:
    return CN_PMA_URL if server == "cn" else SG_PMA_URL

async def _pma_get(path: str, params: dict = None) -> dict | list:
    device = current_device.get()
    base_url = _pma_url(device.get("pma_server", "cn"))
    user_id  = device["pma_user_id"]
    headers  = {
        "X-Internal-Token": INTERNAL_TOKEN,
        "X-User-ID": str(user_id),
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{base_url}{path}", params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()


# ── MCP Server ────────────────────────────────────────────────────────────────

mcp = FastMCP("PMA")


@mcp.tool()
async def search_quotations(
    search: str = "",
    status: str = "",
    limit: int = 10
) -> str:
    """
    搜索报价单。
    status 可选: draft / pending / approved / rejected
    返回报价单列表，包含编号、标题、状态、金额、负责人。
    """
    params = {"limit": limit}
    if search: params["search"] = search
    if status: params["status"] = status
    data = await _pma_get("/internal/api/quotations", params)
    if not data:
        return "没有找到符合条件的报价单。"
    lines = [f"找到 {len(data)} 份报价单：\n"]
    for q in data:
        amount = f"¥{q['total_amount']/10000:.1f}万" if q.get('total_amount') else "金额未定"
        lines.append(f"• {q['number']} | {q['title']} | {q['status']} | {amount} | {q['owner']}")
    return "\n".join(lines)


@mcp.tool()
async def search_projects(
    search: str = "",
    status: str = "",
    limit: int = 10
) -> str:
    """
    搜索项目。
    status 可选: active / completed / cancelled
    返回项目列表，包含名称、状态、负责人、最后更新时间。
    """
    params = {"limit": limit}
    if search: params["search"] = search
    if status: params["status"] = status
    data = await _pma_get("/internal/api/projects", params)
    if not data:
        return "没有找到符合条件的项目。"
    lines = [f"找到 {len(data)} 个项目：\n"]
    for p in data:
        lines.append(f"• {p['name']} | {p['status']} | {p['owner']} | 更新: {p['updated_at'][:10] if p.get('updated_at') else '-'}")
    return "\n".join(lines)


@mcp.tool()
async def search_customers(search: str, limit: int = 10) -> str:
    """
    搜索客户（公司）。
    返回公司名称、行业、负责人。
    """
    data = await _pma_get("/internal/api/customers", {"search": search, "limit": limit})
    if not data:
        return f"没有找到包含"{search}"的客户。"
    lines = [f"找到 {len(data)} 个客户：\n"]
    for c in data:
        lines.append(f"• {c['name']} | {c.get('industry', '-')} | {c['owner']}")
    return "\n".join(lines)


@mcp.tool()
async def get_pending_approvals() -> str:
    """
    获取当前用户待处理的审批项目。
    """
    data = await _pma_get("/internal/api/approvals/pending")
    if not data:
        return "暂无待审批项目。"
    lines = [f"你有 {len(data)} 项待审批：\n"]
    for a in data:
        lines.append(f"• {a['object_type']} #{a['object_id']} | 提交于 {a['created_at'][:10] if a.get('created_at') else '-'}")
    return "\n".join(lines)


@mcp.tool()
async def get_monthly_summary() -> str:
    """
    获取当前用户本月报价汇总数据。
    """
    data = await _pma_get("/internal/api/stats/summary")
    return (
        f"📊 {data['month']} 月度汇总\n"
        f"报价单总数：{data['quotations_total']}\n"
        f"待确认：{data['quotations_pending']}\n"
    )


# ── 启动 ──────────────────────────────────────────────────────────────────────

app = mcp.sse_app()
app.add_middleware(AuthMiddleware)

if __name__ == "__main__":
    import uvicorn
    print(f"[pma-mcp] listening on 0.0.0.0:{PORT}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
```

**Step 2: 上传到 Mac mini**
```bash
scp /tmp/pma_mcp_server.py jing@100.110.41.83:~/cliproxy/pma_mcp_server.py
```

**Step 3: 手动测试启动**
```bash
ssh jing@100.110.41.83 "INTERNAL_API_TOKEN=your_token CN_PMA_URL=http://100.118.231.15:5000 python3 ~/cliproxy/pma_mcp_server.py &"
# 等3秒后验证
ssh jing@100.110.41.83 "curl -s http://localhost:8765/"
```
预期：收到 MCP 相关响应或 404（不是 connection refused）

---

## Task 5: macOS LaunchAgent 配置

**文件:** `~/Library/LaunchAgents/com.jing.pma-mcp.plist`（Mac mini 上新建）

**Step 1: 创建 plist 文件**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jing.pma-mcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/jing/cliproxy/pma_mcp_server.py</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>INTERNAL_API_TOKEN</key>
        <string>REPLACE_WITH_ACTUAL_TOKEN</string>
        <key>CN_PMA_URL</key>
        <string>http://100.118.231.15:5000</string>
        <key>SG_PMA_URL</key>
        <string>http://100.87.155.40:5000</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/jing/cliproxy/pma_mcp.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/jing/cliproxy/pma_mcp_error.log</string>
</dict>
</plist>
```

**Step 2: 加载服务**
```bash
ssh jing@100.110.41.83 "launchctl load ~/Library/LaunchAgents/com.jing.pma-mcp.plist"
ssh jing@100.110.41.83 "launchctl list | grep pma-mcp"
```
预期：显示进程 PID（非 `-`）

---

## Task 6: Cloudflare Tunnel 添加新 hostname

**文件:** `~/.cloudflared/macmini-proxy.yml`（Mac mini 上修改）

**Step 1: 修改 macmini-proxy.yml**
```yaml
tunnel: 58e9ab52-88ee-4d6d-9084-7d19a91cfa3e
credentials-file: /Users/jing/.cloudflared/58e9ab52-88ee-4d6d-9084-7d19a91cfa3e.json

ingress:
  - hostname: mac-proxy.jamesgpone.win
    service: https://localhost:8317
    originRequest:
      noTLSVerify: true
  - hostname: pma-mcp.jamesgpone.win       # 新增
    service: http://localhost:8765
  - service: http_status:404
```

**Step 2: 在 Cloudflare Dashboard 添加 DNS 记录**

登录 dash.cloudflare.com → jamesgpone.win → DNS：
- 类型: CNAME
- 名称: `pma-mcp`
- 目标: `<tunnel-id>.cfargotunnel.com`（tunnel ID: `58e9ab52-88ee-4d6d-9084-7d19a91cfa3e`）
- Proxy: 开启（橙色云朵）

**Step 3: 重启 CF Tunnel**
```bash
ssh jing@100.110.41.83 "launchctl unload ~/Library/LaunchAgents/com.cloudflare.macmini-proxy.plist && launchctl load ~/Library/LaunchAgents/com.cloudflare.macmini-proxy.plist"
```

**Step 4: 验证 Tunnel**
```bash
curl -s -o /dev/null -w "%{http_code}" https://pma-mcp.jamesgpone.win/
```
预期：`200` 或 `401`（不是 `404` 或连接失败）

---

## Task 7: Claude Desktop 用户配置

每个用户在自己 Mac 上编辑：
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

添加：
```json
{
  "mcpServers": {
    "pma": {
      "url": "https://pma-mcp.jamesgpone.win/sse",
      "headers": {
        "Authorization": "Bearer <用户现有的Claude代理Token>"
      }
    }
  }
}
```

重启 Claude Desktop。

**验证：** 在 Claude Desktop 里问："帮我查一下最近的报价单" → 应该看到 Claude 调用 MCP 工具并返回数据。

---

## 实施顺序

1. Task 1 → 确认 devices.json 用户映射（需手动对照 PMA 用户表）
2. Task 2 → PMA 内部 API（本地测试通过后部署到 CN NAS）
3. Task 3 → Mac mini 安装依赖
4. Task 4 → MCP Server 文件 + 手动测试
5. Task 5 → LaunchAgent 持久化运行
6. Task 6 → CF Tunnel 配置（需要 Cloudflare Dashboard 操作）
7. Task 7 → 用户配置 Claude Desktop

---

## 注意事项

- `INTERNAL_API_TOKEN` 要足够长（32 字节 hex），CN/SG NAS 需要相同的值
- CN NAS 的 PMA API 端口默认是 5000，如有不同请修改 `CN_PMA_URL`
- Task 2 中 `ApprovalNode/ApprovalInstance` 模型名需对照实际代码确认
- MCP SSE 连接是长连接，CF Tunnel 默认支持，无需额外配置
- 初次部署建议只开 CN NAS，验证稳定后再接 SG NAS
