<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getQuotationDetail } from '@/api/projects'

const route = useRoute()
const router = useRouter()
const quotation = ref(null)
const loading = ref(true)

// 完全自定义手势 — touch-action: none + JS 接管 pan + pinch
// (浏览器原生 pinch 受 user-scalable=no 阻止, 必须自己实现)
const wrapRef = ref(null)
const iframeRef = ref(null)
const scale = ref(1)
const contentHeight = ref(800)
let lastDistance = 0
let lastScale = 1
let lastX = 0, lastY = 0

function dist(touches) {
  const dx = touches[0].clientX - touches[1].clientX
  const dy = touches[0].clientY - touches[1].clientY
  return Math.sqrt(dx * dx + dy * dy)
}

function _onTouchStart(e) {
  if (e.touches.length === 1) {
    lastX = e.touches[0].clientX
    lastY = e.touches[0].clientY
  } else if (e.touches.length === 2) {
    lastDistance = dist(e.touches)
    lastScale = scale.value
    e.preventDefault()
  }
}

function _onTouchMove(e) {
  const el = wrapRef.value
  if (!el) return
  if (e.touches.length === 1) {
    // 单指 pan — JS 控制 scrollLeft/Top
    const t = e.touches[0]
    const dx = t.clientX - lastX
    const dy = t.clientY - lastY
    el.scrollLeft -= dx
    el.scrollTop  -= dy
    lastX = t.clientX
    lastY = t.clientY
    e.preventDefault()
  } else if (e.touches.length === 2 && lastDistance > 0) {
    // 双指 pinch
    const d = dist(e.touches)
    const next = Math.max(0.5, Math.min(3, lastScale * (d / lastDistance)))
    scale.value = next
    e.preventDefault()
  }
}

function _onTouchEnd(e) {
  if (e.touches.length < 2) lastDistance = 0
  if (e.touches.length === 1) {
    // 双指松一指 → 切到 pan, 重置 anchor
    lastX = e.touches[0].clientX
    lastY = e.touches[0].clientY
  }
}

// 双击切换 1× / 2× (常见 doc preview 行为)
let lastTap = 0
function onClick(e) {
  const now = Date.now()
  if (now - lastTap < 300) {
    scale.value = scale.value > 1.2 ? 1 : 2
    e.preventDefault()
  }
  lastTap = now
}

// 显式注册 passive:false 的 touch listeners
function attachTouchHandlers() {
  const el = wrapRef.value
  if (!el) return
  el.addEventListener('touchstart', _onTouchStart, { passive: false })
  el.addEventListener('touchmove', _onTouchMove, { passive: false })
  el.addEventListener('touchend', _onTouchEnd, { passive: true })
  el.addEventListener('touchcancel', _onTouchEnd, { passive: true })
}
function detachTouchHandlers() {
  const el = wrapRef.value
  if (!el) return
  el.removeEventListener('touchstart', _onTouchStart)
  el.removeEventListener('touchmove', _onTouchMove)
  el.removeEventListener('touchend', _onTouchEnd)
  el.removeEventListener('touchcancel', _onTouchEnd)
}

// iframe 加载完后取真实内容高度, 让外层 sized wrapper 撑足
function onIframeLoad() {
  nextTick(() => {
    const iframe = iframeRef.value
    if (!iframe) return
    try {
      // 等下一帧让 layout 完成
      setTimeout(() => {
        const h = iframe.contentDocument?.body?.scrollHeight
              || iframe.contentDocument?.documentElement?.scrollHeight
              || 800
        if (h > 0) contentHeight.value = h
      }, 100)
    } catch {}
  })
}

onMounted(() => {
  load()
  nextTick(attachTouchHandlers)
})
onBeforeUnmount(detachTouchHandlers)

async function load() {
  try {
    const res = await getQuotationDetail(route.params.id)
    quotation.value = res.data.data
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

function fmt(n) {
  if (n == null) return ''
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function fmtDisc(d) {
  if (d == null || d === 1) return ''
  return Math.round(d * 100) + '%'
}
function esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
}

// 生成完整 HTML 放入 iframe srcdoc
// iframe 有自己的 viewport width=1100，浏览器等比例缩放，捏合缩放原生支持
const iframeHTML = computed(() => {
  const q = quotation.value
  if (!q) return ''
  const lh = q.letterhead || {}
  const ef = q.extra_fields || {}
  const details = q.details || []

  // 产品行
  let rowsHTML = ''
  let sn = 0
  for (const d of details) {
    if (d.row_type === 'section') {
      rowsHTML += `<tr><td class="nb"></td><td colspan="10" class="sec">${esc(d.section_label)}</td><td class="nb"></td></tr>`
    } else {
      sn++
      const desc = [
        d.product_name ? esc(d.product_name) : '',
        d.product_model ? `<span style="display:block;color:#475569">${esc(d.product_model)}</span>` : '',
        d.product_desc  ? `<span style="display:block;color:#64748b;font-size:11px">${esc(d.product_desc)}</span>` : '',
      ].join('')
      rowsHTML += `<tr>
        <td class="nb"></td>
        <td class="pv" style="text-align:center;color:#94a3b8;font-size:11px">${sn}</td>
        <td class="pv" style="font-size:11px;color:#475569">${esc(d.product_mn)}</td>
        <td class="pv">${esc(d.brand)}</td>
        <td class="pv">${desc}</td>
        <td class="pvr">${esc(fmtDisc(d.discount))}</td>
        <td class="pvr">${esc(fmt(d.market_price))}</td>
        <td class="pvr">${esc(fmt(d.unit_price))}</td>
        <td class="pvr">${esc(d.quantity)}${d.unit ? ' ' + esc(d.unit) : ''}</td>
        <td class="pvr" style="font-weight:600">${esc(fmt(d.total_price))}</td>
        <td class="pv" style="font-size:11px;color:#64748b">${esc(d.item_note)}</td>
        <td class="nb"></td>
      </tr>`
    }
  }

  // 合计
  const subtotal = details
    .filter(d => d.row_type !== 'section' && d.total_price != null)
    .reduce((s, d) => s + d.total_price, 0)
  const showTotal = q.amount != null && Math.abs(q.amount - subtotal) > 0.01

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1100, user-scalable=yes, minimum-scale=0.1, maximum-scale=10, viewport-fit=cover">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#cfd2d7;font-family:'Calibri',-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;font-size:12px;padding:12px}
.paper{background:#fff;box-shadow:0 4px 16px rgba(0,0,0,.15);padding:36px 50px 50px;width:1100px}
table.g{width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed}
table.g td{border:1px solid #b3b3b3;padding:4px 8px;vertical-align:middle;background:#fff;line-height:1.35;color:#000;word-wrap:break-word}
.nb{border:none!important;background:transparent!important;padding:2px 8px}
.cn{background:transparent!important;padding:0 4px!important;vertical-align:top!important;font-size:18px;font-weight:700;border:none!important}
.ci{background:transparent!important;padding:0 4px!important;vertical-align:top!important;font-size:11px;border:none!important}
.title{font-size:24px;font-weight:700;text-align:center;padding:10px 0!important;letter-spacing:1px;background:transparent!important;border:none!important}
.lbl{font-weight:700;background:#fafbfc}
.val{background:#fff;color:#1e293b}
.th{background:#f1f5f9;font-weight:700;text-align:center;padding:5px 4px;white-space:nowrap}
.pv{vertical-align:top}
.pvr{vertical-align:top;text-align:right}
.sec{background:#f8fafc!important;font-weight:700;color:#334155}
.tr td{background:#fafbfc}
.tl{font-weight:700;text-align:right}
.tv{font-weight:700;text-align:right}
.tf td{border-top:2px solid #000!important}
.sb{min-height:50px;background:#fff}
.sl{display:block;font-weight:600;font-size:12px;padding-bottom:2px;border-bottom:1px solid #666;min-width:160px}
</style>
</head>
<body>
<div class="paper">

<table class="g" style="margin-bottom:8px">
<colgroup><col style="width:130px"><col></colgroup>
<tbody>
<tr>
  <td class="nb" rowspan="3" style="vertical-align:top;padding:0 8px 0 0">
    ${lh.logo_url ? `<img src="${esc(lh.logo_url)}" style="width:116px;height:auto" onerror="this.style.display='none'">` : ''}
  </td>
  <td class="cn">${esc(lh.line1 || 'EVERTAC SOLUTIONS SINGAPORE PTE. LTD.')}</td>
</tr>
<tr><td class="ci">${esc(lh.line2 || '18 Boon Lay Way, #03-117 Tradehub 21, Singapore 609966')}</td></tr>
<tr><td class="ci">${esc(lh.line3 || 'UEN No/GST Reg. No.: 202230146C    Website: www.evertac-solutions.com')}</td></tr>
</tbody>
</table>

<div class="title">QUOTATION</div>

<table class="g">
<colgroup>
  <col style="width:26px"><col style="width:4%"><col style="width:13%"><col style="width:12%">
  <col><col style="width:7%"><col style="width:9%"><col style="width:9%"><col style="width:6%"><col style="width:11%">
  <col style="width:12%"><col style="width:28px">
</colgroup>
<tbody>
<tr><td class="nb"></td><td class="lbl" colspan="3">客户名称:</td><td class="val" colspan="3">${esc(q.customer?.name)}</td><td class="lbl" colspan="2">报价编号:</td><td class="val" colspan="2">${esc(q.quotation_number)}</td><td class="nb"></td></tr>
<tr><td class="nb"></td><td class="lbl" colspan="3">客户地址:</td><td class="val" colspan="3">${esc(ef.customer_address)}</td><td class="lbl" colspan="2">报价日期:</td><td class="val" colspan="2">${esc(ef.quotation_date || q.created_at)}</td><td class="nb"></td></tr>
<tr><td class="nb"></td><td class="lbl" colspan="3">联系人:</td><td class="val" colspan="3">${esc(q.contact?.name)}</td><td class="lbl" colspan="2">付款条件:</td><td class="val" colspan="2">${esc(ef.payment_terms)}</td><td class="nb"></td></tr>
<tr><td class="nb"></td><td class="lbl" colspan="3">联系电话:</td><td class="val" colspan="3">${esc(ef.contact_phone || q.contact?.phone)}</td><td class="lbl" colspan="2">交付条件:</td><td class="val" colspan="2">${esc(ef.shipping_terms)}</td><td class="nb"></td></tr>
<tr><td class="nb"></td><td class="lbl" colspan="3">项目名称:</td><td class="val" colspan="3">${esc(q.project?.name)}</td><td class="lbl" colspan="2">有效期:</td><td class="val" colspan="2">${esc(ef.validity)}</td><td class="nb"></td></tr>
<tr><td class="nb"></td><td class="lbl" colspan="3">货币:</td><td class="val" colspan="3">${esc(q.currency)}</td><td class="lbl" colspan="2">参考编号:</td><td class="val" colspan="2">${esc(ef.ref_no)}</td><td class="nb"></td></tr>
</tbody>
<tbody>
<tr><td class="nb"></td><td class="th">S/N</td><td class="th">产品编码</td><td class="th">品牌</td><td class="th">型号规格</td><td class="th">折扣%</td><td class="th">市场价</td><td class="th">单价</td><td class="th">数量</td><td class="th">小计</td><td class="th">备注</td><td class="nb"></td></tr>
</tbody>
<tbody>${rowsHTML}</tbody>
<tbody>
<tr class="tr"><td class="nb"></td><td colspan="4" style="border:none;background:transparent"></td><td class="tl" colspan="4">合计</td><td class="tv">${esc(fmt(subtotal))}</td><td class="val"></td><td class="nb"></td></tr>
${showTotal ? `<tr class="tr tf"><td class="nb"></td><td colspan="4" style="border:none;background:transparent"></td><td class="tl" colspan="4">总计 (${esc(q.currency)})</td><td class="tv" style="font-size:13px">${esc(fmt(q.amount))}</td><td class="val"></td><td class="nb"></td></tr>` : ''}
${q.notes ? `<tr><td class="nb"></td><td class="lbl" colspan="2" style="vertical-align:top">备注:</td><td colspan="8" style="vertical-align:top;white-space:pre-wrap">${esc(q.notes)}</td><td class="nb"></td></tr>` : ''}
</tbody>
</table>

<table class="g" style="margin-top:40px">
<colgroup>
  <col style="width:26px"><col style="width:4%"><col style="width:13%"><col style="width:12%">
  <col><col style="width:7%"><col style="width:9%"><col style="width:9%"><col style="width:6%"><col style="width:11%">
  <col style="width:12%"><col style="width:28px">
</colgroup>
<tbody>
<tr><td class="nb"></td><td class="sb" colspan="4"></td><td class="nb" style="font-weight:700;font-size:12px;padding-left:12px" colspan="5">Signed and Accepted by Customer:</td><td class="nb" colspan="1"></td><td class="nb"></td></tr>
<tr><td class="nb"></td><td class="sb" colspan="4">${q.signature?.url ? `<img src="${esc(q.signature.url)}" style="max-height:60px;max-width:100%" onerror="this.style.display='none'">` : ''}</td><td class="sb" colspan="5"></td><td class="nb" colspan="1"></td><td class="nb"></td></tr>
<tr><td class="nb"></td><td class="nb" colspan="4" style="padding-left:12px"><span class="sl">${esc(q.signature?.left)}</span></td><td class="nb" colspan="5" style="padding-left:12px;font-size:11px;font-style:italic"><span class="sl" style="font-weight:400">${esc(q.signature?.right)}</span></td><td class="nb" colspan="1"></td><td class="nb"></td></tr>
</tbody>
</table>

</div>
</body>
</html>`
})
</script>

<template>
  <!-- 顶部导航（在主 viewport 下渲染，尺寸正常） -->
  <div class="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-100 flex items-center gap-3 px-4"
       :style="{ paddingTop: 'env(safe-area-inset-top)', height: 'calc(44px + env(safe-area-inset-top))' }">
    <button @click="router.back()" class="p-1 -ml-1 text-gray-500">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M15 18l-6-6 6-6"/>
      </svg>
    </button>
    <span class="text-base font-semibold flex-1 truncate">
      {{ quotation?.quotation_number || '报价单' }}
    </span>
  </div>

  <!-- 加载中 -->
  <div v-if="loading" class="flex items-center justify-center"
       :style="{ paddingTop: 'calc(44px + env(safe-area-inset-top))', height: '100vh' }">
    <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"/>
  </div>

  <!-- 自定义 pinch-zoom: 外容器 overflow 滚动 + sized wrapper 撑出 scaled 区域 + iframe transform
       touch handlers 在 onMounted 用 addEventListener+passive:false 绑定(Vue @touchstart 在
       某些 iOS WebView 是 passive 默认, preventDefault 静默失败) -->
  <div v-else-if="quotation"
       ref="wrapRef"
       @click="onClick"
       :style="{
         position: 'fixed',
         top: 'calc(44px + env(safe-area-inset-top))',
         left: 0, right: 0, bottom: 0,
         overflow: 'auto',
         WebkitOverflowScrolling: 'touch',
         touchAction: 'none',
         background: '#cfd2d7',
       }">
    <!-- sized wrapper: 宽高 = 内容尺寸 × scale, 撑出 scrollable 区域 -->
    <div :style="{
      width: (1100 * scale) + 'px',
      height: (contentHeight * scale) + 'px',
      position: 'relative',
    }">
      <!-- pointer-events: none 让 touch 穿透到外层 wrapper(否则 iframe 自己捕获 touch
           导致 pinch 手势无法被父级检测). 副作用: 不能选/复制 iframe 内容, 但报价单
           是只读预览, 可接受. -->
      <iframe ref="iframeRef"
              :srcdoc="iframeHTML"
              scrolling="no"
              @load="onIframeLoad"
              :style="{
                border: 'none',
                display: 'block',
                width: '1100px',
                height: contentHeight + 'px',
                transform: `scale(${scale})`,
                transformOrigin: '0 0',
                transition: lastDistance === 0 ? 'transform 0.2s ease-out' : 'none',
                pointerEvents: 'none',
              }" />
    </div>
  </div>

  <!-- 失败 -->
  <div v-else class="flex flex-col items-center justify-center text-gray-400 gap-2"
       :style="{ paddingTop: 'calc(44px + env(safe-area-inset-top))', height: '100vh' }">
    <span>加载失败</span>
    <button @click="load" class="text-sm text-blue-500">重试</button>
  </div>
</template>
