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
      title="识别中"
      :sub="`${receiptCount} 张发票 · AI 正在提取字段`"
      :back="false"
    />

    <div :style="{ paddingTop: '102px', height: '100%' }">
      <OcrProcessingAnimation
        :card-count="3"
        :title="`正在识别 ${receiptCount} 张发票`"
        :subtitle="`通常需要 ${Math.max(3, receiptCount * 3)}-${receiptCount * 5} 秒`"
        :fields="revealedFields"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { uploadInvoice } from '@/api/expense'
import { useExpenseStore } from '@/stores/expense'
import ExNav from '@/components/expense/ExNav.vue'
import OcrProcessingAnimation from '@/components/common/OcrProcessingAnimation.vue'

const route = useRoute()
const router = useRouter()
const store = useExpenseStore()
const expenseId = computed(() => parseInt(route.params.id))

const receiptCount = computed(() => store.pendingReceipts.length)

// 占位字段(动画用), 实际 OCR 完成后跳页
const revealedFields = [
  { label: '开票方', val: '识别中...', confident: true },
  { label: '开票日期', val: '识别中...', confident: true },
  { label: '价税合计', val: '识别中...', confident: true },
  { label: '推荐科目', val: '识别中...', confident: false },
]

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
      const file = new File([r.blob], `invoice-${i}.jpg`, { type: r.blob.type || 'image/jpeg' })
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
          error: resp.data?.message || '识别失败',
        })
      }
    } catch (e) {
      store.updatePendingReceipt(i, {
        status: 'failed',
        error: e.response?.data?.message || e.message,
      })
    }
  }

  // 全部处理完 → 跳确认页
  setTimeout(() => {
    router.replace(`/expense/${expenseId.value}/confirm?idx=0`)
  }, 600)
})
</script>
