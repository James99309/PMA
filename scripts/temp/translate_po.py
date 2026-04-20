#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量翻译 messages.po 中空的 msgstr 条目（使用 Claude API）

用法:
    python3 scripts/temp/translate_po.py [--dry-run] [--batch-size 40]

会跳过:
    - 空 msgid（文件头部元数据块）
    - 已有 msgstr 的条目
    - 纯标点/数字的短 msgid（无意义翻译）
"""
import sys, os, re, json, argparse, time

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

ROOT = get_project_root()
PO_PATH = os.path.join(ROOT, 'app/translations/en/LC_MESSAGES/messages.po')


# ── .po 解析器 ────────────────────────────────────────────────────────────────

def parse_po(path):
    """返回条目列表，每条: {'msgid': str, 'msgstr': str, 'start': int, 'end': int, 'raw': str}"""
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = []
    i = 0
    while i < len(lines):
        # 跳过注释和空行，找 msgid
        if not lines[i].startswith('msgid '):
            i += 1
            continue
        start = i
        # 读取 msgid（可能多行）
        msgid_lines = [lines[i]]
        i += 1
        while i < len(lines) and lines[i].startswith('"'):
            msgid_lines.append(lines[i])
            i += 1
        # 读取 msgstr
        if i >= len(lines) or not lines[i].startswith('msgstr '):
            continue
        msgstr_lines = [lines[i]]
        i += 1
        while i < len(lines) and lines[i].startswith('"'):
            msgstr_lines.append(lines[i])
            i += 1
        end = i

        def decode_po_string(po_lines):
            result = ''
            for line in po_lines:
                line = line.strip()
                m = re.match(r'^(?:msgid|msgstr)\s+"(.*)"$', line)
                if m:
                    result += m.group(1)
                elif re.match(r'^"(.*)"$', line):
                    result += re.match(r'^"(.*)"$', line).group(1)
            return result.replace('\\n', '\n').replace('\\"', '"')

        msgid = decode_po_string(msgid_lines)
        msgstr = decode_po_string(msgstr_lines)
        entries.append({
            'msgid': msgid,
            'msgstr': msgstr,
            'start': start,
            'end': end,
        })
    return lines, entries


def should_skip(msgid):
    """不值得翻译的条目"""
    if not msgid:
        return True
    # 纯 ASCII（已经是英文）
    if msgid.isascii() and not any('\u4e00' <= c <= '\u9fff' for c in msgid):
        return True
    # 纯数字/标点
    stripped = re.sub(r'[\s\d\W]', '', msgid)
    if len(stripped) == 0:
        return True
    return False


# ── Claude API 翻译 ───────────────────────────────────────────────────────────

def translate_batch(items, client):
    """items: list of (msgid,). 返回 dict {msgid: translated}"""
    if not items:
        return {}

    numbered = '\n'.join(f'{i+1}. {item}' for i, item in enumerate(items))
    prompt = f"""You are a professional translator for a Chinese business management SaaS application (PMA).
Translate the following Chinese UI strings to natural English.

Rules:
- Output ONLY a JSON object mapping each number to its English translation
- Keep the same tone and brevity as the original
- Preserve any placeholders like %(name)s, %(count)d unchanged
- Preserve newlines (\\n) if present
- Don't add explanation, just the JSON

Chinese strings to translate:
{numbered}

JSON output:"""

    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=4096,
        messages=[{'role': 'user', 'content': prompt}]
    )
    text = response.content[0].text.strip()

    # 提取 JSON
    json_match = re.search(r'\{[\s\S]*\}', text)
    if not json_match:
        print(f"  ⚠️  无法解析响应: {text[:200]}")
        return {}
    try:
        result = json.loads(json_match.group())
        return {items[int(k)-1]: v for k, v in result.items() if k.isdigit() and int(k)-1 < len(items)}
    except Exception as e:
        print(f"  ⚠️  JSON 解析失败: {e}")
        return {}


# ── 写回 .po ─────────────────────────────────────────────────────────────────

def encode_po_string(s, keyword='msgstr'):
    """将字符串编码为 .po 格式"""
    s = s.replace('"', '\\"').replace('\n', '\\n')
    return f'{keyword} "{s}"\n'


def apply_translations(lines, entries, translations):
    """把翻译结果写回 lines 列表（原地修改）"""
    # 建立 start->entry 映射
    entry_map = {e['start']: e for e in entries}
    updated = 0
    for start, entry in entry_map.items():
        t = translations.get(entry['msgid'])
        if not t:
            continue
        # 找 msgstr 行的位置（在 start 到 end 之间）
        for j in range(start, entry['end']):
            if lines[j].startswith('msgstr '):
                # 替换 msgstr 及其后续 continuation lines
                new_line = encode_po_string(t, 'msgstr')
                # 删除原有的多行 msgstr continuation
                k = j + 1
                while k < entry['end'] and lines[k].startswith('"'):
                    lines[k] = None
                    k += 1
                lines[j] = new_line
                updated += 1
                break
    return updated


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='只统计，不调用 API')
    parser.add_argument('--batch-size', type=int, default=40, help='每批翻译条数')
    parser.add_argument('--limit', type=int, default=0, help='最多翻译N条（0=全部）')
    args = parser.parse_args()

    print(f"📂 解析 {PO_PATH}")
    lines, entries = parse_po(PO_PATH)

    # 找出需要翻译的条目
    to_translate = [
        e for e in entries
        if not e['msgstr'].strip() and not should_skip(e['msgid'])
    ]
    print(f"📊 总条目: {len(entries)} | 已翻译: {sum(1 for e in entries if e['msgstr'])} | 待翻译: {len(to_translate)}")

    if args.limit:
        to_translate = to_translate[:args.limit]
        print(f"🔧 限制翻译 {args.limit} 条")

    if args.dry_run:
        print("\n🔍 Dry-run 模式，以下是待翻译样本（前20条）:")
        for e in to_translate[:20]:
            print(f"  {repr(e['msgid'][:60])}")
        return

    # 调用 Claude API
    try:
        import anthropic
    except ImportError:
        print("❌ anthropic 包未安装，请运行: pip install anthropic")
        sys.exit(1)

    # 支持 .env.local 中的 OAuth proxy 配置
    env_local = os.path.join(ROOT, '.env.local')
    env_vars = {}
    for env_file in [os.path.join(ROOT, '.env'), env_local]:
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, _, v = line.partition('=')
                        env_vars[k.strip()] = v.strip()

    api_key = os.environ.get('ANTHROPIC_API_KEY') or env_vars.get('ANTHROPIC_API_KEY', 'dummy')
    base_url = os.environ.get('ANTHROPIC_BASE_URL') or env_vars.get('ANTHROPIC_BASE_URL')

    client_kwargs = {'api_key': api_key}
    if base_url:
        client_kwargs['base_url'] = base_url
        print(f"🔗 使用 OAuth proxy: {base_url}")

    client = anthropic.Anthropic(**client_kwargs)
    all_translations = {}
    batch_size = args.batch_size
    batches = [to_translate[i:i+batch_size] for i in range(0, len(to_translate), batch_size)]

    print(f"\n🚀 开始翻译 {len(to_translate)} 条，共 {len(batches)} 批...")
    for idx, batch in enumerate(batches):
        msgids = [e['msgid'] for e in batch]
        print(f"  批次 {idx+1}/{len(batches)} ({len(msgids)} 条)...", end=' ', flush=True)
        try:
            result = translate_batch(msgids, client)
            all_translations.update(result)
            print(f"✅ {len(result)} 条成功")
        except Exception as e:
            print(f"❌ {e}")
        if idx < len(batches) - 1:
            time.sleep(0.5)

    # 写回
    updated = apply_translations(lines, entries, all_translations)
    clean_lines = [l for l in lines if l is not None]
    with open(PO_PATH, 'w', encoding='utf-8') as f:
        f.writelines(clean_lines)

    print(f"\n✅ 写回完成，更新 {updated} 条")
    print("🔧 运行编译: pybabel compile -d app/translations")


if __name__ == '__main__':
    main()
