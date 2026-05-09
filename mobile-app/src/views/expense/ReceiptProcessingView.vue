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

    <div
      class="flex flex-col items-center"
      :style="{ paddingTop: '102px', height: '100%' }"
    >
      <!-- 叠票 + 扫描线 -->
      <div :style="{ width: '220px', height: '156px', position: 'relative', marginTop: '8px', marginBottom: '28px' }">
        <div
          :style="{
            position: 'absolute', inset: 0, background: '#F5EFE3',
            transform: 'rotate(-2deg)',
            boxShadow: '0 18px 30px rgba(0,0,0,.18)',
          }"
        />
        <div
          :style="{
            position: 'absolute', inset: 0, background: '#F5EFE3',
            transform: 'translate(8px, 6px) rotate(2deg)',
            boxShadow: '0 18px 30px rgba(0,0,0,.18)',
          }"
        />
        <div
          class="ex-scan-line"
          :style="{
            position: 'absolute', left: '-10px', right: '-10px',
            height: '2px', background: 'var(--color-ex-accent)',
            boxShadow: '0 0 10px var(--color-ex-accent), 0 0 20px var(--color-ex-accent)',
          }"
        />
      </div>

      <div
        :style="{
          fontSize: '22px', fontWeight: 500, fontFamily: 'var(--font-serif)',
          color: 'var(--color-ex-ink)', textAlign: 'center',
        }"
      >正在识别 {{ receiptCount }} 张发票</div>
      <div
        :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)', marginTop: '6px', textAlign: 'center' }"
      >通常需要 {{ Math.max(3, receiptCount * 3) }}-{{ receiptCount * 5 }} 秒</div>

      <!-- 字段揭示 -->
      <div :style="{ marginTop: '32px', width: '280px' }">
        <div
          v-for="(f, i) in revealedFields"
          :key="i"
          class="flex justify-between"
          :style="{
            padding: '10px 0',
            borderBottom: i < revealedFields.length - 1 ? '1px solid var(--color-ex-divider)' : 'none',
            opacity: visibleCount > i ? (0.4 + Math.min(visibleCount - i, 3) * 0.2) : 0,
            transform: visibleCount > i ? 'translateY(0)' : 'translateY(8px)',
            transition: 'opacity 250ms ease-out, transform 250ms ease-out',
          }"
        >
          <span :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)' }">{{ f.label }}</span>
          <span
            :style="{
              fontSize: '13px',
              color: f.confident ? 'var(--color-ex-ink)' : 'var(--color-ex-warn)',
              fontWeight: 500,
            }"
          >{{ f.val }}{{ !f.confident ? ' (置信度低)' : '' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { uploadInvoice } from '@/api/expense'
import { useExpenseStore } from '@/stores/expense'
import ExNav from '@/components/expense/ExNav.vue'

const route = useRoute()
const router = useRouter()
const store = useExpenseStore()
const expenseId = computed(() => parseInt(route.params.id))

const receiptCount = computed(() => store.pendingReceipts.length)
const visibleCount = ref(0)
let revealTimer = null

// 占位字段(动画用), 实际 OCR 完成后跳页
const revealedFields = [
  { label: '开票方', val: '识别中...', confident: true },
  { label: '开票日期', val: '识别中...', confident: true },
  { label: '价税合计', val: '识别中...', confident: true },
  { label: '推荐科目', val: '识别中...', confident: false },
]

onMounted(async () => {
  // 字段揭示动画
  revealTimer = setInterval(() => {
    if (visibleCount.value < revealedFields.length) {
      visibleCount.value += 1
    } else {
      clearInterval(revealTimer)
      revealTimer = null
    }
  }, 250)

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

onUnmounted(() => {
  if (revealTimer) clearInterval(revealTimer)
})
</script>

<style scoped>
@keyframes ex-scan {
  0%   { top: 4px; opacity: 0.6; }
  50%  { top: 50%; opacity: 1; }
  100% { top: calc(100% - 4px); opacity: 0.6; }
}
.ex-scan-line {
  animation: ex-scan 1.6s ease-in-out infinite;
}
</style>
