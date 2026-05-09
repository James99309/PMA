<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getQuotationDetail } from '@/api/projects'

const route = useRoute()
const router = useRouter()
const quotation = ref(null)
const loading = ref(true)

// 进此页时临时允许 pinch-zoom (app 全局 viewport user-scalable=no 防表单自动放大,
// 但报价单需要双指缩放查看), 离开时恢复
let _origViewport = null
function setViewport(content) {
  const meta = document.querySelector('meta[name=viewport]')
  if (!meta) return
  if (_origViewport === null) _origViewport = meta.getAttribute('content')
  meta.setAttribute('content', content)
}
function restoreViewport() {
  const meta = document.querySelector('meta[name=viewport]')
  if (meta && _origViewport !== null) {
    meta.setAttribute('content', _origViewport)
    _origViewport = null
  }
}

onMounted(() => {
  setViewport('width=device-width, initial-scale=1.0, minimum-scale=0.5, maximum-scale=5, user-scalable=yes, viewport-fit=cover')
  load()
})
onBeforeUnmount(restoreViewport)

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

  <!-- iframe 承载报价单，有独立 viewport width=1100，等比例缩放 -->
  <iframe v-else-if="quotation"
          :srcdoc="iframeHTML"
          style="border:none; width:100%; display:block;"
          :style="{
            marginTop: 'calc(44px + env(safe-area-inset-top))',
            height: 'calc(100vh - 44px - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 60px)'
          }"
          scrolling="yes"
  />

  <!-- 失败 -->
  <div v-else class="flex flex-col items-center justify-center text-gray-400 gap-2"
       :style="{ paddingTop: 'calc(44px + env(safe-area-inset-top))', height: '100vh' }">
    <span>加载失败</span>
    <button @click="load" class="text-sm text-blue-500">重试</button>
  </div>
</template>
