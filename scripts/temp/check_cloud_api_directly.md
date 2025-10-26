# 直接检查云端API返回数据

由于云端数据库已经修复（添加了status字段），现在需要验证API返回的数据是否正确。

## 方法1：浏览器开发者工具检查（推荐）

1. **打开批价单详情页**：PO202510-004
2. **打开开发者工具**：F12 或 右键->检查
3. **切换到 Network 标签**
4. **刷新页面**（Ctrl+R）
5. **查找API请求**：
   - 筛选：XHR
   - 找到类似 `/api/approval/106/flow` 的请求
6. **查看响应数据**：
   - 点击该请求
   - 切换到 Response 或 Preview 标签
   - 找到 `flow_data` 数组
   - 检查第一个元素（gxh的步骤）的 `status` 字段

### 预期结果

```json
{
  "success": true,
  "data": {
    "flow_data": [
      {
        "id": 79,
        "stage_name": "批价审批",
        "approver_name": "郭小会",
        "status": "approved",    ← 应该是这个值
        "completed_at": "2025-10-19T12:29:32..."
      },
      ...
    ]
  }
}
```

### 如果 status 不是 "approved"

说明后端API逻辑有问题，需要进一步排查。

### 如果 status 是 "approved"

说明是前端缓存或渲染问题：
1. **强制刷新**：Ctrl + Shift + R
2. **清除站点数据**：
   - F12 -> Application -> Storage -> Clear site data
   - 重新登录

3. **检查Console错误**：
   - F12 -> Console
   - 看是否有JavaScript错误

---

## 方法2：使用curl测试（需要登录token）

```bash
# 需要先获取登录token（在浏览器中复制Cookie）
curl -X GET 'https://your-domain.com/pricing_order/api/approval/106/flow' \
  -H 'Cookie: session=your_session_token' \
  -H 'Accept: application/json' | jq '.data.flow_data[0]'
```

---

## 方法3：临时添加日志（开发环境）

在 `app/routes/pricing_order_routes.py` 第973行之后添加：

```python
# 临时调试：打印返回数据
import json
print("=" * 50)
print(f"订单: {pricing_order.order_number}")
print("Flow Data:")
print(json.dumps(flow_data, ensure_ascii=False, indent=2))
print("=" * 50)
```

重启应用后访问页面，查看服务器日志输出。

---

## 快速验证命令

**在云端服务器执行**：

```bash
# 检查gxh的审批记录status字段
psql -d your_database -c "
SELECT ar.id, ar.step_id, u.real_name, ar.action, ar.status
FROM approval_record ar
JOIN users u ON ar.approver_id = u.id
WHERE ar.instance_id = 378
ORDER BY ar.timestamp;
"
```

预期输出应该包含：
```
 id  | step_id | real_name | action  | status
-----+---------+-----------+---------+---------
 558 | 79      | 郭小会    | approve | approved
 559 | 80      | 倪捷      | approve | approved
```

如果 status 是 NULL 或其他值，说明数据库修复未生效，需要重新执行修复脚本。
