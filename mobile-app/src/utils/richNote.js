// 富文本便签渲染/清洗 —— 与 web at-rich-note 同口径(内容存 HTML;旧纯文本/Markdown 兼容)。
// 用于:日报正文 / 工作项描述 的「显示」与「编辑器初始化」。无第三方库。

const ALLOWED_TAGS = new Set([
  'B', 'I', 'U', 'EM', 'STRONG', 'A', 'BR', 'P', 'DIV', 'SPAN', 'IMG',
  'UL', 'OL', 'LI', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
])
const ALLOWED_ATTR = {
  A: ['href', 'target', 'rel'],
  IMG: ['src', 'alt'],
  SPAN: ['class', 'style', 'contenteditable'],
  DIV: ['style'],
}

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]))
}

function looksHtml(s) {
  return /<(img|div|br|span|p|b|i|a|ul|ol|li|h[1-6]|strong|em)[\s>/]/i.test(s || '')
}

// 仅保留白名单中的 style 子属性(尺寸/对象适配),其余丢弃
function safeStyle(style) {
  const out = []
  String(style || '').split(';').forEach(decl => {
    const [k, v] = decl.split(':')
    if (!k || !v) return
    const key = k.trim().toLowerCase()
    if (['width', 'height', 'max-width', 'object-fit', 'display', 'resize',
         'overflow', 'border-radius', 'vertical-align', 'line-height'].includes(key)) {
      if (!/url\s*\(|expression|javascript:/i.test(v)) out.push(`${key}:${v.trim()}`)
    }
  })
  return out.join(';')
}

function sanitizeNode(node) {
  const kids = Array.from(node.childNodes)
  for (const child of kids) {
    if (child.nodeType === 1) { // element
      const tag = child.tagName
      if (!ALLOWED_TAGS.has(tag)) { child.replaceWith(...child.childNodes); continue }
      const allowed = ALLOWED_ATTR[tag] || []
      Array.from(child.attributes).forEach(a => {
        const name = a.name.toLowerCase()
        if (name === 'class' && tag === 'SPAN') return            // 允许 arn-img class
        if (name === 'contenteditable') return
        if (name === 'style') { const s = safeStyle(a.value); if (s) child.setAttribute('style', s); else child.removeAttribute('style'); return }
        if (!allowed.includes(name)) { child.removeAttribute(a.name); return }
        if ((name === 'href' || name === 'src') && /^\s*javascript:/i.test(a.value)) child.removeAttribute(a.name)
      })
      if (tag === 'A') { child.setAttribute('target', '_blank'); child.setAttribute('rel', 'noopener') }
      sanitizeNode(child)
    } else if (child.nodeType !== 3) {
      child.remove() // 注释等
    }
  }
  return node
}

export function sanitizeRich(html) {
  try {
    const doc = new DOMParser().parseFromString(`<div>${html || ''}</div>`, 'text/html')
    const root = doc.body.firstChild
    sanitizeNode(root)
    return root.innerHTML
  } catch (e) {
    return esc(html)
  }
}

// 纯文本/Markdown 子集 → HTML
function mdToHtml(text) {
  let s = esc(text)
  s = s.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g,
    (_m, alt, url) => `<span class="arn-img"><img src="${url}" alt="${esc(alt)}"></span>`)
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g,
    (_m, txt, url) => `<a href="${url}" target="_blank" rel="noopener">${txt}</a>`)
  return s.replace(/\n/g, '<br>')
}

// 显示/编辑器初始化用:任意内容 → 安全 HTML
export function renderRich(text) {
  if (!text) return ''
  return looksHtml(text) ? sanitizeRich(text) : mdToHtml(text)
}

// 判空(去标签后无文字且无图片)
export function isRichEmpty(html) {
  if (!html) return true
  if (/<img\b/i.test(html)) return false
  return !String(html).replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').trim()
}
