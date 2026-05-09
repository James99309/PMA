<!--
  ReceiptCaptureView · 拍发票 - 复用 DocumentScanFlow 公用组件
  与 CardScanCaptureView 完全同款方法 (VisionKit 优先 + Camera fallback + 4 角裁剪 + 预览)
  本视图只负责: 接收 done 事件 → 把页加入 pendingReceipts → 跳到 OCR 识别页
-->
<template>
  <DocumentScanFlow
    :allow-multi="true"
    capture-tip="把发票放在桌面平整位置, 设备保持稳定 1-2 秒等聚焦, 系统会自动捕捉并校正纸面"
    preview-tip="看清楚发票字段"
    primary-label="AI 识别"
    multi-primary-format="用这张 · 共 {n} 张 · 开始识别"
    @done="onDone"
    @cancel="$router.back()"
  />
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useExpenseStore } from '@/stores/expense'
import DocumentScanFlow from '@/components/common/DocumentScanFlow.vue'

const route = useRoute()
const router = useRouter()
const store = useExpenseStore()
const expenseId = parseInt(route.params.id)

function onDone(pages) {
  if (!pages || pages.length === 0) {
    router.back()
    return
  }
  // 重置队列(每次拍发票 = 新一批)
  if (store.currentReceiptExpenseId !== expenseId) {
    store.clearPendingReceipts()
    store.currentReceiptExpenseId = expenseId
  }
  for (const p of pages) {
    store.addPendingReceipt({ dataUrl: p.dataUrl, blob: p.blob })
  }
  router.replace(`/expense/${expenseId}/processing`)
}
</script>
