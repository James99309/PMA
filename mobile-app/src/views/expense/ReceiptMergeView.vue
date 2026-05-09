<!--
  ReceiptMergeView · 多张发票合并为 1 行
  严格对齐 design_handoff/expense-receipt.jsx::ExReceiptMerge (L234-290)
  - hero: 合并科目 12 ink3 / 22 serif 科目名 / 38 serif 总额 / 11 ink3 N 张合计
  - SectionHeader 包含发票 + 行(36x26 mini + seller + date·#no + amount + ×)
  - SectionHeader 明细字段(汇总) + ExFieldRow x6
  - ExBottomBar 保存合并 / 拆分独立
-->
<template>
  <div
    class="relative h-full overflow-hidden"
    :style="{ background: 'var(--color-ex-bg)', color: 'var(--color-ex-ink)', fontFamily: 'var(--font-sans)' }"
  >
    <div class="status-pad" />
    <ExNav
      title="合并明细"
      :sub="`${included.length} 张${categoryLabel}发票合并为 1 行`"
      @back="$router.back()"
    />

    <div
      class="overflow-auto h-full no-scrollbar"
      :style="{ paddingTop: '102px', paddingBottom: '100px' }"
    >
      <!-- hero -->
      <div :style="{ padding: '14px 20px 6px' }">
        <div :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)', marginBottom: '6px' }">合并科目</div>
        <div :style="{ fontSize: '22px', fontWeight: 500, fontFamily: 'var(--font-serif)' }">{{ categoryLabel }}</div>
        <div
          :style="{
            fontSize: '38px', fontWeight: 500, fontFamily: 'var(--font-serif)',
            marginTop: '12px', lineHeight: 1,
          }"
        >{{ currencySymbol }} {{ formatAmount(totalAmount) }}</div>
        <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginTop: '6px' }">
          {{ included.length }} 张发票合计
        </div>
      </div>

      <!-- 包含发票 -->
      <ExSectionHeader>包含发票</ExSectionHeader>
      <div :style="{ background: 'var(--color-ex-card)' }">
        <div
          v-for="(r, i) in included"
          :key="r.idx"
          class="flex items-center"
          :style="{
            padding: '12px 20px',
            borderBottom: i < included.length - 1 ? '1px solid var(--color-ex-divider-soft)' : 'none',
            gap: '12px',
          }"
        >
          <div
            :style="{
              width: '36px', height: '26px', borderRadius: '3px',
              backgroundImage: r.dataUrl ? `url(${r.dataUrl})` : 'none',
              backgroundColor: '#F5EFE3', backgroundSize: 'cover',
              flexShrink: 0,
            }"
          />
          <div class="flex-1 min-w-0">
            <div :style="{ fontSize: '13px', fontWeight: 500 }">{{ r.fields?.seller || '未知商户' }}</div>
            <div
              :style="{
                fontSize: '10px', color: 'var(--color-ex-ink4)',
                marginTop: '2px', fontFamily: 'var(--font-mono)',
              }"
            >{{ r.fields?.date || '—' }} · #{{ r.fields?.invoice_no || '—' }}</div>
          </div>
          <div :style="{ fontSize: '14px', fontFamily: 'var(--font-serif)', fontWeight: 500 }">
            {{ currencySymbol }}{{ formatAmount(r.fields?.invoice_amount) }}
          </div>
          <div
            :style="{ fontSize: '16px', color: 'var(--color-ex-ink4)', fontWeight: 300 }"
            @click="onRemove(r.idx)"
          >×</div>
        </div>
      </div>

      <!-- 汇总字段 -->
      <ExSectionHeader>明细字段(汇总)</ExSectionHeader>
      <ExFieldRow label="报销科目 *" :value="categoryLabel" />
      <ExFieldRow label="时间范围" :value="dateRange" />
      <ExFieldRow label="费用描述" :value="form.description" />
      <ExFieldRow
        label="发票金额 *"
        :value="`${currencySymbol} ${formatAmount(totalAmount)}`"
        :lock="true"
        note="自动累加"
      />
      <ExFieldRow label="币种" :value="`${currencyLabel} (${currency})`" />
      <ExFieldRow label="单据数" :value="String(included.length)" />
    </div>

    <ExBottomBar
      primary="保存合并"
      secondary="拆分独立"
      :disabled="saving"
      @primary="onSaveMerge"
      @secondary="onSplit"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as expApi from '@/api/expense'
import { useExpenseStore } from '@/stores/expense'
import ExNav from '@/components/expense/ExNav.vue'
import ExSectionHeader from '@/components/expense/ExSectionHeader.vue'
import ExFieldRow from '@/components/expense/ExFieldRow.vue'
import ExBottomBar from '@/components/expense/ExBottomBar.vue'

const route = useRoute()
const router = useRouter()
const store = useExpenseStore()
const expenseId = computed(() => parseInt(route.params.id))
const primaryIdx = computed(() => parseInt(route.query.primary) || 0)
const saving = ref(false)

const primary = computed(() => store.pendingReceipts[primaryIdx.value])
const category = computed(() => primary.value?.fields?.category || 'other')
const currency = computed(() => primary.value?.fields?.currency || 'CNY')

const included = computed(() =>
  store.pendingReceipts.filter(r =>
    r.status === 'done' &&
    r.fields?.category === category.value &&
    r.fields?.currency === currency.value &&
    !r.saved && !r.skipped
  )
)

const totalAmount = computed(() =>
  included.value.reduce((s, r) => s + (Number(r.fields?.invoice_amount) || 0), 0))

const dateRange = computed(() => {
  const dates = included.value.map(r => r.fields?.date).filter(Boolean).sort()
  if (dates.length === 0) return '—'
  if (dates.length === 1) return dates[0]
  return `${dates[0]} — ${dates[dates.length - 1]}`
})

const form = ref({ description: '' })

const categoryLabel = computed(() => store.categoryLabel(category.value))
const currencySymbol = computed(() => store.currencySymbol(currency.value))
const currencyLabel = computed(() =>
  store.currencies.find(c => c.code === currency.value)?.label || currency.value)

function formatAmount(n) {
  return (Number(n) || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

onMounted(async () => {
  await store.loadReference()
  form.value.description = `${categoryLabel.value} · ${included.value.length} 次`
})

function onRemove(idx) {
  store.updatePendingReceipt(idx, { skipped: true })
}

async function onSaveMerge() {
  if (included.value.length === 0) {
    alert('没有可合并的发票')
    return
  }
  saving.value = true
  try {
    const payload = {
      expense_category: category.value,
      expense_date: included.value[0].fields?.date || new Date().toISOString().slice(0, 10),
      currency: currency.value,
      invoice_amount: totalAmount.value,
      description: form.value.description,
      document_count: included.value.length,
      invoice_images: included.value.map(r => ({
        filename: `invoice-${r.idx}.jpg`,
        url: r.file_url,
        invoice_no: r.fields?.invoice_no || '',
        seller: r.fields?.seller || '',
      })).filter(im => im.url),
    }
    await expApi.addLine(expenseId.value, payload)
    // 标记所有合并的票为已保存
    included.value.forEach(r => store.updatePendingReceipt(r.idx, { saved: true }))
    // 跳到下一张未处理的
    nextUnprocessed()
  } catch (e) {
    alert('保存失败: ' + (e.response?.data?.message || e.message))
  } finally {
    saving.value = false
  }
}

function onSplit() {
  // 回到 confirm, 把当前 receipt 当独立明细处理
  router.replace(`/expense/${expenseId.value}/confirm?idx=${primaryIdx.value}`)
}

function nextUnprocessed() {
  const idx = store.pendingReceipts.findIndex(r => !r.saved && !r.skipped && r.status !== 'failed')
  if (idx >= 0) {
    router.replace(`/expense/${expenseId.value}/confirm?idx=${idx}`)
  } else {
    store.clearPendingReceipts()
    router.replace(`/expense/${expenseId.value}/edit`)
  }
}
</script>
