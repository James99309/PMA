#!/bin/bash
#
# AI 写代码质量自检 hook(PostToolUse 触发)
# ─────────────────────────────────────────────────────────────────────────────
# 目的:在 Edit/Write/MultiEdit 之后,自动 grep 改动的文件,
#       发现 N+1 / 模板 lazy load / 宏名错引 三类常见问题,
#       通过 stderr 反馈给 AI(AI 看到后会自我修正)。
#
# 触发:配置在 .claude/settings.local.json 的 hooks.PostToolUse,
#       matcher: "Edit|Write|MultiEdit"
#
# 输入:Claude Code 通过 stdin 传 JSON:
#       {"tool_name": "...", "tool_input": {"file_path": "...", ...}}
#
# 输出:
#   - exit 0:无问题或仅有提醒(stderr 内容 AI 可见)
#   - exit 2:严重问题(阻断,极少用 — 这套 hook 不阻断)
# ─────────────────────────────────────────────────────────────────────────────

INPUT=$(cat)

# jq 不可用时降级用 python(项目大概率有)
extract_field() {
    if command -v jq >/dev/null 2>&1; then
        echo "$INPUT" | jq -r "$1 // empty"
    else
        echo "$INPUT" | python3 -c "import sys, json; d = json.load(sys.stdin); \
            keys = '$1'.replace('.', ' ').split(); v = d; \
            [v := (v.get(k) if isinstance(v, dict) else None) for k in keys]; \
            print(v if v is not None else '')" 2>/dev/null
    fi
}

FILE=$(extract_field '.tool_input.file_path')
TOOL=$(extract_field '.tool_name')

# 只对路由 / helpers / 模板生效
[[ "$FILE" =~ app/(routes|helpers|templates)/.*\.(py|html)$ ]] || exit 0
[[ -f "$FILE" ]] || exit 0

WARNINGS=()

# ─── 检查 1:routes/helpers 的 N+1 风险 ────────────────────────────────────
# 启发式:文件出现 .paginate( 或 Model.query.xxx.all() / .first()
# 但全文找不到 .options(joinedload|selectinload|subqueryload)
# 且模板侧或自身代码会循环访问 ORM 关联(由人/AI 判断)
if [[ "$FILE" =~ app/(routes|helpers)/.*\.py$ ]]; then
    if grep -qE '(\.paginate\(|\.query\..*\.all\(\)|\.query\..*\.filter\(.*\)\.all\(\))' "$FILE" 2>/dev/null \
       && ! grep -qE '\.options\((joinedload|selectinload|subqueryload)' "$FILE" 2>/dev/null \
       && ! grep -qE '#\s*eager-loaded by ORM' "$FILE" 2>/dev/null; then
        WARNINGS+=("⚠️  [N+1 风险] $FILE
    检测到 .paginate() 或 .query.all() 但未找到 .options(joinedload/selectinload/subqueryload)。
    后续模板若循环访问 obj.relation,会触发 N 次额外 SQL。
    动作:
      • 若关联会被遍历访问 → 加 .options(joinedload(Model.relation))
      • 若确认不会触发 → 在该 query 旁加注释  '# eager-loaded by ORM relation defaults'  跳过本检查
      • 规范:CLAUDE-DATABASE.md 「查询性能规范」")
    fi
fi

# ─── 检查 2:模板里循环内访问关联 ─────────────────────────────────────────
# 启发式:.html 出现 {% for x in obj.relation %} 或 {% for x in items %}
# 且循环体内有 x.something.field(多级属性访问 → 极大概率 lazy load)
if [[ "$FILE" =~ \.html$ ]]; then
    if grep -qE '\{%\s*for\s+\w+\s+in\s+' "$FILE" 2>/dev/null; then
        # 简化版:统计 .field.subfield 模式(grep -c 多文件返多行,wc -l 才靠谱)
        LAZY_HITS=$(grep -E '\{\{[^}]*\b\w+\.\w+\.\w+' "$FILE" 2>/dev/null | wc -l | tr -d ' ')
        LAZY_HITS=${LAZY_HITS:-0}
        if [[ "$LAZY_HITS" -gt 0 ]] 2>/dev/null; then
            WARNINGS+=("ℹ️  [模板 lazy load 提示] $FILE
    模板里有 N 处 'obj.relation.field' 多级访问(在循环内 → N+1)。
    确认对应路由的 query 已加 .options(joinedload(Model.relation))。
    若已加 → 忽略本提示。")
        fi
    fi
fi

# ─── 检查 3:模板宏引用 vs 组件实际导出 ───────────────────────────────────
# 这就是 tw_profile.html 的 render_tw_card_shell / render_tw_button bug:
# 模板 import 了组件文件,但组件根本没 export 该宏 → 渲染时才暴露
if [[ "$FILE" =~ \.html$ ]]; then
    # 提取所有 {% from 'X' import macro1, macro2 %} 行(用 awk 避 BSD sed PCRE 限制)
    while IFS= read -r LINE; do
        # 路径:第一对 '...' 或 "..." 内的字符串
        COMPONENT=$(echo "$LINE" | awk -F"'" '/from /{print $2; exit}')
        [[ -z "$COMPONENT" ]] && COMPONENT=$(echo "$LINE" | awk -F'"' '/from /{print $2; exit}')
        # 宏列表:截取 'import' 与 'with' 或 '%}' 之间的内容
        MACROS=$(echo "$LINE" | awk -F'import ' '{print $2}' | awk -F' with ' '{print $1}' | awk -F'%}' '{print $1}')
        [[ -z "$COMPONENT" || -z "$MACROS" ]] && continue

        # 解析模板文件实际路径(默认在 app/templates/)
        COMPONENT_FILE="app/templates/$COMPONENT"
        [[ -f "$COMPONENT_FILE" ]] || continue

        # 逐个宏名验证
        IFS=',' read -ra MACRO_LIST <<< "$MACROS"
        for M in "${MACRO_LIST[@]}"; do
            NAME=$(echo "$M" | tr -d ' ' | sed 's/as.*//')  # 处理 'a as b' 别名
            [[ -z "$NAME" ]] && continue
            if ! grep -qE "^\s*\{%\s*macro\s+${NAME}\s*\(" "$COMPONENT_FILE" 2>/dev/null; then
                WARNINGS+=("❌ [宏不存在] $FILE
    导入了 '${NAME}' 自 $COMPONENT,但该组件文件没定义该宏。
    页面运行时才会 UndefinedError。请到 $COMPONENT_FILE 确认真实宏名。")
            fi
        done
    done < <(grep -E "^\s*\{%\s*from\s+['\"]components" "$FILE" 2>/dev/null)
fi

# ─── 检查 4:Write 新模板 / 新 JS 时输出 AT 组件清单 ──────────────────────
# 目的:写新功能前确认现有 AT 组件是否够用,避免造轮子
# 触发:tool == Write 且文件在 app/templates/ 或 app/static/js/(排除已存在的修改)
if [[ "$TOOL" == "Write" ]] \
   && [[ "$FILE" =~ app/(templates|static/js)/ ]] \
   && [[ ! "$FILE" =~ /(_archived|partials)/ ]]; then

    # 收集 AT 组件清单(文件名 + 顶部注释首行作描述)
    list_components() {
        local DIR="$1" PREFIX="$2" EXT="$3" COMMENT_PATTERN="$4"
        for F in "$DIR"/${PREFIX}*.${EXT}; do
            [[ -f "$F" ]] || continue
            local NAME=$(basename "$F" ".$EXT")
            # 取头 10 行里第一条非空、非纯符号的中文/英文注释
            local DESC=$(head -10 "$F" \
                | grep -oE "${COMMENT_PATTERN}" \
                | head -1 \
                | sed 's/^[ #*{%-]*//; s/[ #}*]*$//' \
                | head -c 80)
            printf "  • %-32s  %s\n" "$NAME" "${DESC:-(无描述)}" >&2
        done
    }

    echo "" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "  📦 AT 组件复用提示  ($TOOL → $FILE)" >&2
    echo "  写新文件前确认下列组件不能复用,避免造轮子:" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2

    if [[ "$FILE" =~ app/templates/ ]]; then
        echo "" >&2
        echo "【AT Jinja 组件】(import 自 components/at_*.html)" >&2
        list_components "app/templates/components" "at_" "html" "[^a-zA-Z]+[A-Z一-龥a-z][^#}]*"
    fi

    if [[ "$FILE" =~ app/static/js/ ]] || [[ "$FILE" =~ app/templates/ ]]; then
        echo "" >&2
        echo "【AT JS 工具】(<script src=\"js/at-*.js\">)" >&2
        list_components "app/static/js" "at-" "js" "\* [A-Z一-龥a-z][^*]*"
    fi

    echo "" >&2
    echo "💡 决策:" >&2
    echo "  - 现有组件能覆盖 → 删除本文件,改 Edit 调用方使用现成组件" >&2
    echo "  - 现有不够用 → 保留并在文件头注释 '复用检查: 已查 at_*, 未覆盖 XX 需求'" >&2
    echo "" >&2
fi

# ─── 输出汇总 ─────────────────────────────────────────────────────────────
if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo "" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "  ai_quality_check: ${#WARNINGS[@]} 处提示  ($TOOL → $FILE)" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    for W in "${WARNINGS[@]}"; do
        echo "" >&2
        echo "$W" >&2
    done
    echo "" >&2
fi

exit 0
