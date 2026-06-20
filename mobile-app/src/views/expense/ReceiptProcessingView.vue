<!--
  ReceiptProcessingView · OCR 识别中
  严格对齐 design_handoff/expense-receipt.jsx::ExReceiptProcessing (L116-164)
  - 顶部 ExNav: 识别中 / N 张发票 · AI 正在提取字段
  - 中部:三张叠票 220x156 + 扫描线 (accent 颜色 1.6s 动画)
  - 标题 22/500 serif: 正在识别 N 张发票
  - 副标题 13 ink3: 通常需要 3-5 秒
  - 字段揭示列表(animated stagger 250ms): 开票方/开票日期/价税合计/推荐科目(warn)
-->
<template>
  <div
    class="relative h-full overflow-hidden"
    :style="{ background: 'var(--color-ex-bg)', color: 'var(--color-ex-ink)', fontFamily: 'var(--font-sans)' }"
  >
    <div class="status-pad" />
    <ExNav
      :title="t('receiptScan.processing.navTitle')"
      :sub="t('receiptScan.processing.navSub', { n: receiptCount })"
      :back="false"
    />

    <div :style="{ paddingTop: '102px', height: '100%' }">
      <OcrProcessingAnimation
        :card-count="3"
        :title="t('receiptScan.processing.title', { n: receiptCount })"
        :subtitle="t('receiptScan.processing.subtitle', { min: Math.max(3, receiptCount * 3), max: receiptCount * 5 })"
        :fields="revealedFields"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { uploadInvoice, groupInvoices } from '@/api/expense'
import { useExpenseStore } from '@/stores/expense'
import ExNav from '@/components/expense/ExNav.vue'
import OcrProcessingAnimation from '@/components/common/OcrProcessingAnimation.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const store = useExpenseStore()
const expenseId = computed(() => parseInt(route.params.id))

const receiptCount = computed(() => store.pendingReceipts.length)

// 占位字段(动画用), 实际 OCR 完成后跳页; 跟随 locale
const revealedFields = computed(() => [
  { label: t('receiptScan.processing.pSeller'), val: t('receiptScan.processing.recognizing'), confident: true },
  { label: t('receiptScan.processing.pDate'), val: t('receiptScan.processing.recognizing'), confident: true },
  { label: t('receiptScan.processing.pTotal'), val: t('receiptScan.processing.recognizing'), confident: true },
  { label: t('receiptScan.processing.pCategory'), val: t('receiptScan.processing.recognizing'), confident: false },
])

onMounted(async () => {
  // 顺序上传所有发票, 取得 OCR 结果
  if (store.pendingReceipts.length === 0) {
    router.replace(`/expense/${expenseId.value}/edit`)
    return
  }

  for (let i = 0; i < store.pendingReceipts.length; i++) {
    const r = store.pendingReceipts[i]
    if (r.status === 'done' || r.status === 'failed') continue
    store.updatePendingReceipt(i, { status: 'ocr' })
    try {
      // 根据 blob.type 决定 filename 后缀, 让后端正确判断 PDF/图片
      const mime = r.blob.type || 'image/jpeg'
      const ext = mime === 'application/pdf' ? 'pdf'
                : mime.startsWith('image/') ? mime.split('/')[1].replace('jpeg', 'jpg')
                : 'jpg'
      const filename = r.filename || `invoice-${i}.${ext}`
      const file = new File([r.blob], filename, { type: mime })
      const resp = await uploadInvoice(file)
      if (resp.data?.success && resp.data.data?.fields) {
        store.updatePendingReceipt(i, {
          file_url: resp.data.data.file_url,
          fields: resp.data.data.fields,
          confidence: resp.data.data.fields?.confidence || {},
          status: 'done',
        })
      } else {
        store.updatePendingReceipt(i, {
          status: 'failed',
          error: resp.data?.message || t('receiptScan.processing.failed'),
        })
      }
    } catch (e) {
      store.updatePendingReceipt(i, {
        status: 'failed',
        error: e.response?.data?.message || e.message,
      })
    }
  }

  // grouping via shared backend logic (same as web): tag each receipt with groupKey for confirm/merge pages
  try {
    let defCcy = 'CNY'
    try {
      const d = await store.fetchDetail(expenseId.value, false)
      if (d?.currency) defCcy = d.currency
    } catch {}
    const items = store.pendingReceipts.map(r => r.fields || {})
    const resp = await groupInvoices(items, defCcy)
    const groups = resp?.data?.data?.groups || []
    groups.forEach(g => (g.indices || []).forEach(i => {
      store.updatePendingReceipt(i, { groupKey: g.key })
    }))
  } catch (e) {
    console.warn('[expense] groupInvoices failed, fallback to per-receipt', e?.message)
  }

  // 全部处理完 → 跳确认页
  setTimeout(() => {
    router.replace(`/expense/${expenseId.value}/confirm?idx=0`)
  }, 600)
})
</script>
