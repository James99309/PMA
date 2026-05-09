<!--
  ApprovalView · 我审批的列表
  严格对齐 design_handoff/expense-approval.jsx::ApprovalList (L74-136)
  - StatusPad 54 + ExNav "我审批的"
  - 三段 tab(待我审批 N / 我已处理 / 抄送给我), active 带 ink 下划线 2px
  - 行: 36x36 头像(色彩按申请人) + 标题 14/600 + tag 9/600 + 副 12 ink3
        底: ID·时间 10 ink4 + 金额 14/600 serif
-->
<template>
  <div
    class="relative h-full overflow-hidden"
    :style="{ background: 'var(--color-ex-bg)', color: 'var(--color-ex-ink)', fontFamily: 'var(--font-sans)' }"
  >
    <div class="status-pad" />
    <ExNav
      title="我审批的"
      :sub="`${pendingCount} 待审批 · ${historyCount} 已处理`"
      :back="false"
    />

    <!-- 段落 tabs -->
    <div
      class="absolute left-0 right-0 z-[4] flex"
      :style="{
        top: '102px',
        padding: '8px 20px 8px',
        background: 'var(--color-ex-bg)',
        gap: '16px',
        fontSize: '13px',
        borderBottom: '1px solid var(--color-ex-divider)',
      }"
    >
      <span
        :style="{
          color: tab === 'pending' ? 'var(--color-ex-ink)' : 'var(--color-ex-ink3)',
          fontWeight: tab === 'pending' ? 600 : 400,
          borderBottom: tab === 'pending' ? '2px solid var(--color-ex-ink)' : 'none',
          paddingBottom: '6px',
        }"
        @click="tab = 'pending'"
      >
        待我审批
        <span v-if="pendingCount > 0" :style="{ color: 'var(--color-ex-warn)', marginLeft: '2px' }">{{ pendingCount }}</span>
      </span>
      <span
        :style="{
          color: tab === 'history' ? 'var(--color-ex-ink)' : 'var(--color-ex-ink3)',
          fontWeight: tab === 'history' ? 600 : 400,
          borderBottom: tab === 'history' ? '2px solid var(--color-ex-ink)' : 'none',
          paddingBottom: '6px',
        }"
        @click="tab = 'history'"
      >我已处理</span>
      <span
        :style="{
          color: tab === 'cc' ? 'var(--color-ex-ink)' : 'var(--color-ex-ink3)',
          fontWeight: tab === 'cc' ? 600 : 400,
          borderBottom: tab === 'cc' ? '2px solid var(--color-ex-ink)' : 'none',
          paddingBottom: '6px',
        }"
        @click="tab = 'cc'"
      >抄送给我</span>
    </div>

    <div
      class="overflow-auto h-full no-scrollbar"
      :style="{ paddingTop: '144px' }"
    >
      <div v-if="loading" :style="{ padding: '40px 20px', textAlign: 'center', color: 'var(--color-ex-ink3)', fontSize: '13px' }">加载中...</div>
      <div v-else-if="visibleItems.length === 0" :style="{ padding: '40px 20px', textAlign: 'center', color: 'var(--color-ex-ink3)', fontSize: '13px' }">
        {{ tab === 'pending' ? '没有待审批' : tab === 'history' ? '没有处理记录' : '没有抄送' }}
      </div>
      <div v-else>
        <div
          v-for="it in visibleItems"
          :key="`${tab}-${it.id}`"
          class="flex"
          :style="{
            background: 'var(--color-ex-card)',
            padding: '14px 20px',
            borderBottom: '1px solid var(--color-ex-divider-soft)',
            gap: '12px',
          }"
          @click="onOpenItem(it)"
        >
          <!-- avatar -->
          <div
            class="flex items-center justify-center flex-shrink-0"
            :style="{
              width: '36px', height: '36px', borderRadius: '18px',
              background: avatarColor(it.submitter_name || it.creator_name || ''),
              color: '#fff', fontSize: '13px', fontWeight: 600,
            }"
          >{{ (it.submitter_name || it.creator_name || '?').slice(0, 1) }}</div>

          <div class="flex-1 min-w-0">
            <div class="flex items-center" :style="{ gap: '8px' }">
              <div
                class="truncate"
                :style="{ fontSize: '14px', fontWeight: 600, color: 'var(--color-ex-ink)' }"
              >{{ it.title }}</div>
              <div
                :style="{
                  fontSize: '9px', fontWeight: 600,
                  color: it.tag_color, background: it.tag_bg,
                  padding: '2px 6px', borderRadius: '3px',
                  flexShrink: 0,
                }"
              >{{ it.tag }}</div>
            </div>
            <div
              class="truncate"
              :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)', marginTop: '3px' }"
            >{{ it.submitter_name || '—' }} · {{ it.subtitle || it.object_type_label }}</div>
            <div class="flex items-center justify-between" :style="{ marginTop: '6px' }">
              <div :style="{ fontSize: '10px', color: 'var(--color-ex-ink4)' }">
                {{ it.object_name || it.id }} · {{ it.time }}
              </div>
              <div
                v-if="it.amount !== null && it.amount !== undefined"
                :style="{
                  fontSize: '14px', fontWeight: 600,
                  fontFamily: 'var(--font-serif)', color: 'var(--color-ex-ink)',
                }"
              >{{ it.currency_symbol }}{{ formatAmount(it.amount) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as approvalApi from '@/api/approval'
import ExNav from '@/components/expense/ExNav.vue'

const router = useRouter()
const tab = ref('pending')
const pending = ref([])
const history = ref([])
const cc = ref([])
const loading = ref(false)

const pendingCount = computed(() => pending.value.length)
const historyCount = computed(() => history.value.length)

const visibleItems = computed(() => {
  if (tab.value === 'pending') return pending.value
  if (tab.value === 'history') return history.value
  return cc.value
})

function avatarColor(name) {
  // 简单 hash → 颜色
  const colors = ['#3A6FB7', '#9B5DE5', '#2F7A4F', '#C77B22', '#B5453A']
  if (!name) return colors[0]
  let h = 0
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0
  return colors[h % colors.length]
}

function formatAmount(n) {
  return (Number(n) || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmtTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const today = new Date()
  if (d.toDateString() === today.toDateString()) {
    return `今天 ${d.toTimeString().slice(0, 5)}`
  }
  const yesterday = new Date(today.getTime() - 86400000)
  if (d.toDateString() === yesterday.toDateString()) return '昨天'
  return `${d.getMonth() + 1} 月 ${d.getDate()} 日`
}

const TAG_PENDING = { color: 'var(--color-ex-warn)', bg: 'var(--color-ex-warn-soft)' }
const TAG_APPROVE = { color: 'var(--color-ex-green)', bg: 'var(--color-ex-green-soft)' }
const TAG_REJECT  = { color: 'var(--color-ex-red)', bg: 'var(--color-ex-red-soft)' }
const TAG_FORWARD = { color: 'var(--color-ex-blue)', bg: 'var(--color-ex-blue-soft)' }

async function loadPending() {
  const r = await approvalApi.getPendingApprovals()
  const items = r.data?.data?.items || []
  pending.value = items.map(i => ({
    id: i.id,
    title: i.object_name,
    subtitle: i.current_step ? `当前步骤 ${i.current_step}` : '',
    submitter_name: i.submitted_by_name,
    object_type_label: i.object_type_label,
    object_name: i.object_name,
    amount: i.total_amount ?? null,
    currency_symbol: i.currency_symbol || '¥',
    time: fmtTime(i.created_at),
    tag: `待我审批${i.current_step ? ' · ' + i.current_step : ''}`,
    tag_color: TAG_PENDING.color,
    tag_bg: TAG_PENDING.bg,
  }))
}

async function loadHistory() {
  const r = await approvalApi.getApprovalHistory()
  const items = r.data?.data?.items || []
  history.value = items.map(i => {
    const tagMeta = i.action === 'approve' ? { tag: '我已通过', ...TAG_APPROVE }
      : i.action === 'reject' ? { tag: '我已驳回', ...TAG_REJECT }
      : i.action === 'forward' ? { tag: '我已转交', ...TAG_FORWARD }
      : { tag: i.action || '已处理', ...TAG_APPROVE }
    return {
      id: i.id,
      title: i.object_name,
      subtitle: i.comment || '',
      object_type_label: i.object_type_label,
      object_name: i.object_name,
      amount: null,
      currency_symbol: '¥',
      time: fmtTime(i.created_at),
      tag: tagMeta.tag,
      tag_color: tagMeta.color,
      tag_bg: tagMeta.bg,
      _instance_id: i.instance_id,
    }
  })
}

async function loadCc() {
  const r = await approvalApi.getApprovalCc()
  cc.value = r.data?.data?.items || []
}

async function load() {
  loading.value = true
  try {
    if (tab.value === 'pending') await loadPending()
    else if (tab.value === 'history') await loadHistory()
    else await loadCc()
  } finally {
    loading.value = false
  }
}

watch(tab, load)
onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([loadPending(), loadHistory(), loadCc()])
  } finally {
    loading.value = false
  }
})

function onOpenItem(it) {
  // tab=pending → instance.id 直接跳详情
  // tab=history → record.instance_id
  const instanceId = it._instance_id || it.id
  router.push(`/approval/${instanceId}`)
}
</script>
