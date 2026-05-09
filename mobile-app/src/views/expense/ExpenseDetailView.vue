<!--
  ExpenseDetailView · 报销单详情(申请人视角, 含审批时间轴)
  严格对齐 design_handoff/expense-list-form.jsx::ExpenseDetail (L292-358)
  - StatusPad 54 + ExNav 48
  - hero(12/20/18 padding):
      chip 审批中(warn 10/600) + ID mono 10 ink4
      title 22/500 serif
      subtitle 13 ink3
      amount 38/500 serif (margin 14)
      meta 11 ink3 (人民币 · 共 N 项明细)
  - SectionHeader: 详情 → DefRow x6
  - SectionHeader: 审批流程 · 当前在「N」 → ExFlowNode x N
  - SectionHeader: 明细 · N 项 → 紧凑明细行
-->
<template>
  <div
    class="relative h-full overflow-hidden"
    :style="{ background: 'var(--color-ex-bg)', color: 'var(--color-ex-ink)', fontFamily: 'var(--font-sans)' }"
  >
    <div class="status-pad" />

    <ExNav
      :title="'报销单详情'"
      :sub="navSub"
      @back="$router.back()"
    >
      <template #right>
        <div
          v-if="detail?.control?.can_edit"
          :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)' }"
          @click="$router.push(`/expense/${id}/edit`)"
        >编辑</div>
        <div v-else :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)' }">···</div>
      </template>
    </ExNav>

    <div
      v-if="loading"
      class="overflow-auto h-full no-scrollbar"
      :style="{ paddingTop: '102px', textAlign: 'center', color: 'var(--color-ex-ink3)', fontSize: '13px' }"
    >
      <div :style="{ padding: '40px 20px' }">加载中...</div>
    </div>

    <div
      v-else-if="detail"
      class="overflow-auto h-full no-scrollbar"
      :style="{ paddingTop: '102px', paddingBottom: detail.control?.can_submit || detail.control?.can_recall || detail.control?.can_resubmit ? '90px' : '24px' }"
    >
      <!-- hero -->
      <div :style="{ padding: '12px 20px 18px' }">
        <div class="flex items-center" :style="{ gap: '8px', marginBottom: '6px' }">
          <div
            :style="{
              fontSize: '10px',
              fontWeight: 600,
              color: detail.status_meta.color,
              background: detail.status_meta.bg,
              padding: '2px 7px',
              borderRadius: '4px',
            }"
          >{{ detail.status_meta.label }}</div>
          <div
            :style="{
              fontSize: '10px',
              color: 'var(--color-ex-ink4)',
              letterSpacing: '0.6px',
              fontFamily: 'var(--font-mono)',
            }"
          >{{ detail.expense_number }}</div>
        </div>
        <div
          :style="{
            fontSize: '22px',
            fontWeight: 500,
            fontFamily: 'var(--font-serif)',
            color: 'var(--color-ex-ink)',
          }"
        >{{ detail.title }}</div>
        <div
          v-if="detail.description"
          :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)', marginTop: '4px' }"
        >{{ detail.description }}</div>
        <div
          :style="{
            fontSize: '38px',
            fontWeight: 500,
            fontFamily: 'var(--font-serif)',
            color: 'var(--color-ex-ink)',
            marginTop: '14px',
            lineHeight: 1,
          }"
        >{{ currencySymbol(detail.currency) }} {{ formatAmount(detail.total_amount) }}</div>
        <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginTop: '6px' }">
          {{ currencyLabel(detail.currency) }} · 共 {{ detail.lines.length }} 项明细
        </div>
      </div>

      <!-- 详情 def list -->
      <ExSectionHeader>详情</ExSectionHeader>
      <div :style="{ background: 'var(--color-ex-card)' }">
        <ExDefRow label="申请人">
          {{ detail.owner?.name || '—' }}
          <span v-if="detail.owner?.department" :style="{ color: 'var(--color-ex-ink3)' }">· {{ detail.owner.department }}</span>
        </ExDefRow>
        <ExDefRow label="申请时间">{{ detail.created_at || '—' }}</ExDefRow>
        <ExDefRow label="关联客户">
          {{ detail.customer?.name || '—' }}
          <span v-if="detail.customer?.code" :style="{ color: 'var(--color-ex-ink4)', fontSize: '11px' }">· {{ detail.customer.code }}</span>
        </ExDefRow>
        <ExDefRow label="关联项目">{{ detail.project?.name || '—' }}</ExDefRow>
        <ExDefRow label="费用归属">{{ detail.attributed_to?.name || '归属自己' }}</ExDefRow>
        <ExDefRow label="说明" :last="true">{{ detail.description || '—' }}</ExDefRow>
      </div>

      <!-- 审批流程 -->
      <ExSectionHeader v-if="detail.flow && detail.flow.length">
        审批流程
        <span v-if="currentNodeName"> · 当前在「{{ currentNodeName }}」</span>
      </ExSectionHeader>
      <div
        v-if="detail.flow && detail.flow.length"
        :style="{ background: 'var(--color-ex-card)', padding: '8px 20px 8px' }"
      >
        <ExFlowNode
          v-for="(n, i) in detail.flow"
          :key="i"
          :node="n"
          :last="i === detail.flow.length - 1"
        />
      </div>

      <!-- 明细缩略 -->
      <ExSectionHeader>明细 · {{ detail.lines.length }} 项</ExSectionHeader>
      <div :style="{ background: 'var(--color-ex-card)' }">
        <div
          v-for="(d, i) in detail.lines"
          :key="d.id"
          class="flex items-center justify-between"
          :style="{
            padding: '12px 20px',
            borderBottom: i < detail.lines.length - 1 ? '1px solid var(--color-ex-divider-soft)' : 'none',
          }"
        >
          <div>
            <div :style="{ fontSize: '13px', fontWeight: 600 }">{{ d.expense_category_label }}</div>
            <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginTop: '2px' }">
              {{ d.description || '—' }} · {{ d.expense_date }}
            </div>
          </div>
          <div :style="{ fontSize: '14px', fontFamily: 'var(--font-serif)', fontWeight: 500 }">
            {{ currencySymbol(d.currency) }}{{ formatAmount(d.invoice_amount) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏(申请人视角: 提交/召回/重提) -->
    <div
      v-if="detail && (detail.control?.can_submit || detail.control?.can_recall || detail.control?.can_resubmit)"
      class="absolute bottom-0 left-0 right-0 flex"
      :style="{
        padding: '12px 16px 28px',
        background: 'var(--color-ex-card)',
        borderTop: '1px solid var(--color-ex-divider)',
        gap: '10px',
      }"
    >
      <div
        v-if="detail.control.can_recall"
        class="flex-1 flex items-center justify-center"
        :style="{
          height: '46px',
          borderRadius: '23px',
          background: 'var(--color-ex-card)',
          border: '1.5px solid var(--color-ex-divider)',
          color: 'var(--color-ex-ink2)',
          fontSize: '14px',
          fontWeight: 600,
        }"
        @click="onRecall"
      >召回</div>
      <div
        v-if="detail.control.can_submit || detail.control.can_resubmit"
        class="flex items-center justify-center"
        :style="{
          flex: 2,
          height: '46px',
          borderRadius: '23px',
          background: 'var(--color-ex-ink)',
          color: 'var(--color-ex-card)',
          fontSize: '14px',
          fontWeight: 600,
        }"
        @click="onSubmit"
      >{{ detail.control.can_resubmit ? '重新提交' : '提交审批' }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useExpenseStore } from '@/stores/expense'
import { submitExpense, recallExpense, resubmitExpense } from '@/api/expense'
import ExNav from '@/components/expense/ExNav.vue'
import ExSectionHeader from '@/components/expense/ExSectionHeader.vue'
import ExDefRow from '@/components/expense/ExDefRow.vue'
import ExFlowNode from '@/components/expense/ExFlowNode.vue'

const route = useRoute()
const router = useRouter()
const store = useExpenseStore()
const id = computed(() => parseInt(route.params.id))
const loading = ref(false)

const detail = computed(() => store.detailCache[id.value])

const navSub = computed(() => detail.value
  ? `${detail.value.expense_number} · ${detail.value.status_meta.label}`
  : '')

const currentNodeName = computed(() => {
  const cur = detail.value?.flow?.find(n => n.state === 'current')
  return cur?.node || ''
})

function formatAmount(n) {
  return (n || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function currencySymbol(code) {
  const m = { CNY: '¥', USD: '$', HKD: 'HK$', TWD: 'NT$', SGD: 'S$', MYR: 'RM', IDR: 'Rp', THB: '฿', VND: '₫' }
  return m[code] || code
}
function currencyLabel(code) {
  const m = { CNY: '人民币', USD: '美元', HKD: '港币', TWD: '台币', SGD: '新加坡元', MYR: '马来西亚林吉特', IDR: '印尼盾', THB: '泰铢', VND: '越南盾' }
  return m[code] || code
}

async function load() {
  loading.value = true
  try {
    await store.fetchDetail(id.value, true)
  } finally {
    loading.value = false
  }
}

async function onSubmit() {
  if (!confirm(detail.value.control.can_resubmit ? '确认重新提交?' : '确认提交审批?')) return
  try {
    const r = detail.value.control.can_resubmit
      ? await resubmitExpense(id.value)
      : await submitExpense(id.value)
    if (r.data?.success) {
      store.detailCache[id.value] = r.data.data
    }
  } catch (e) {
    alert('提交失败: ' + (e.response?.data?.message || e.message))
  }
}

async function onRecall() {
  if (!confirm('确认召回此报销单?')) return
  try {
    const r = await recallExpense(id.value)
    if (r.data?.success) {
      store.detailCache[id.value] = r.data.data
    }
  } catch (e) {
    alert('召回失败: ' + (e.response?.data?.message || e.message))
  }
}

onMounted(load)
</script>
