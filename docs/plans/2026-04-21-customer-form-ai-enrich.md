# Customer Form AI Enrich Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在客户创建/编辑表单中，加入实时内部查重（纯代码）和 AI 一键回填（Tavily + Claude）两个功能。

**Architecture:**
- 内部查重：前端防抖 → `GET /customer/api/similar-companies?q=` → 复用现有 `normalize_company_name()` + difflib 模糊匹配 → 下拉提示
- AI 回填：点击 ✨ 按钮 → `POST /customer/api/ai-enrich` → Tavily 搜索 → Claude 解析结构化结果 → 前端面板展示 → 用户确认 → 填入表单

**Tech Stack:** Flask, Tavily Python SDK (`TAVILY_API_KEY`), Anthropic SDK, Tailwind CSS, vanilla JS

---

## Task 1: 后端 — 轻量相似企业查询 API

**Files:**
- Modify: `app/views/customer.py` — 在文件末尾 `normalize_company_name` 函数之前新增路由

**Step 1: 新增 API 端点**

在 `app/views/customer.py` 中，找到 `@customer.route('/api/detect-duplicates'` 前面，插入：

```python
@customer.route('/api/similar-companies')
@login_required
@permission_required('customer', 'view')
def similar_companies_api():
    """实时相似企业查询，供创建表单防抖调用"""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'results': []})

    from app.utils.access_control import get_viewable_data
    import difflib

    companies = get_viewable_data(
        Company, current_user, [Company.is_deleted == False]
    ).all()

    q_norm = normalize_company_name(q)
    results = []

    for c in companies:
        c_norm = normalize_company_name(c.company_name)
        if not c_norm:
            continue
        if q_norm == c_norm:
            score = 1.0
        elif len(q_norm) < 2 or len(c_norm) < 2:
            continue
        else:
            score = difflib.SequenceMatcher(None, q_norm, c_norm).ratio()

        if score >= 0.5:
            results.append({
                'id': c.id,
                'name': c.company_name,
                'score': round(score, 2),
                'url': url_for('customer.view_company', company_id=c.id),
            })

    results.sort(key=lambda x: x['score'], reverse=True)
    return jsonify({'results': results[:6]})
```

**Step 2: 手动测试端点**

启动本地服务后访问：
```
GET /customer/api/similar-companies?q=华为
```
期望返回 `{"results": [...]}` 格式，无报错。

**Step 3: Commit**

```bash
git add app/views/customer.py
git commit -m "feat(customer): add similar-companies API for real-time duplicate check"
```

---

## Task 2: 前端 — 实时查重 UI（输入框下拉）

**Files:**
- Modify: `app/templates/customer/partials/_company_form_fields.html`

**Step 1: 修改模板 — 企业名称区域**

将现有 `<!-- 企业名称 -->` div 替换为以下内容（保留原有结构，增加 AI 按钮 + 查重下拉）：

```html
<!-- 企业名称 -->
<div class="relative">
    <label for="company_name" class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
        {{ _('企业名称') }}<span class="text-red-500">*</span>
    </label>
    <div class="flex gap-2">
        <div class="relative flex-1">
            <input type="text" id="company_name" name="company_name"
                   data-field-code="company_name"
                   class="form-input block w-full rounded-lg border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-primary focus:ring-primary text-sm shadow-sm"
                   placeholder="{{ _('请输入企业名称') }}"
                   autocomplete="off"
                   required>
            <!-- 查重下拉 -->
            <div id="companySimilarList"
                 class="hidden absolute z-50 w-full mt-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg max-h-56 overflow-y-auto text-sm">
            </div>
        </div>
        <!-- AI 回填按钮 -->
        <button type="button" id="aiEnrichBtn"
                title="{{ _('AI 智能回填') }}"
                class="flex-shrink-0 px-3 py-2 rounded-lg border border-primary text-primary hover:bg-primary hover:text-white transition-colors text-sm font-medium flex items-center gap-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>
            </svg>
            AI
        </button>
    </div>
    <!-- 名称错误提示 -->
    <p id="companyNameError" class="hidden mt-1 text-sm text-red-500"></p>
    <!-- AI 回填结果面板（默认隐藏） -->
    <div id="aiEnrichPanel" class="hidden mt-3 p-4 rounded-lg border border-primary/30 bg-primary/5 dark:bg-primary/10 space-y-3">
        <div class="flex items-center justify-between">
            <p class="text-sm font-medium text-slate-700 dark:text-slate-300">{{ _('AI 建议') }}</p>
            <button type="button" id="aiEnrichClose" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
            </button>
        </div>
        <div id="aiEnrichContent"></div>
    </div>
</div>
```

**Step 2: 在模板末尾添加 JS（查重部分）**

在文件最末尾加入 `<script>` 块：

```html
<script>
(function() {
    const nameInput = document.getElementById('company_name');
    const similarList = document.getElementById('companySimilarList');
    let debounceTimer = null;

    function renderSimilarList(results) {
        if (!results.length) {
            similarList.classList.add('hidden');
            return;
        }
        similarList.innerHTML = results.map(r => {
            const badge = r.score >= 0.9
                ? '<span class="text-xs text-red-500 font-medium ml-1">高度相似</span>'
                : r.score >= 0.7
                    ? '<span class="text-xs text-yellow-500 font-medium ml-1">相似</span>'
                    : '';
            return `<a href="${r.url}" target="_blank"
                       class="flex items-center justify-between px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer border-b border-slate-100 dark:border-slate-700 last:border-0">
                        <span class="text-slate-800 dark:text-slate-200">${r.name}${badge}</span>
                        <span class="text-xs text-slate-400">查看</span>
                    </a>`;
        }).join('');
        similarList.classList.remove('hidden');
    }

    nameInput && nameInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const q = this.value.trim();
        if (q.length < 2) {
            similarList.classList.add('hidden');
            return;
        }
        debounceTimer = setTimeout(function() {
            fetch(`/customer/api/similar-companies?q=${encodeURIComponent(q)}`)
                .then(r => r.json())
                .then(data => renderSimilarList(data.results || []))
                .catch(() => {});
        }, 500);
    });

    // 点击外部关闭
    document.addEventListener('click', function(e) {
        if (similarList && !similarList.contains(e.target) && e.target !== nameInput) {
            similarList.classList.add('hidden');
        }
    });
})();
</script>
```

**Step 3: 验证查重 UI**

本地打开新建客户页面，输入已存在的企业名称前几个字，确认下方出现匹配列表。

**Step 4: Commit**

```bash
git add app/templates/customer/partials/_company_form_fields.html
git commit -m "feat(customer): add real-time duplicate check dropdown on company name input"
```

---

## Task 3: 后端 — AI 回填 API

**Files:**
- Modify: `app/views/customer.py` — 紧接 Task 1 端点后新增

**Step 1: 新增 AI 回填端点**

```python
@customer.route('/api/ai-enrich', methods=['POST'])
@login_required
@permission_required('customer', 'create')
def ai_enrich_company():
    """AI 回填：Tavily 搜索 + Claude 解析，返回企业结构化信息"""
    import os, json as _json
    data = request.get_json(silent=True) or {}
    company_name = (data.get('company_name') or '').strip()
    if not company_name:
        return jsonify({'success': False, 'message': '请输入企业名称'}), 400

    # 1. Tavily 搜索
    tavily_key = os.environ.get('TAVILY_API_KEY', '').strip()
    if not tavily_key:
        return jsonify({'success': False, 'message': '未配置 TAVILY_API_KEY'}), 500

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=tavily_key)
        search_result = client.search(
            query=f'{company_name} 公司 官网 地址 简介',
            search_depth='basic',
            max_results=5,
            include_answer=True,
        )
    except Exception as e:
        current_app.logger.error(f'[ai_enrich] Tavily 失败: {e}')
        return jsonify({'success': False, 'message': f'网络搜索失败: {e}'}), 500

    # 2. Claude 解析
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    if not anthropic_key:
        return jsonify({'success': False, 'message': '未配置 ANTHROPIC_API_KEY'}), 500

    snippets = '\n'.join(
        f"- {r.get('title','')}: {r.get('content','')[:300]}"
        for r in search_result.get('results', [])
    )
    answer = search_result.get('answer', '')
    search_text = f"Answer: {answer}\n\nSnippets:\n{snippets}"

    prompt = f"""根据以下搜索结果，提取关于企业「{company_name}」的结构化信息。

搜索结果：
{search_text}

请以 JSON 格式返回，字段如下（无法确定的字段返回空字符串）：
{{
  "official_names": ["正式名称候选1", "正式名称候选2"],
  "address": "详细地址（中文）",
  "country": "国家（英文，如 China / Singapore）",
  "description": "100字以内的企业简介（中文）"
}}

只返回 JSON，不要任何其他文字。"""

    try:
        import anthropic
        claude = anthropic.Anthropic(api_key=anthropic_key)
        msg = claude.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=512,
            messages=[{'role': 'user', 'content': prompt}],
        )
        raw = msg.content[0].text.strip()
        # 剥离可能的 markdown 代码块
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        parsed = _json.loads(raw)
    except Exception as e:
        current_app.logger.error(f'[ai_enrich] Claude 解析失败: {e}')
        return jsonify({'success': False, 'message': f'AI 解析失败: {e}'}), 500

    return jsonify({
        'success': True,
        'official_names': parsed.get('official_names', []),
        'address': parsed.get('address', ''),
        'country': parsed.get('country', ''),
        'description': parsed.get('description', ''),
    })
```

**Step 2: 手动测试端点**

```bash
curl -X POST http://localhost:5000/customer/api/ai-enrich \
  -H "Content-Type: application/json" \
  -d '{"company_name": "华为技术有限公司"}' \
  -b "session=<your_session_cookie>"
```

期望返回包含 `official_names`, `address`, `description` 的 JSON。

**Step 3: Commit**

```bash
git add app/views/customer.py
git commit -m "feat(customer): add AI enrich endpoint using Tavily + Claude Haiku"
```

---

## Task 4: 前端 — AI 按钮 + 回填确认面板

**Files:**
- Modify: `app/templates/customer/partials/_company_form_fields.html` — 在 Task 2 的 `<script>` 块中追加 AI 按钮逻辑

**Step 1: 在现有 `<script>` 块中追加 AI 回填逻辑**

在 `})();` 闭合前追加：

```javascript
    // ---- AI 回填 ----
    const aiBtn = document.getElementById('aiEnrichBtn');
    const aiPanel = document.getElementById('aiEnrichPanel');
    const aiContent = document.getElementById('aiEnrichContent');
    const aiClose = document.getElementById('aiEnrichClose');

    function renderAiPanel(data) {
        const nameOptions = (data.official_names || []).map(n =>
            `<label class="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="ai_name_pick" value="${n}" class="text-primary">
                <span class="text-sm text-slate-800 dark:text-slate-200">${n}</span>
            </label>`
        ).join('');

        aiContent.innerHTML = `
            ${nameOptions ? `
            <div class="space-y-1">
                <p class="text-xs text-slate-500 mb-1">选择正式名称（点选后自动填入）</p>
                ${nameOptions}
            </div>` : ''}
            ${data.address ? `
            <div class="text-sm">
                <span class="text-slate-500 text-xs">地址</span>
                <p class="text-slate-800 dark:text-slate-200 mt-0.5">${data.address}</p>
            </div>` : ''}
            ${data.description ? `
            <div class="text-sm">
                <span class="text-slate-500 text-xs">企业简介</span>
                <p class="text-slate-800 dark:text-slate-200 mt-0.5">${data.description}</p>
            </div>` : ''}
            <div class="flex gap-2 pt-1">
                <button type="button" id="aiApplyBtn"
                        class="flex-1 py-1.5 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors">
                    应用到表单
                </button>
            </div>`;

        // 选择正式名称时自动填入输入框
        aiContent.querySelectorAll('input[name="ai_name_pick"]').forEach(radio => {
            radio.addEventListener('change', function() {
                nameInput.value = this.value;
            });
        });

        // 应用按钮
        const applyBtn = document.getElementById('aiApplyBtn');
        applyBtn && applyBtn.addEventListener('click', function() {
            // 填入选中名称（如有）
            const picked = aiContent.querySelector('input[name="ai_name_pick"]:checked');
            if (picked) nameInput.value = picked.value;

            // 填入地址
            if (data.address) {
                const addrField = document.getElementById('address');
                if (addrField) addrField.value = data.address;
            }

            // 填入国家
            if (data.country) {
                const countryField = document.getElementById('country');
                if (countryField) countryField.value = data.country;
            }

            // 填入备注/简介
            if (data.description) {
                const notesField = document.getElementById('notes');
                if (notesField && !notesField.value) notesField.value = data.description;
            }

            aiPanel.classList.add('hidden');
        });

        aiPanel.classList.remove('hidden');
    }

    aiBtn && aiBtn.addEventListener('click', function() {
        const q = nameInput ? nameInput.value.trim() : '';
        if (!q) {
            alert('请先输入企业名称');
            return;
        }
        aiBtn.disabled = true;
        aiBtn.innerHTML = '<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg> 查询中';

        fetch('/customer/api/ai-enrich', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({company_name: q}),
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                renderAiPanel(data);
            } else {
                alert(data.message || 'AI 查询失败，请稍后重试');
            }
        })
        .catch(() => alert('网络错误，请稍后重试'))
        .finally(() => {
            aiBtn.disabled = false;
            aiBtn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg> AI';
        });
    });

    aiClose && aiClose.addEventListener('click', function() {
        aiPanel.classList.add('hidden');
    });
```

**Step 2: 验证完整流程**

1. 打开新建客户页面
2. 输入企业名称 → 确认查重下拉出现
3. 点击 **AI** 按钮 → 确认按钮变为加载状态
4. 等待约 3-5 秒 → 确认 AI 面板出现，显示正式名称、地址、简介
5. 选择名称 → 点击"应用到表单" → 确认各字段填入正确
6. 关闭面板（×）→ 面板隐藏

**Step 3: Commit**

```bash
git add app/templates/customer/partials/_company_form_fields.html
git commit -m "feat(customer): add AI enrich button with name correction and field auto-fill"
```

---

## Task 5: 翻译补全（可选）

**Files:**
- Modify: `app/translations/en/LC_MESSAGES/messages.po`

新增以下翻译条目（如需英文界面支持）：

```po
msgid "AI 智能回填"
msgstr "AI Auto-fill"

msgid "AI 建议"
msgstr "AI Suggestions"
```

编译翻译：
```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && pybabel compile -d app/translations
```

**Commit**

```bash
git add app/translations/
git commit -m "i18n: add AI enrich translations"
```

---

## 验收标准

- [ ] 输入企业名称 ≥2 字后 500ms，下方出现系统内相似企业列表
- [ ] 点击列表项可跳转查看已有企业
- [ ] 点击 AI 按钮，按钮显示加载动画
- [ ] 3-5 秒后出现 AI 面板（正式名称候选 + 地址 + 简介）
- [ ] 点选名称后自动填入输入框
- [ ] 点击"应用到表单"后，地址/备注字段正确填入
- [ ] 关闭按钮可隐藏 AI 面板
- [ ] TAVILY_API_KEY 未配置时，AI 按钮返回友好错误提示
