#!/usr/bin/env node
// i18n 护栏 — 棘轮式:容忍现有中文债, 只拦"新增"硬编码中文字面量。
//
// 扫 src 下 .vue/.js/.ts(排除 src/locales/),含 CJK 的行计为一条;
// 与 scripts/i18n-baseline.json 比对:
//   - 出现 baseline 里没有的新条目 → 打印 + exit 1(挡 PR/OTA)
//   - baseline 里有、现在没了 → 提示"债已减少"(可 --update 收紧)
//
// 用法:
//   node scripts/i18n-guard.mjs           # 检查(默认, release-ota / CI 用)
//   node scripts/i18n-guard.mjs --update  # 把当前现状写成新 baseline(修完债后收紧)
//
// 规则见 CLAUDE-I18N.md「开发纪律」。中文应走 t() + en.js/zh.js;
// 后端数据值由后端按 _lang() 返回 *_label, 前端别再硬编码。
import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join, relative } from 'path'

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url))
const APP_DIR = join(SCRIPT_DIR, '..')
const SRC_DIR = join(APP_DIR, 'src')
// 用 .txt(仓库 .gitignore 全局忽略 *.json, baseline 必须进 git 供他人/CI 用)
const BASELINE = join(SCRIPT_DIR, 'i18n-baseline.txt')

const CJK = /[㐀-䶿一-鿿豈-﫿\u{20000}-\u{2a6df}]/u
const EXCLUDE_DIRS = new Set(['locales', 'node_modules', 'dist', '.git'])

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name)
    const st = statSync(p)
    if (st.isDirectory()) {
      if (EXCLUDE_DIRS.has(name)) continue
      walk(p, out)
    } else if (/\.(vue|js|ts)$/.test(name)) {
      out.push(p)
    }
  }
  return out
}

function collect() {
  const hits = new Map() // key -> {file, line, text}
  for (const f of walk(SRC_DIR)) {
    const rel = relative(APP_DIR, f)
    const lines = readFileSync(f, 'utf8').split('\n')
    lines.forEach((ln, i) => {
      if (CJK.test(ln)) {
        const text = ln.trim()
        const key = `${rel}\t${text}`
        if (!hits.has(key)) hits.set(key, { file: rel, line: i + 1, text })
      }
    })
  }
  return hits
}

const hits = collect()
const curKeys = [...hits.keys()].sort()

if (process.argv.includes('--update')) {
  writeFileSync(BASELINE, curKeys.join('\n') + '\n')
  console.log(`✅ i18n baseline 已更新: ${curKeys.length} 条现存中文字面量`)
  process.exit(0)
}

const baseline = existsSync(BASELINE)
  ? new Set(readFileSync(BASELINE, 'utf8').split('\n').filter(Boolean))
  : new Set()

const added = curKeys.filter(k => !baseline.has(k))
const resolved = [...baseline].filter(k => !hits.has(k)).length

if (added.length) {
  console.error(`\n❌ i18n 护栏: 发现 ${added.length} 处新增硬编码中文字面量(应走 t() / 后端 *_label):\n`)
  for (const k of added) {
    const h = hits.get(k)
    console.error(`  ${h.file}:${h.line}  ${h.text.slice(0, 100)}`)
  }
  console.error(`\n修法见 CLAUDE-I18N.md「开发纪律」。确属误报/已合规, 修完后跑:`)
  console.error(`  node scripts/i18n-guard.mjs --update\n`)
  process.exit(1)
}

console.log(
  `✅ i18n 护栏通过: 无新增中文字面量` +
  (resolved ? `(另: baseline 中 ${resolved} 条已清除, 可 --update 收紧)` : '')
)
