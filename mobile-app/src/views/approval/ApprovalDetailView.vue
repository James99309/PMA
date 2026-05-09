<!--
  ApprovalDetailView · 审批详情(审批人视角)
  严格对齐 design_handoff/expense-approval.jsx::ApprovalDetail (L139-232)
-->
<template>
  <div class="flex flex-col h-full" style="background: #F7F5F2;">

    <!-- Header — 项目同款 (返回 ‹ 审批 + ··· 菜单) -->
    <div class="flex items-center justify-between px-5 py-2.5 shrink-0">
      <button @click="$router.back()"
        class="flex items-center gap-1 active:opacity-60 py-1 pr-2"
        style="color: var(--color-ink-2);">
        <svg width="9" height="14" viewBox="0 0 9 14">
          <path d="M7 1L1 7l6 6" fill="none" stroke="currentColor"
            stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <span class="text-[15px]">审批</span>
      </button>
      <button @click="moreMenuOpen = true"
        class="text-[18px] font-bold active:opacity-60 px-2"
        style="color: var(--color-ink);">···</button>
    </div>

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 border-[#D97757] border-t-transparent rounded-full animate-spin" />
    </div>

    <div
      v-else-if="detail"
      class="flex-1 overflow-y-auto no-scrollbar"
      :style="{ paddingBottom: detail.is_current_approver ? '92px' : '24px' }"
    >
      <!-- Hero — 项目同款: 30px 标题 + 44px serif tabular 金额 -->
      <div class="px-7 pt-5 pb-6">
        <!-- 状态 chip + 单号 -->
        <div class="flex items-center gap-2 mb-3.5 flex-wrap">
          <span
            v-if="currentStepName"
            class="text-[12px] font-medium"
            :style="{
              color: 'var(--color-ex-warn)',
              background: 'var(--color-ex-warn-soft)',
              padding: '2px 8px', borderRadius: '4px',
            }"
          >等你审批 · {{ currentStepName }}</span>
          <span
            class="text-[11px]"
            :style="{
              color: 'var(--color-ink-3)', letterSpacing: '0.5px',
              fontFamily: 'var(--font-mono)',
            }"
          >· {{ detail.business_obj?.expense_number || detail.object_name }}</span>
        </div>

        <!-- 主题: 30px serif (项目同款) -->
        <h1 class="font-serif m-0"
          :style="{
            fontSize: '30px', fontWeight: 500,
            lineHeight: '1.2', letterSpacing: '-0.3px',
            color: 'var(--color-ink)',
          }">{{ detail.business_obj?.title || detail.object_name }}</h1>

        <!-- Sub: 申请人提交时间 -->
        <div v-if="detail.submitter" class="mt-3.5 text-[13px]" style="color: var(--color-ink-3);">
          {{ detail.submitter.name }} 提交 · {{ (detail.created_at || '').slice(0, 10) }}
        </div>

        <!-- 金额 44px serif tabular (项目同款) -->
        <div class="mt-7 flex items-baseline gap-2">
          <span class="font-serif font-medium tabular leading-none"
            :style="{ fontSize: '44px', color: 'var(--color-ink)' }">
            {{ amountStr }}
          </span>
          <span v-if="detail.business_obj" class="text-[14px]" style="color: var(--color-ink-3);">
            {{ currencyLabel(detail.business_obj.currency) }} · {{ detail.business_obj.detail_count }} 项明细
          </span>
        </div>
        <div v-if="waitingHint" class="text-[12px] mt-1.5" style="color: var(--color-ink-3);">{{ waitingHint }}</div>
      </div>

      <!-- 申请人卡 -->
      <div
        v-if="detail.submitter"
        class="flex items-center"
        :style="{
          margin: '0 20px 16px',
          padding: '12px 14px',
          background: 'var(--color-ex-card)',
          borderRadius: '10px',
          border: '1px solid var(--color-ex-divider)',
          gap: '12px',
        }"
      >
        <div
          class="flex items-center justify-center flex-shrink-0"
          :style="{
            width: '38px', height: '38px', borderRadius: '19px',
            background: detail.submitter.avatar_color || '#3A6FB7',
            color: '#fff', fontSize: '14px', fontWeight: 600,
          }"
        >{{ detail.submitter.name.slice(0, 1) }}</div>
        <div class="flex-1">
          <div :style="{ fontSize: '13px', fontWeight: 600 }">
            {{ detail.submitter.name }}
            <span v-if="detail.submitter.department" :style="{ color: 'var(--color-ex-ink3)' }">· {{ detail.submitter.department }}</span>
          </div>
          <div
            v-if="detail.submitter_stats"
            :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginTop: '2px' }"
          >本月已申报 {{ detail.submitter_stats.month_count }} 笔 · 平均 ¥{{ formatAmount(detail.submitter_stats.month_avg) }}</div>
        </div>
        <div
          class="flex items-center justify-center"
          :style="{
            width: '28px', height: '28px', borderRadius: '14px',
            background: 'var(--color-ex-divider-soft)',
            fontSize: '12px', color: 'var(--color-ex-ink3)',
          }"
        >✉</div>
      </div>

      <!-- 详情 def list -->
      <ExSectionHeader v-if="detail.business_obj">详情</ExSectionHeader>
      <div v-if="detail.business_obj" :style="{ background: 'var(--color-ex-card)' }">
        <ExDefRow label="主题">{{ detail.business_obj.title }}</ExDefRow>
        <ExDefRow label="客户">{{ detail.business_obj.customer_name || '—' }}</ExDefRow>
        <ExDefRow label="项目">{{ detail.business_obj.project_name || '—' }}</ExDefRow>
        <ExDefRow label="说明" :last="true">{{ detail.business_obj.description || '—' }}</ExDefRow>
      </div>

      <!-- 明细 list -->
      <ExSectionHeader v-if="detail.business_obj?.lines?.length">
        明细 · {{ detail.business_obj.lines.length }} 项
      </ExSectionHeader>
      <div v-if="detail.business_obj?.lines?.length" :style="{ background: 'var(--color-ex-card)' }">
        <div
          v-for="(d, i) in detail.business_obj.lines"
          :key="d.id"
          class="flex items-center"
          :style="{
            padding: '12px 20px',
            borderBottom: i < detail.business_obj.lines.length - 1 ? '1px solid var(--color-ex-divider-soft)' : 'none',
            gap: '12px',
          }"
        >
          <div
            :style="{
              width: '40px', height: '28px', borderRadius: '3px',
              background: '#F5EFE3', flexShrink: 0,
              fontSize: '4px', padding: '2px',
              color: '#7B2F22', lineHeight: 1.4,
            }"
          >增值税<br>普通<br>发票</div>
          <div class="flex-1 min-w-0">
            <div :style="{ fontSize: '13px', fontWeight: 600 }">{{ d.category }}</div>
            <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginTop: '2px' }">
              {{ d.description }} · {{ d.expense_date }}
            </div>
          </div>
          <div :style="{ fontSize: '14px', fontFamily: 'var(--font-serif)', fontWeight: 500 }">
            {{ currencySymbol(d.currency) }}{{ formatAmount(d.invoice_amount) }}
          </div>
        </div>
      </div>

      <!-- 审批进度 -->
      <ExSectionHeader v-if="detail.flow?.length">审批进度</ExSectionHeader>
      <div
        v-if="detail.flow?.length"
        :style="{ background: 'var(--color-ex-card)', padding: '8px 20px' }"
      >
        <ExFlowNode
          v-for="(n, i) in detail.flow"
          :key="i"
          :node="n"
          :last="i === detail.flow.length - 1"
        />
      </div>
    </div>

    <!-- 底部审批操作 -->
    <div
      v-if="detail?.is_current_approver"
      class="absolute bottom-0 left-0 right-0 flex"
      :style="{
        padding: '12px 16px 28px',
        paddingBottom: 'calc(28px + env(safe-area-inset-bottom))',
        background: 'var(--color-ex-card)',
        borderTop: '1px solid var(--color-ex-divider)',
        gap: '10px',
      }"
    >
      <div
        class="flex items-center justify-center"
        :style="{
          width: '46px', height: '46px', borderRadius: '23px',
          background: 'var(--color-ex-divider-soft)',
          fontSize: '18px', color: 'var(--color-ex-ink2)',
        }"
        @click="moreMenuOpen = true"
      >↻</div>
      <div
        class="flex-1 flex items-center justify-center"
        :style="{
          height: '46px', borderRadius: '23px',
          background: 'var(--color-ex-card)',
          border: '1.5px solid var(--color-ex-red)',
          color: 'var(--color-ex-red)',
          fontSize: '14px', fontWeight: 600,
        }"
        @click="openSheet('reject')"
      >驳回</div>
      <div
        class="flex items-center justify-center"
        :style="{
          flex: 2,
          height: '46px', borderRadius: '23px',
          background: 'var(--color-ex-green)',
          color: 'var(--color-ex-card)',
          fontSize: '14px', fontWeight: 600,
        }"
        @click="openSheet('approve')"
      >同意</div>
    </div>

    <!-- ··· 菜单(转交) -->
    <Teleport to="body">
      <div
        v-if="moreMenuOpen"
        class="fixed inset-0 z-50"
        :style="{ background: 'rgba(0,0,0,0.32)' }"
        @click.self="moreMenuOpen = false"
      >
        <div
          class="absolute left-0 right-0 bottom-0"
          :style="{
            background: 'var(--color-ex-bg)',
            borderRadius: '20px 20px 0 0',
            paddingBottom: 'calc(20px + env(safe-area-inset-bottom))',
          }"
        >
          <div :style="{ width: '36px', height: '4px', background: 'var(--color-ex-divider)', borderRadius: '2px', margin: '10px auto 6px' }" />
          <div
            v-if="detail?.is_current_approver"
            :style="{
              padding: '14px 20px', background: 'var(--color-ex-card)',
              borderTop: '1px solid var(--color-ex-divider-soft)',
              fontSize: '14px', color: 'var(--color-ex-blue)', fontWeight: 600, textAlign: 'center',
            }"
            @click="onForwardClick"
          >转交其他人</div>
          <div
            :style="{
              padding: '14px 20px', background: 'var(--color-ex-card)',
              borderTop: '1px solid var(--color-ex-divider-soft)',
              fontSize: '14px', color: 'var(--color-ex-ink2)', textAlign: 'center',
            }"
            @click="moreMenuOpen = false"
          >取消</div>
        </div>
      </div>
    </Teleport>

    <!-- 同意/驳回/转交 sheet -->
    <ApprovalSheet
      v-model="sheetOpen"
      :action="currentAction"
      :context-line="contextLine"
      :selected-user="selectedForwardUser"
      :submitting="submitting"
      @confirm="onConfirmAction"
      @pick-user="userPickerOpen = true"
    />

    <!-- 转交目标 user picker -->
    <ExSearchPickerSheet
      v-model="userPickerOpen"
      title="选择转交目标"
      placeholder="搜索用户"
      :search-fn="searchUsers"
      @pick="onPickForwardUser"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import client from '@/api/client'
import * as approvalApi from '@/api/approval'
import ExNav from '@/components/expense/ExNav.vue'
import ExSectionHeader from '@/components/expense/ExSectionHeader.vue'
import ExDefRow from '@/components/expense/ExDefRow.vue'
import ExFlowNode from '@/components/expense/ExFlowNode.vue'
import ApprovalSheet from '@/components/expense/ApprovalSheet.vue'
import ExSearchPickerSheet from '@/components/expense/ExSearchPickerSheet.vue'

const route = useRoute()
const router = useRouter()
const instanceId = computed(() => parseInt(route.params.instanceId))

const detail = ref(null)
const loading = ref(false)
const sheetOpen = ref(false)
const currentAction = ref('approve')
const moreMenuOpen = ref(false)
const submitting = ref(false)
const userPickerOpen = ref(false)
const selectedForwardUser = ref(null)

const navTitle = computed(() => detail.value
  ? `审批 · ${detail.value.business_obj?.title || detail.value.object_name}`
  : '审批详情')
const navSub = computed(() => detail.value?.submitter
  ? `${detail.value.submitter.name} 提交 · ${(detail.value.created_at || '').slice(0, 10)}`
  : '')

const currentStepName = computed(() => detail.value?.flow?.find(n => n.state === 'current')?.node || '')

const amountStr = computed(() => {
  const b = detail.value?.business_obj
  if (!b) return '—'
  return `${currencySymbol(b.currency)} ${formatAmount(b.total_amount)}`
})

const waitingHint = computed(() => {
  if (!detail.value?.created_at) return ''
  const submitted = new Date(detail.value.created_at)
  const ms = Date.now() - submitted.getTime()
  const hours = Math.floor(ms / 3600000)
  if (hours < 1) return '刚刚提交'
  if (hours < 24) return `已等待 ${hours} 小时`
  const days = Math.floor(hours / 24)
  return `已等待 ${days} 天`
})

const contextLine = computed(() => detail.value
  ? `${detail.value.business_obj?.expense_number || detail.value.object_name} · ${detail.value.business_obj?.title || ''} · ${amountStr.value}`
  : '')

function formatAmount(n) {
  return (Number(n) || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
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
    const r = await approvalApi.getApprovalDetail(instanceId.value)
    if (r.data?.success) detail.value = r.data.data
  } finally {
    loading.value = false
  }
}

function openSheet(action) {
  currentAction.value = action
  selectedForwardUser.value = null
  sheetOpen.value = true
  moreMenuOpen.value = false
}

function onForwardClick() {
  moreMenuOpen.value = false
  openSheet('forward')
}

async function onConfirmAction({ comment, targetUserId }) {
  submitting.value = true
  try {
    if (currentAction.value === 'forward') {
      await approvalApi.forwardApproval(instanceId.value, targetUserId, comment)
    } else {
      await approvalApi.doApprovalAction(instanceId.value, currentAction.value, comment)
    }
    sheetOpen.value = false
    await load()
    setTimeout(() => router.back(), 600)
  } catch (e) {
    alert('操作失败: ' + (e.response?.data?.message || e.message))
  } finally {
    submitting.value = false
  }
}

async function searchUsers(q) {
  try {
    const r = await client.get('/users/search', { params: { q: q || '', per_page: 20 } }).catch(() =>
      client.get('/users', { params: { search: q || '', per_page: 20 } }))
    const items = r.data?.data?.items || r.data?.items || r.data?.users || r.data || []
    return items.map(u => ({
      id: u.id,
      label: u.real_name || u.username,
      sub: u.department || u.role || '',
      role_label: u.role_display || u.role || '',
    }))
  } catch {
    return []
  }
}

function onPickForwardUser(it) {
  selectedForwardUser.value = {
    id: it.id,
    name: it.label,
    role_label: it.role_label || it.sub,
  }
}

onMounted(load)
</script>
