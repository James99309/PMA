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
  <div class="flex flex-col h-full" style="background: #F7F5F2;">

    <!-- Header — 对齐 ProjectDetailView 标准: 返回 ‹ 报销 + ··· -->
    <div class="flex items-center justify-between px-5 py-2.5 shrink-0">
      <button @click="$router.back()"
        class="flex items-center gap-1 active:opacity-60 py-1 pr-2"
        style="color: var(--color-ink-2);">
        <svg width="9" height="14" viewBox="0 0 9 14">
          <path d="M7 1L1 7l6 6" fill="none" stroke="currentColor"
            stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <span class="text-[15px]">报销</span>
      </button>
      <button v-if="detail?.control?.can_edit"
        @click="$router.push(`/expense/${id}/edit`)"
        class="text-[15px] active:opacity-60 px-2"
        style="color: var(--color-ink-2);">编辑</button>
      <button v-else-if="hasMoreActions"
        @click="moreMenuOpen = true"
        class="text-[18px] font-bold active:opacity-60 px-2"
        style="color: var(--color-ink);">···</button>
      <div v-else style="width: 32px;" />
    </div>

    <!-- ··· 菜单(审批中支持召回; 已驳回支持重提) -->
    <Teleport to="body">
      <div v-if="moreMenuOpen"
        class="fixed inset-0 z-50"
        style="background: rgba(0,0,0,0.32);"
        @click.self="moreMenuOpen = false">
        <div class="absolute left-0 right-0 bottom-0"
          :style="{
            background: 'var(--color-ex-bg)',
            borderRadius: '20px 20px 0 0',
            paddingBottom: 'calc(20px + env(safe-area-inset-bottom))',
          }">
          <div :style="{ width: '36px', height: '4px', background: 'var(--color-ex-divider)', borderRadius: '2px', margin: '10px auto 6px' }" />
          <div v-if="detail?.control?.can_recall"
            class="text-[14px] text-center font-medium active:opacity-60"
            :style="{
              padding: '14px 20px', background: 'var(--color-ex-card)',
              borderTop: '1px solid var(--color-ex-divider-soft)',
              color: 'var(--color-ex-warn)',
            }"
            @click="moreMenuOpen = false; onRecall()">召回审批</div>
          <div v-if="detail?.control?.can_resubmit"
            class="text-[14px] text-center font-medium active:opacity-60"
            :style="{
              padding: '14px 20px', background: 'var(--color-ex-card)',
              borderTop: '1px solid var(--color-ex-divider-soft)',
              color: 'var(--color-ex-ink)',
            }"
            @click="moreMenuOpen = false; onSubmit()">重新提交</div>
          <div class="text-[14px] text-center active:opacity-60"
            :style="{
              padding: '14px 20px', background: 'var(--color-ex-card)',
              borderTop: '1px solid var(--color-ex-divider-soft)',
              color: 'var(--color-ex-ink2)',
            }"
            @click="moreMenuOpen = false">取消</div>
        </div>
      </div>
    </Teleport>

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 border-[#D97757] border-t-transparent rounded-full animate-spin" />
    </div>

    <div
      v-else-if="detail"
      class="flex-1 overflow-y-auto no-scrollbar"
      :style="{ paddingBottom: detail.control?.can_submit ? '90px' : '24px' }"
    >
      <!-- Hero — 对齐 ProjectDetailView 标准: 30px serif 标题 + 44px serif tabular 金额 -->
      <div class="px-7 pt-5 pb-6">
        <!-- 状态 chip + 单号 -->
        <div class="flex items-center gap-2 mb-3.5 flex-wrap">
          <!-- 状态 chip 在审批中时可点开流程 sheet (审批中 / 已驳回 / 已通过 / 已支付都有流程) -->
          <span
            class="text-[12px] font-medium inline-flex items-center"
            :class="hasFlow ? 'active:opacity-60 cursor-pointer' : ''"
            :style="{
              color: detail.status_meta.color,
              background: detail.status_meta.bg,
              padding: '2px 8px',
              borderRadius: '4px',
              gap: '3px',
            }"
            @click="hasFlow && (flowSheetOpen = true)"
          >
            {{ detail.status_meta.label }}<template v-if="hasFlow && currentNodeName"> · {{ currentNodeName }}</template>
            <svg v-if="hasFlow" width="9" height="9" viewBox="0 0 12 12" fill="none">
              <path d="M3 4.5l3 3 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <span
            class="text-[11px]"
            :style="{
              color: 'var(--color-ink-3)',
              letterSpacing: '0.5px',
              fontFamily: 'var(--font-mono)',
            }"
          >· {{ detail.expense_number }}</span>
        </div>

        <!-- 主题: 30px serif weight 500 (项目同款) -->
        <h1 class="font-serif m-0"
          :style="{
            fontSize: '30px',
            fontWeight: 500,
            lineHeight: '1.2',
            letterSpacing: '-0.3px',
            color: 'var(--color-ink)',
          }">{{ detail.title }}</h1>

        <!-- 副标题: 申请人 · 客户 · 项目 -->
        <div class="mt-3.5 text-[13px]" style="color: var(--color-ink-3);">
          {{ [detail.owner?.name, detail.customer?.name, detail.project?.name].filter(Boolean).join(' · ') || '—' }}
        </div>

        <!-- 金额: 44px serif tabular (项目同款) -->
        <div class="mt-7 flex items-baseline gap-2">
          <span class="font-serif font-medium tabular leading-none"
            :style="{ fontSize: '44px', color: 'var(--color-ink)' }">
            {{ currencySymbol(detail.currency) }}{{ formatAmount(detail.total_amount) }}
          </span>
          <span class="text-[14px]" style="color: var(--color-ink-3);">
            {{ currencyLabel(detail.currency) }} · {{ detail.lines.length }} 项明细
          </span>
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

      <!-- 明细 (放在审批流程之上, 用户审单时先看花了什么再看流程) -->
      <ExSectionHeader>明细 · {{ detail.lines.length }} 项</ExSectionHeader>
      <div :style="{ background: 'var(--color-ex-card)' }">
        <div
          v-for="(d, i) in detail.lines"
          :key="d.id"
          class="flex items-center active:opacity-60 cursor-pointer"
          :style="{
            padding: '12px 20px', gap: '12px',
            borderBottom: i < detail.lines.length - 1 ? '1px solid var(--color-ex-divider-soft)' : 'none',
          }"
          @click="openLineDetail(d)"
        >
          <!-- 实际发票缩略图 -->
          <div
            class="flex items-center justify-center flex-shrink-0 relative overflow-hidden"
            :style="{
              width: '40px', height: '40px', borderRadius: '4px',
              background: 'var(--color-ex-divider-soft)',
              color: 'var(--color-ex-ink4)', fontSize: '9px', fontWeight: 600,
            }"
          >
            <img v-if="lineThumbUrl(d)"
              :src="lineThumbUrl(d)"
              class="w-full h-full" style="object-fit: cover;"
              @error="$event.target.style.display='none'" />
            <span v-else>发票</span>
            <span v-if="(d.invoice_images?.length || 0) > 1"
              :style="{
                position: 'absolute', top: '-2px', right: '-2px',
                minWidth: '14px', height: '14px',
                borderRadius: '7px', padding: '0 3px',
                background: 'var(--color-ex-ink)', color: '#fff',
                fontSize: '8px', fontWeight: 700,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: '1.5px solid var(--color-ex-card)',
              }">{{ d.invoice_images.length }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <div :style="{ fontSize: '13px', fontWeight: 600 }">{{ d.expense_category_label }}</div>
            <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginTop: '2px' }">
              {{ d.description || '—' }} · {{ d.expense_date }}
            </div>
          </div>
          <div :style="{ fontSize: '14px', fontFamily: 'var(--font-serif)', fontWeight: 500 }">
            {{ currencySymbol(d.currency) }}{{ formatAmount(d.invoice_amount) }}
          </div>
          <div :style="{ fontSize: '14px', color: 'var(--color-ex-ink4)' }">›</div>
        </div>
      </div>

      <!-- 之前底部 '审批流程' section 已迁到顶部状态 chip 点击弹 ExFlowSheet, 节省屏幕 -->
    </div>

    <!-- 流程 sheet (顶部 chip 点击触发) -->
    <ExFlowSheet v-model="flowSheetOpen" :nodes="detail?.flow || []" />

    <!-- 明细详情 sheet -->
    <ExLineDetailSheet
      v-model="lineDetailOpen"
      :line="selectedLine"
      :base-currency="detail?.currency || 'CNY'" />

    <!-- 提交/重提确认 sheet (设计稿同款 ExSubmitSheet, 不再用 native confirm) -->
    <ExSubmitSheet
      v-if="detail"
      v-model="submitSheetOpen"
      :total-amount="detail.total_amount"
      :currency-symbol="currencySymbol(detail.currency)"
      :customer-name="detail.customer?.name || ''"
      :project-name="detail.project?.name || ''"
      :line-count="detail.lines?.length || 0"
      :next-approver="{ user: '上级', node: '上级审批' }"
      :submitting="submitting"
      @confirm="onConfirmSubmit"
    />

    <!-- 召回确认 sheet -->
    <ExConfirmSheet
      v-model="recallSheetOpen"
      eyebrow="召回"
      title="确认召回此报销?"
      :sub="detail ? `${detail.expense_number} · ${detail.title}` : ''"
      confirm-label="确认召回"
      color="warn"
      :submitting="recalling"
      @confirm="onConfirmRecall"
    />

    <!-- 底部操作栏(仅草稿态显示提交; 召回/重提 已迁到 ··· 菜单) -->
    <div
      v-if="detail?.control?.can_submit"
      class="absolute bottom-0 left-0 right-0"
      :style="{
        padding: '12px 16px 28px',
        background: 'var(--color-ex-card)',
        borderTop: '1px solid var(--color-ex-divider)',
        paddingBottom: 'calc(28px + env(safe-area-inset-bottom))',
      }"
    >
      <div
        class="flex items-center justify-center"
        :style="{
          height: '46px',
          borderRadius: '23px',
          background: 'var(--color-ex-ink)',
          color: 'var(--color-ex-card)',
          fontSize: '14px',
          fontWeight: 600,
        }"
        @click="onSubmit"
      >提交审批</div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useExpenseStore } from '@/stores/expense'
import { submitExpense, recallExpense, resubmitExpense, lineThumbUrl } from '@/api/expense'
import ExNav from '@/components/expense/ExNav.vue'
import ExSectionHeader from '@/components/expense/ExSectionHeader.vue'
import ExDefRow from '@/components/expense/ExDefRow.vue'
import ExFlowNode from '@/components/expense/ExFlowNode.vue'
import ExFlowSheet from '@/components/expense/ExFlowSheet.vue'
import ExLineDetailSheet from '@/components/expense/ExLineDetailSheet.vue'
import ExSubmitSheet from '@/components/expense/ExSubmitSheet.vue'
import ExConfirmSheet from '@/components/expense/ExConfirmSheet.vue'

const route = useRoute()
const router = useRouter()
const store = useExpenseStore()
const id = computed(() => parseInt(route.params.id))
const loading = ref(false)
const lineDetailOpen = ref(false)
const flowSheetOpen = ref(false)
const hasFlow = computed(() => Boolean(detail.value?.flow?.length))
const selectedLine = ref({})
const moreMenuOpen = ref(false)

const hasMoreActions = computed(() => Boolean(
  detail.value?.control?.can_recall || detail.value?.control?.can_resubmit
))

function openLineDetail(d) {
  selectedLine.value = d
  lineDetailOpen.value = true
}

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

// 提交 sheet 状态(用 ExSubmitSheet 替代原生 confirm)
const submitSheetOpen = ref(false)
const submitting = ref(false)

function onSubmit() {
  // 打开 ExSubmitSheet, 用户在 sheet 里点"确认提交"才真正调 API
  submitSheetOpen.value = true
}

async function onConfirmSubmit() {
  submitting.value = true
  try {
    const r = detail.value.control.can_resubmit
      ? await resubmitExpense(id.value)
      : await submitExpense(id.value)
    if (r.data?.success) {
      submitSheetOpen.value = false
      await store.fetchDetail(id.value, true)
    }
  } catch (e) {
    alert('提交失败: ' + (e.response?.data?.message || e.message))
  } finally {
    submitting.value = false
  }
}

// 召回 sheet 状态
const recallSheetOpen = ref(false)
const recalling = ref(false)

function onRecall() {
  recallSheetOpen.value = true
}

async function onConfirmRecall() {
  recalling.value = true
  try {
    const r = await recallExpense(id.value)
    if (r.data?.success) {
      recallSheetOpen.value = false
      await store.fetchDetail(id.value, true)
    }
  } catch (e) {
    alert('召回失败: ' + (e.response?.data?.message || e.message))
  } finally {
    recalling.value = false
  }
}

onMounted(load)
</script>
