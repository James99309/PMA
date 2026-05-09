<!--
  ReceiptConfirmView · 核对单张发票字段
  严格对齐 design_handoff/expense-receipt.jsx::ExReceiptConfirm (L167-231)
  - ExNav 核对发票 N/M · 检查字段后保存 + 下一张›
  - 顶部缩略 92x64 + 类型/编号/字段置信度
  - 字段表单(用 ExFieldRow): 报销科目* / 发生日期* / 描述 / 金额* / 币种 / 汇率(lock)
                          / 报销金额(lock 自动计算) / 开票方 / 税额
  - 合并模式 picker: 独立明细 / 合并到现有
  - 底部 ExBottomBar: 保存这张 · 下一张 / 跳过
-->
<template>
  <div class="flex flex-col h-full" style="background: #F7F5F2;">

    <!-- Header — 返回 + 标题 + 上一张/下一张(纯导航,不影响保存状态) -->
    <div class="flex items-center justify-between px-5 py-2.5 shrink-0">
      <button @click="$router.back()"
        class="flex items-center gap-1 active:opacity-60 py-1 pr-2"
        style="color: var(--color-ink-2);">
        <svg width="9" height="14" viewBox="0 0 9 14">
          <path d="M7 1L1 7l6 6" fill="none" stroke="currentColor"
            stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <span class="text-[15px]">
          核对 {{ idx + 1 }}/{{ total }}<span v-if="processedCount > 0"
            class="text-[11px]" style="color: var(--color-ink-3); margin-left: 4px;">· 已处理 {{ processedCount }}</span>
        </span>
      </button>
      <div class="flex items-center" style="gap: 4px;">
        <button v-if="idx > 0"
          @click="navTo(idx - 1)"
          class="text-[14px] font-medium active:opacity-60 px-2"
          style="color: var(--color-accent);">‹ 上一张</button>
        <button v-if="idx < total - 1"
          @click="navTo(idx + 1)"
          class="text-[14px] font-medium active:opacity-60 px-2"
          style="color: var(--color-accent);">下一张 ›</button>
      </div>
    </div>

    <!-- 主滚动区(整页可滚动, 包括缩略图和字段表单) -->
    <div class="flex-1 overflow-y-auto no-scrollbar" style="padding-bottom: 100px;">
      <!-- 缩略 + 元信息 (点击放大查看原图) -->
      <div class="flex items-start" :style="{ padding: '12px 20px 16px', gap: '12px' }">
        <div
          @click="receipt?.dataUrl && (showFullImage = true)"
          :style="{
            width: '92px', height: '64px', borderRadius: '4px',
            backgroundImage: receipt?.dataUrl ? `url(${receipt.dataUrl})` : 'none',
            backgroundColor: '#F5EFE3', backgroundSize: 'cover', backgroundPosition: 'center',
            flexShrink: 0,
            cursor: 'pointer',
            position: 'relative',
          }"
        >
          <!-- 放大镜角标 -->
          <div v-if="receipt?.dataUrl"
            :style="{
              position: 'absolute', bottom: '-4px', right: '-4px',
              width: '20px', height: '20px', borderRadius: '10px',
              background: 'var(--color-ink)', color: '#fff',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '10px', fontWeight: 600,
              boxShadow: '0 1px 4px rgba(0,0,0,.25)',
            }"
          >⤢</div>
        </div>
        <div class="flex-1">
          <div :style="{ fontSize: '14px', fontWeight: 600, color: 'var(--color-ex-ink)' }">
            {{ docTypeLabel }}
          </div>
          <div
            v-if="form.invoice_no"
            :style="{
              fontSize: '11px', color: 'var(--color-ex-ink4)',
              marginTop: '4px', fontFamily: 'var(--font-mono)', letterSpacing: '0.4px',
            }"
          >{{ form.invoice_no }}</div>
          <div class="inline-flex items-center" :style="{ marginTop: '8px', gap: '6px' }">
            <span
              :style="{
                width: '8px', height: '8px', borderRadius: '4px',
                background: confidenceLabel.color,
              }"
            />
            <span :style="{ fontSize: '11px', color: confidenceLabel.color }">
              {{ confidenceLabel.text }}
            </span>
          </div>
          <div v-if="receipt?.dataUrl"
            class="text-[11px] mt-1.5 active:opacity-60"
            style="color: var(--color-accent);"
            @click="showFullImage = true">
            点击放大查看 ›
          </div>
        </div>
      </div>

      <!-- 字段表单 -->
      <ExSectionHeader>字段</ExSectionHeader>
      <ExFieldRow
        label="报销科目 *"
        :value="categoryLabel(form.expense_category)"
        :warn="lowConfidence('category')"
        :note="lowConfidence('category') ? `置信度 ${pct('category')}% · 请确认` : ''"
        @click="onPickCategory"
      />
      <ExFieldRow
        label="发生日期 *"
        :value="form.expense_date || '—'"
        :warn="lowConfidence('date')"
        :note="lowConfidence('date') ? `置信度 ${pct('date')}% · 请确认` : ''"
      />
      <ExFieldRow
        label="费用描述"
        :value="form.description || '—'"
        :warn="lowConfidence('description')"
      />
      <ExFieldRow
        label="发票金额 *"
        :value="`${currencySymbol(form.currency)} ${formatAmount(form.invoice_amount)}`"
        :warn="lowConfidence('invoice_amount')"
        :note="lowConfidence('invoice_amount') ? '请核对金额' : ''"
      />
      <ExFieldRow
        label="币种"
        :value="`${currencyLabel(form.currency)} (${form.currency})`"
      />
      <ExFieldRow
        label="汇率"
        :value="(form.exchange_rate || 1).toFixed(4)"
        :lock="true"
      />
      <ExFieldRow
        label="报销金额"
        :value="`${currencySymbol(expenseCurrency)} ${formatAmount(currentAmount)}`"
        :lock="true"
        note="自动计算 = 发票 × 汇率"
      />
      <ExFieldRow
        label="开票方"
        :value="form.seller || '—'"
        :warn="lowConfidence('seller')"
      />
      <ExFieldRow
        label="税额"
        :value="form.tax_amount ? `${currencySymbol(form.currency)} ${formatAmount(form.tax_amount)}` : '—'"
      />

      <!-- 合并模式 -->
      <ExSectionHeader v-if="mergeable.length > 0">合并模式</ExSectionHeader>
      <div
        v-if="mergeable.length > 0"
        :style="{
          background: 'var(--color-ex-card)',
          padding: '12px 20px',
          borderTop: '1px solid var(--color-ex-divider-soft)',
          borderBottom: '1px solid var(--color-ex-divider-soft)',
        }"
      >
        <div class="flex" :style="{ gap: '10px', marginBottom: '10px' }">
          <div
            class="flex-1"
            :style="{
              padding: '10px',
              border: mergeMode === 'separate' ? '1.5px solid var(--color-ex-ink)' : '1px solid var(--color-ex-divider)',
              borderRadius: '8px',
              background: mergeMode === 'separate' ? 'var(--color-ex-divider-soft)' : 'var(--color-ex-card)',
            }"
            @click="mergeMode = 'separate'"
          >
            <div :style="{ fontSize: '12px', fontWeight: 600 }">独立明细</div>
            <div :style="{ fontSize: '10px', color: 'var(--color-ex-ink3)', marginTop: '2px' }">每张一行</div>
          </div>
          <div
            class="flex-1"
            :style="{
              padding: '10px',
              border: mergeMode === 'merge' ? '1.5px solid var(--color-ex-ink)' : '1px solid var(--color-ex-divider)',
              borderRadius: '8px',
              background: mergeMode === 'merge' ? 'var(--color-ex-divider-soft)' : 'var(--color-ex-card)',
            }"
            @click="mergeMode = 'merge'"
          >
            <div :style="{ fontSize: '12px', fontWeight: 600 }">
              合并到现有 ({{ mergeable.length + 1 }} 张)
            </div>
            <div :style="{ fontSize: '10px', color: 'var(--color-ex-ink3)', marginTop: '2px' }">
              多张并 1 行 · 自动累加
            </div>
          </div>
        </div>
      </div>
    </div>

    <ExBottomBar
      :primary="isLastUnprocessed ? '保存全部' : '保存这张 · 下一张'"
      secondary="跳过"
      :disabled="saving"
      @primary="onSave"
      @secondary="onSkip"
    />

    <!-- 报销科目选择 -->
    <ExPickerSheet
      v-model="categoryPickerOpen"
      title="选择报销科目"
      :options="store.categories.map(c => ({ value: c.key, label: c.label }))"
      :selected="form.expense_category"
      @pick="(v) => { form.expense_category = v; categoryPickerOpen = false }"
    />

    <!-- 全屏图片预览 (核对原图清晰度) -->
    <Teleport to="body">
      <div v-if="showFullImage && receipt?.dataUrl"
        class="fixed inset-0 z-50 flex items-center justify-center"
        style="background: rgba(0,0,0,0.92);"
        @click="showFullImage = false">
        <img :src="receipt.dataUrl"
          class="block"
          style="max-width: 100%; max-height: 100%; object-fit: contain;"
          @click.stop />
        <button @click="showFullImage = false"
          class="absolute flex items-center justify-center rounded-full active:opacity-70"
          style="
            top: calc(env(safe-area-inset-top) + 12px);
            right: 16px;
            width: 36px; height: 36px;
            background: rgba(255,255,255,0.16);
            color: #fff; font-size: 18px;
          ">×</button>
        <div class="absolute text-white text-[12px] opacity-70"
          style="bottom: calc(env(safe-area-inset-bottom) + 16px);">
          点击空白区关闭
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as expApi from '@/api/expense'
import { useExpenseStore } from '@/stores/expense'
import ExSectionHeader from '@/components/expense/ExSectionHeader.vue'
import ExFieldRow from '@/components/expense/ExFieldRow.vue'
import ExBottomBar from '@/components/expense/ExBottomBar.vue'
import ExPickerSheet from '@/components/expense/ExPickerSheet.vue'

const route = useRoute()
const router = useRouter()
const store = useExpenseStore()

const expenseId = computed(() => parseInt(route.params.id))
const idx = computed(() => parseInt(route.query.idx) || 0)
const total = computed(() => store.pendingReceipts.length)
const receipt = computed(() => store.pendingReceipts[idx.value])
// 已处理数 = saved + skipped (用于显示 + 决定底部主按钮文案)
const processedCount = computed(() =>
  store.pendingReceipts.filter(r => r.saved || r.skipped).length
)
// 是否所有(其他)receipt 都已处理 — 此时按钮变"保存全部"
const isLastUnprocessed = computed(() =>
  store.pendingReceipts.filter((r, i) => i !== idx.value && !r.saved && !r.skipped).length === 0
)

const expenseCurrency = ref('CNY')
const saving = ref(false)
const mergeMode = ref('separate')
const categoryPickerOpen = ref(false)
const showFullImage = ref(false)

const form = ref({
  seller: '',
  invoice_no: '',
  expense_date: new Date().toISOString().slice(0, 10),
  currency: 'CNY',
  invoice_amount: 0,
  tax_amount: null,
  expense_category: 'other',
  description: '',
  exchange_rate: 1,
})

watch(idx, () => loadFromReceipt(), { immediate: false })

onMounted(async () => {
  await store.loadReference()
  await loadExpenseCurrency()
  loadFromReceipt()
})

async function loadExpenseCurrency() {
  try {
    // 只需要 currency 字段, 用 cache 即可; force=true 会跟保存后的 fetch 形成竞态
    const d = await store.fetchDetail(expenseId.value, false)
    if (d?.currency) expenseCurrency.value = d.currency
  } catch {}
}

function loadFromReceipt() {
  const r = store.pendingReceipts[idx.value]
  if (!r) return
  if (r.status === 'failed') {
    alert('这张发票识别失败: ' + (r.error || '未知错误') + ', 你可以手动填写或跳过')
  }
  const f = r.fields || {}
  form.value = {
    seller: f.seller || '',
    invoice_no: f.invoice_no || '',
    expense_date: normalizeDate(f.date) || new Date().toISOString().slice(0, 10),
    currency: f.currency || expenseCurrency.value || 'CNY',
    invoice_amount: Number(f.invoice_amount) || 0,
    tax_amount: f.tax_amount ? Number(f.tax_amount) : null,
    expense_category: f.category || 'other',
    description: f.description || (f.seller ? `${f.seller}发票` : ''),
    exchange_rate: 1,
  }
  fetchRate()
}

function normalizeDate(s) {
  if (!s) return ''
  const m = String(s).match(/(\d{4})[-/](\d{1,2})[-/](\d{1,2})/)
  if (!m) return ''
  return `${m[1]}-${m[2].padStart(2, '0')}-${m[3].padStart(2, '0')}`
}

async function fetchRate() {
  if (form.value.currency === expenseCurrency.value) {
    form.value.exchange_rate = 1
    return
  }
  try {
    const r = await expApi.getExchangeRate(form.value.currency, expenseCurrency.value)
    form.value.exchange_rate = Number(r.data?.data?.rate) || 1
  } catch {
    form.value.exchange_rate = 1
  }
}

const currentAmount = computed(() => (form.value.invoice_amount || 0) * (form.value.exchange_rate || 1))

const mergeable = computed(() => {
  // 当前及之前的同 category + 同 currency 的 receipts
  const cur = receipt.value
  if (!cur) return []
  return store.pendingReceipts
    .filter((r, i) => i !== idx.value && r.status === 'done' &&
      r.fields?.category === form.value.expense_category &&
      r.fields?.currency === form.value.currency)
})

function pct(key) {
  return Math.round(((receipt.value?.confidence || {})[key] || 0) * 100)
}
function lowConfidence(key) {
  const c = (receipt.value?.confidence || {})[key]
  return c !== undefined && c < 0.85
}

const docTypeLabel = computed(() =>
  form.value.invoice_no ? '增值税普通发票' : '收据 / 通用发票'
)

const confidenceLabel = computed(() => {
  const conf = receipt.value?.confidence || {}
  const total = Object.keys(conf).length || 1
  const high = Object.values(conf).filter(v => v >= 0.85).length
  if (high === total) return { color: 'var(--color-ex-green)', text: `${high}/${total} 字段高置信` }
  if (high < total / 2) return { color: 'var(--color-ex-warn)', text: `仅 ${high}/${total} 字段高置信 · 请仔细核对` }
  return { color: 'var(--color-ex-warn)', text: `${high}/${total} 字段高置信` }
})

function categoryLabel(key) { return store.categoryLabel(key) }
function currencySymbol(code) { return store.currencySymbol(code) }
function currencyLabel(code) {
  return store.currencies.find(c => c.code === code)?.label || code
}
function formatAmount(n) {
  return (n || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function onPickCategory() {
  categoryPickerOpen.value = true
}

async function onSave() {
  if (!form.value.invoice_amount || form.value.invoice_amount <= 0) {
    alert('请填写正确的发票金额')
    return
  }
  saving.value = true
  try {
    if (mergeMode.value === 'merge' && mergeable.value.length > 0) {
      // 合并模式: 累加金额到 mergeable[0] 对应的 detail
      router.replace(`/expense/${expenseId.value}/merge?primary=${idx.value}`)
      return
    }
    // 独立明细 → 调 addLine
    const payload = {
      expense_category: form.value.expense_category,
      expense_date: form.value.expense_date,
      currency: form.value.currency,
      invoice_amount: form.value.invoice_amount,
      description: form.value.description,
      document_count: 1,
      invoice_images: receipt.value?.file_url ? [{
        filename: `invoice-${idx.value}.jpg`,
        url: receipt.value.file_url,
        invoice_no: form.value.invoice_no,
        seller: form.value.seller,
      }] : [],
    }
    await expApi.addLine(expenseId.value, payload)
    store.updatePendingReceipt(idx.value, { saved: true })
    nextUnprocessed()  // 跳到下一张未处理的
  } catch (e) {
    alert('保存失败: ' + (e.response?.data?.message || e.message))
  } finally {
    saving.value = false
  }
}

function onSkip() {
  store.updatePendingReceipt(idx.value, { skipped: true })
  nextUnprocessed()
}

// 纯导航 — 不动 saved/skipped 状态, 用户可来回浏览
function navTo(targetIdx) {
  if (targetIdx < 0 || targetIdx >= total.value) return
  router.replace(`/expense/${expenseId.value}/confirm?idx=${targetIdx}`)
}

// 智能跳转 — 跳到下一张未处理的(saved=false 且 skipped=false)
// 全部处理完则清队列 + 跳 edit
function nextUnprocessed() {
  const arr = store.pendingReceipts
  // 优先找当前 idx 之后的未处理
  let target = arr.findIndex((r, i) => i > idx.value && !r.saved && !r.skipped)
  // 没找到 → 从头找(可能用户来回浏览跳过了某些)
  if (target < 0) target = arr.findIndex(r => !r.saved && !r.skipped)
  if (target >= 0) {
    router.replace(`/expense/${expenseId.value}/confirm?idx=${target}`)
  } else {
    // 全部处理完
    store.clearPendingReceipts()
    store.clearDetail(expenseId.value)
    router.replace(`/expense/${expenseId.value}/edit`)
  }
}
</script>
