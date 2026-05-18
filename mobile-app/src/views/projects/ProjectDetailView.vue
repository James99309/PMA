<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getProject, addProjectNote } from '@/api/projects'
import { searchUsers, createConversation } from '@/api/chat'
import client from '@/api/client'
import ExFlowSheet from '@/components/expense/ExFlowSheet.vue'
import ExConfirmSheet from '@/components/expense/ExConfirmSheet.vue'
import ProjectSubmitSheet from '@/components/project/ProjectSubmitSheet.vue'
import { useApprovalRecall } from '@/composables/useApprovalRecall'
import Avatar from '@/components/common/Avatar.vue'
import MentionPopover from '@/components/common/MentionPopover.vue'
import MessageText from '@/components/common/MessageText.vue'
import MessageRefs from '@/components/common/MessageRefs.vue'
import PendingRefsPreview from '@/components/common/PendingRefsPreview.vue'
import StageAdvanceCard from '@/components/common/StageAdvanceCard.vue'
import NoteSheet from '@/components/common/NoteSheet.vue'
import ExSearchPickerSheet from '@/components/expense/ExSearchPickerSheet.vue'
import SwipeRowAction from '@/components/common/SwipeRowAction.vue'
import { useChatStore } from '@/stores/chat'
import { useDictionariesStore } from '@/stores/dictionaries'
import { useAuthStore } from '@/stores/auth'
import { useMention } from '@/composables/useMention'

const chatStore = useChatStore()
const dictStore = useDictionariesStore()
const auth = useAuthStore()

const route = useRoute()
const router = useRouter()
const { t, te } = useI18n()

// currency display now comes from the backend (project.amount_display),
// single source = dictionary_helpers.format_money — respects per-project
// quotation_currency, no more region-based hardcoding
const project = ref(null)
const loading = ref(true)

const showNoteBox = ref(false)

// ─── 项目讨论卡片 · 行内快速回复（共享 store，与 GroupChatView 同源）────────
// 真实讨论群 id 来自后端 project.discussion_conversation_id
// 没有讨论群时（null）→ 走 "创建讨论群" 流程，不显示输入框和消息预览
const realConvId = computed(() => project.value?.discussion_conversation_id || null)
const hasGroup = computed(() => !!realConvId.value)
const groupId = computed(() => realConvId.value ? String(realConvId.value) : null)

// 项目讨论卡片：真实数据驱动，无 mock 种子
// 卡片只显示最近 4 条（包括用户刚发的）—— 倒序展示新的在上
const chatPreviewMessages = computed(() => {
  if (!groupId.value) return []
  const all = chatStore.getGroup(groupId.value, [])
  return [...all].slice(-4).reverse()
})

// 项目成员（来自后端 owner + shared_with_users）
const projectMembers = computed(() => project.value?.members || [])
const memberSummary = computed(() => {
  const list = projectMembers.value
  if (!list.length) return ''
  return list.slice(0, 4).map(m => m.name).join(' · ') + (list.length > 4 ? ` ·…` : '')
})

// ─── 创建讨论群（项目还未绑定群聊时）─────────────────────────────
const showCreateGroupSheet = ref(false)
const cgSearch = ref('')
const cgResults = ref([])
const cgSelected = ref([])  // [{id, name, avatar, dept}]
const cgSearching = ref(false)
const cgCreating = ref(false)
let cgSearchTimer = null

function openCreateGroup() {
  showCreateGroupSheet.value = true
  cgSearch.value = ''
  cgSelected.value = []
  cgResults.value = []
  doCgSearch('')
}
function closeCreateGroup() {
  showCreateGroupSheet.value = false
}
function onCgSearchInput() {
  clearTimeout(cgSearchTimer)
  cgSearchTimer = setTimeout(() => doCgSearch(cgSearch.value.trim()), 250)
}
async function doCgSearch(q) {
  cgSearching.value = true
  try {
    const r = await searchUsers(q)
    cgResults.value = r.data?.success ? (r.data.data || []) : []
  } catch (e) {
    console.error('cg search failed', e)
    cgResults.value = []
  } finally {
    cgSearching.value = false
  }
}
function isCgSelected(u) {
  return cgSelected.value.some(s => s.id === u.id)
}
function toggleCgSelect(u) {
  const i = cgSelected.value.findIndex(s => s.id === u.id)
  if (i >= 0) cgSelected.value.splice(i, 1)
  else cgSelected.value.push(u)
}
async function confirmCreateGroup() {
  if (cgSelected.value.length < 1 || cgCreating.value || !project.value) return
  cgCreating.value = true
  try {
    const r = await createConversation({
      type: 'group',
      name: project.value.name,
      participant_ids: cgSelected.value.map(u => u.id),
      sync_metadata: { project_id: project.value.id },
    })
    const data = r.data
    if (data?.success && data?.data?.id) {
      const cid = data.data.id
      closeCreateGroup()
      // 刷新一次项目详情让 discussion_conversation_id 生效（后续返回此页时即可）
      router.push({
        path: `/messages/group/${cid}`,
        query: { name: project.value.name },
      })
    } else {
      alert(data?.message || t('project.detCreateDiscussionFailed'))
    }
  } catch (e) {
    console.error('create group failed', e)
    alert(`创建失败：${e.message || e}`)
  } finally {
    cgCreating.value = false
  }
}

const chatReplyText = ref('')
const chatReplyInput = ref(null)
const chatReplySending = ref(false)

// @ 提及（项目讨论卡专用 —— useMention 内置 pendingRefs 跟踪 #/$）
const chatMention = useMention(chatReplyInput)

function handleChatInput(e) {
  chatMention.onInput(e.target.value, e.target.selectionStart)
}
function handleChatMentionSelect(payload) {
  chatMention.onSelect(payload, chatReplyText.value, t => { chatReplyText.value = t })
}

function sendChatReply() {
  const t = chatReplyText.value.trim()
  if (!t || chatReplySending.value || !groupId.value) return
  chatReplySending.value = true
  const now = new Date()
  const hh = String(now.getHours()).padStart(2, '0')
  const mm = String(now.getMinutes()).padStart(2, '0')
  chatStore.appendToGroup(groupId.value, {
    kind: 'me', from: '我', initial: '我',
    time: `${hh}:${mm}`, text: t,
    refs: chatMention.pendingRefs.value.length ? [...chatMention.pendingRefs.value] : undefined,
  })
  chatReplyText.value = ''
  chatMention.clearRefs()
  chatReplyInput.value?.blur()
  setTimeout(() => { chatReplySending.value = false }, 200)
}
const showStagePicker = ref(false)
const updatingStage = ref(false)
const selectedStage = ref(null)

const showAllQuotations = ref(false)
const showAuthModal = ref(false)

// Project ↔ customer link sheet (detail page customers section)
const customerPickerOpen = ref(false)
const addingCustomer = ref(false)
const removingAssocId = ref(null)
async function searchCompaniesForLink(q) {
  // Reuse the same endpoint other pickers use (Expense/WorkItem/Task).
  const r = await client.get('/mobile/customers', { params: { q: q || '', search: q || '', per_page: 20 } })
  return (r.data?.data?.items || []).map(c => ({
    id: c.id,
    label: c.name || c.company_name,
    sub: c.primary_contact_name || c.industry || '',
  }))
}
async function pickCompanyForLink(item) {
  if (!item || addingCustomer.value) return
  addingCustomer.value = true
  try {
    const r = await client.post(
      `/mobile/projects/${route.params.id}/customers`,
      { company_id: item.id },
    )
    if (r.data?.success === false) {
      // surface 409 duplicate / 403 access denied without throwing
      alert(r.data?.message || t('project.detLinkedCustomerAddFail'))
    } else {
      await load()
    }
  } catch (e) {
    alert(e?.response?.data?.message || t('project.detLinkedCustomerAddFail'))
  } finally {
    addingCustomer.value = false
    customerPickerOpen.value = false
  }
}
async function removeLinkedCustomer(c) {
  if (!c?.association_id || removingAssocId.value) return
  if (!c.can_remove) return
  if (!confirm(t('project.detLinkedCustomerRemoveConfirm', { name: c.name }))) return
  removingAssocId.value = c.association_id
  try {
    await client.delete(`/mobile/projects/${route.params.id}/customers/${c.association_id}`)
    await load()
  } catch (e) {
    alert(e?.response?.data?.message || t('project.detLinkedCustomerRemoveFail'))
  } finally {
    removingAssocId.value = null
  }
}

// 审批流程 sheet (顶部 chip 点击展开) — 走通用 ApprovalInstance
const flowSheetOpen = ref(false)
const flowNodes = ref([])
const flowLoadError = ref('')
async function loadAndShowFlow() {
  if (!project.value) return
  flowSheetOpen.value = true
  flowLoadError.value = ''
  flowNodes.value = []
  try {
    const r = await client.get('/mobile/approval/flow-by-object', {
      params: { object_type: 'project', object_id: project.value.id },
    })
    const flow = r.data?.data?.flow || []
    flowNodes.value = flow
    if (flow.length === 0) {
      flowLoadError.value = '未找到流程数据（此项目可能由旧入口创建）'
    }
  } catch (e) {
    flowLoadError.value = '流程加载失败'
  }
}
const submittingAuth = ref(false)

// 召回 — 复用 composable
const {
  sheetOpen: recallSheetOpen,
  submitting: recalling,
  open: openRecall,
  confirm: confirmRecall,
} = useApprovalRecall({
  request: () => client.post(`/mobile/projects/${route.params.id}/recall`),
  onSuccess: load,
})

// 主流程进度条阶段 keys（横向 dots） —— 终止态 lost/paused 不在 track 上
const STAGE_TRACK_KEYS = ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed']

// 阶段赢率（前端，不进字典）。描述走 i18n: project.stageDesc.<key>
const STAGE_PCT = {
  discover: 10, embed: 25, pre_tender: 35, tendering: 50,
  awarded: 75, quoted: 85, signed: 100, lost: 0, paused: 0,
}

// 字典驱动：label 来自后端 project_stage 字典
const stageDictList = computed(() => dictStore.list('project_stage'))
const stageLabelMap = computed(() => dictStore.labelMap('project_stage'))

// 拼出 STAGES_ALL：字典 displayLabel(按 locale 切 zh/en) + 前端 desc/pct
const STAGES_ALL = computed(() => stageDictList.value.map(d => ({
  key: d.key,
  label: d.displayLabel || d.label,
  desc: te(`project.stageDesc.${d.key}`) ? t(`project.stageDesc.${d.key}`) : '',
  pct:  STAGE_PCT[d.key] ?? 0,
})))

// 主进度 track：按 STAGE_TRACK_KEYS 顺序取字典 label
const STAGE_TRACK = computed(() => STAGE_TRACK_KEYS
  .map(k => ({ key: k, label: stageLabelMap.value[k] || k }))
  .filter(s => s.label !== s.key)  // 字典还没加载时 label === key，先不渲染
)

const STAGE_ORDER = computed(() => stageDictList.value.map(d => d.key))

// 严格对齐 customer-screens.jsx StageDot 配色（A 方向 5 tone）
const STAGE_COLORS = {
  discover:   '#7A7570',  // ink-3
  embed:      '#7A7570',
  pre_tender: '#7A7570',
  tendering:  '#D97757',  // accent
  awarded:    '#D97757',
  quoted:     '#D97757',
  signed:     '#1A1A1A',  // ink
  lost:       '#C2BBB3',  // ink-4
  paused:     '#C2BBB3',
}

// 6 级活跃度配色（覆盖后端所有 status，避免 fallback 到黑色）
const ACTIVITY_COLORS = {
  highly_active: '#166534',  // 深绿
  active:        '#1E40AF',  // 深蓝
  normal:        '#0369A1',  // 深青
  to_follow:     '#A16207',  // 深黄
  dormant:       '#C2410C',  // 深橙
  churned:       '#4B5563',  // 深灰
  frozen:        '#6B7280',  // 中灰
}


const stageColor = computed(() =>
  project.value ? (STAGE_COLORS[project.value.current_stage] || '#9CA3AF') : '#9CA3AF'
)

const canAdvanceStage = computed(() => {
  if (!project.value) return false
  return project.value.current_stage !== 'signed'
    && !project.value.is_locked
    && project.value.can_edit !== false
})

const showAuthButton = computed(() => {
  if (!project.value) return false
  if (project.value.authorization_code) return false
  if (project.value.has_pending_approval) return false
  if (project.value.authorization_status === 'pending') return false  // 兼容老数据
  return true
})

// Next stage to advance to (from track if current is on track, else from full order)
const nextTrackStage = computed(() => {
  if (!project.value) return null
  const cur = project.value.current_stage
  const track = STAGE_TRACK.value
  const order = STAGE_ORDER.value
  const tIdx = track.findIndex(s => s.key === cur)
  if (tIdx !== -1 && tIdx < track.length - 1) return track[tIdx + 1]
  const aIdx = order.indexOf(cur)
  if (aIdx !== -1 && aIdx < order.length - 1) {
    const nk = order[aIdx + 1]
    return STAGES_ALL.value.find(s => s.key === nk) || null
  }
  return null
})

// Status of each track dot: 'past' | 'current' | 'future'
function trackStatus(key) {
  const cur = project.value?.current_stage
  const track = STAGE_TRACK.value
  const order = STAGE_ORDER.value
  const tCur = track.findIndex(s => s.key === cur)
  const tKey = track.findIndex(s => s.key === key)
  if (tCur !== -1) {
    if (tKey < tCur) return 'past'
    if (tKey === tCur) return 'current'
    return 'future'
  }
  // Off-track: compare by overall order
  const aKey = order.indexOf(key)
  const aCur = order.indexOf(cur)
  if (aKey < aCur) return 'past'
  return 'future'
}

// Stepper dot 样式 — 对齐 ADetail line 343-348
function dotStyle(status) {
  if (status === 'current') {
    return {
      width: '14px', height: '14px', borderRadius: '50%',
      background: 'var(--color-accent)', display: 'block',
    }
  }
  if (status === 'past') {
    return {
      width: '8px', height: '8px', borderRadius: '50%',
      background: 'var(--color-ink)', display: 'block',
    }
  }
  return {
    width: '8px', height: '8px', borderRadius: '50%',
    background: 'transparent',
    border: '1.5px solid var(--color-ink-3)',
    display: 'block',
  }
}

// Stepper label 样式 — 对齐 ADetail line 348
function labelStyle(status) {
  if (status === 'current') {
    return { fontSize: '10px', color: 'var(--color-accent)', fontWeight: 600 }
  }
  if (status === 'past') {
    return { fontSize: '10px', color: 'var(--color-ink-2)', fontWeight: 500 }
  }
  return { fontSize: '10px', color: 'var(--color-ink-3)', fontWeight: 500 }
}

// Picker status for a stage row
function pickerStatus(key) {
  const cur = project.value?.current_stage
  const order = STAGE_ORDER.value
  const aCur = order.indexOf(cur)
  const aKey = order.indexOf(key)
  if (aKey < aCur) return 'past'
  if (key === cur) return 'current'
  return 'future'
}

async function load() {
  try {
    const res = await getProject(route.params.id)
    project.value = res.data.data
  } finally {
    loading.value = false
  }
}

function openNoteBox() {
  showNoteBox.value = true
}

async function submitNote(text) {
  await addProjectNote(route.params.id, text)
  await load()
}

function openStagePicker() {
  if (!canAdvanceStage.value) return
  selectedStage.value = nextTrackStage.value?.key || null
  showStagePicker.value = true
}

async function confirmStageUpdate() {
  if (!selectedStage.value || updatingStage.value) return
  updatingStage.value = true
  try {
    await client.post(`/mobile/projects/${route.params.id}/stage`, { stage: selectedStage.value })
    showStagePicker.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.message || t('project.detUpdateFailed'))
  } finally {
    updatingStage.value = false
  }
}

async function submitAuthRequest() {
  submittingAuth.value = true
  try {
    await client.post(`/mobile/projects/${route.params.id}/auth-request`, {})
    showAuthModal.value = false
    await load()
  } catch (e) {
    const msg = e.response?.data?.message || ''
    // 已存在 instance(stale UI) — 静默关闭 + 刷新 + 顺势打开流程查看
    if (msg.includes('已有进行中') || msg.includes('正在审批')) {
      showAuthModal.value = false
      await load()
      loadAndShowFlow()
    } else {
      alert(msg || t('project.detSubmitFailed'))
    }
  } finally {
    submittingAuth.value = false
  }
}

function callPhone(phone) { if (phone) window.open(`tel:${phone}`) }
function openQuotation(id) { router.push(`/quotations/${id}`) }

function formatDelivery(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${y} · ${m} · ${d}`
}

function contactInitial(name) {
  return name ? name.charAt(0).toUpperCase() : '?'
}

onMounted(() => {
  dictStore.ensure('project_stage')
  load()
})
</script>

<template>
  <div class="flex flex-col h-full bg-[#F7F5F2]">

    <!-- Header — 对齐 ADetail line 289-295 (返回 ink-2 不是 accent) -->
    <div class="flex items-center justify-between px-5 py-2.5 shrink-0">
      <button @click="router.back()"
        class="flex items-center gap-1 active:opacity-60 py-1 pr-2"
        style="color: var(--color-ink-2);">
        <svg width="9" height="14" viewBox="0 0 9 14">
          <path d="M7 1L1 7l6 6" fill="none" stroke="currentColor"
            stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <span class="text-[15px]">{{ t('common.backProjects') }}</span>
      </button>
      <button v-if="project?.can_edit"
        @click="router.push(`/projects/${project.id}/edit`)"
        class="active:opacity-60 px-2"
        style="font-size: 15px; font-weight: 500; color: var(--color-accent);">{{ t('common.edit') }}</button>
    </div>

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 border-[#D97757] border-t-transparent rounded-full animate-spin" />
    </div>

    <div v-else-if="project" class="flex-1 overflow-y-auto">

      <!-- Hero — 严格对齐 screens.jsx ADetail line 297-315 (无白底卡片) -->
      <div class="px-7 pt-5 pb-6">

        <!-- 阶段彩点 + 标签 + auth code -->
        <div class="flex items-center gap-2 mb-3.5 flex-wrap">
          <span class="inline-flex items-center gap-1.5 text-[12px] font-medium"
            :style="{ color: stageColor, letterSpacing: '0.2px' }">
            <span class="w-[5px] h-[5px] rounded-[3px]" :style="{ background: stageColor }" />
            {{ project.stage_label }}
          </span>
          <span v-if="project.authorization_code" class="text-[11px]"
            style="color: var(--color-ink-3); letter-spacing: 0.5px;">· {{ project.authorization_code }}</span>
          <!-- 审批中（含老 authorization_status='pending' 兼容） → 点击弹流程 sheet -->
          <span v-else-if="project.has_pending_approval || project.authorization_status === 'pending'"
            class="text-[11px] px-2 py-0.5 rounded-full font-medium active:opacity-60 inline-flex items-center"
            style="color: #B45309; background: #FEF3C7; gap: 3px;"
            @click="loadAndShowFlow">
            {{ t('project.detSubmitted') }}
            <svg width="9" height="9" viewBox="0 0 12 12" fill="none">
              <path d="M3 4.5l3 3 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <span v-else-if="project.is_approval_rejected || project.authorization_status === 'rejected'"
            class="text-[11px] px-2 py-0.5 rounded-full font-medium active:opacity-60 inline-flex items-center"
            style="color: #DC2626; background: #FEE2E2; gap: 3px;"
            @click="loadAndShowFlow">
            {{ t('project.detRejectedTag') }}
            <svg width="9" height="9" viewBox="0 0 12 12" fill="none">
              <path d="M3 4.5l3 3 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <!-- 未提交状态：可申请人显示橙色按钮，无权人灰色提示 -->
          <button v-else-if="project.can_apply_auth"
            @click="showAuthModal = true" type="button"
            class="text-[11px] font-medium active:opacity-60"
            style="color: var(--color-accent); background: transparent; border: none; padding: 0;">
            {{ t('project.detSubmitBtn') }}
          </button>
          <span v-else class="text-[11px]"
            style="color: var(--color-ink-3);">{{ t('project.detNotSubmitted') }}</span>
        </div>

        <!-- 项目名 — 30px 衬线 weight 500 line-height 1.2 letter-spacing -0.3 -->
        <h1 class="font-serif m-0"
          :style="{
            fontSize: '30px',
            fontWeight: 500,
            lineHeight: '1.2',
            letterSpacing: '-0.3px',
            color: 'var(--color-ink)',
          }">{{ project.name }}</h1>

        <!-- Sub: owner · industry · city -->
        <div class="mt-3.5 text-[13px]" style="color: var(--color-ink-3);">
          {{ [project.owner_name, project.industry_label || project.industry, project.city].filter(Boolean).join(' · ') }}
        </div>

        <!-- Amount — backend-formatted per project's quotation_currency -->
        <div class="mt-7 flex items-baseline gap-2">
          <span class="font-serif font-medium tabular leading-none"
            :style="{ fontSize: '44px', color: 'var(--color-ink)' }">
            {{ project.amount_display || '—' }}
          </span>
          <span class="text-[14px]" style="color: var(--color-ink-3);">{{ t('project.detExpectedContract') }}</span>
        </div>
      </div>

      <!-- CTA row — 推进按钮 + 跟进按钮 -->
      <div class="px-5 pb-2 flex gap-2.5">
        <!-- 已签约 → 显示成功态；其余情况一律显示橙色推进按钮，无权时仅视觉禁用 -->
        <div v-if="project.current_stage === 'signed'"
          class="flex-1 h-12 rounded-2xl text-[15px] flex items-center justify-center"
          style="background: var(--color-card); color: var(--color-ink-3); border: 1px solid var(--color-divider);">
          {{ t('project.detSigned') }}
        </div>
        <button v-else type="button"
          @click="canAdvanceStage ? openStagePicker() : null"
          :disabled="!canAdvanceStage"
          class="flex-1 h-12 rounded-2xl text-white text-[15px] font-semibold active:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:opacity-50"
          style="background: var(--color-accent); border: none;">
          {{ t('project.detAdvanceTo', { stage: nextTrackStage?.label || t('project.detNextStage') }) }} →
        </button>
        <!-- 添加跟进快捷入口（与"跟进记录 +添加"等价） -->
        <button type="button" @click.stop="openNoteBox"
          class="h-12 px-3.5 rounded-2xl flex items-center gap-1.5 active:opacity-70 shrink-0"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <svg width="14" height="14" viewBox="0 0 18 18" fill="none" class="pointer-events-none">
            <path d="M9 2v14M2 9h14" stroke="var(--color-ink-2)"
              stroke-width="2" stroke-linecap="round" />
          </svg>
          <span class="text-[12px] pointer-events-none" style="color: var(--color-ink-2);">{{ t('project.detFollow') }}</span>
        </button>
      </div>

      <!-- 阶段 stepper — 严格对齐 screens.jsx ADetail line 333-355
           (5 dots + 4 thin lines · 无白底卡片 · current 14×14 accent · past 8×8 ink solid · future 8×8 transparent + 1.5px ink-3 ring) -->
      <div class="px-7 pt-5 pb-2">
        <div class="text-[11px] font-semibold uppercase mb-3"
          style="color: var(--color-ink-3); letter-spacing: 1px;">{{ t('project.detStage') }}</div>
        <!-- 横向可滚动: column 固定 64px, connector 固定 24px。
             英文 label 比中文长得多 (Embedding vs 植入), 用滚动避免 connector 被挤成噪点。 -->
        <div class="flex items-center overflow-x-auto no-scrollbar"
          style="gap: 4px; -webkit-overflow-scrolling: touch;">
          <template v-for="(s, i) in STAGE_TRACK" :key="s.key">
            <!-- dot + label column -->
            <div class="flex flex-col items-center" style="gap: 6px; width: 64px; flex: 0 0 64px;">
              <span :style="dotStyle(trackStatus(s.key))" />
              <span :style="[labelStyle(trackStatus(s.key)), { textAlign: 'center', lineHeight: 1.15, wordBreak: 'keep-all', whiteSpace: 'nowrap' }]">{{ s.label }}</span>
            </div>
            <!-- connector line — 固定 24px, 视觉清晰 -->
            <span v-if="i < STAGE_TRACK.length - 1"
              :style="{
                height: '1.5px',
                width: '24px',
                marginBottom: '16px',
                flex: '0 0 24px',
                background: trackStatus(STAGE_TRACK[i + 1].key) !== 'future'
                  ? 'var(--color-ink)'
                  : 'var(--color-divider)',
              }" />
          </template>
        </div>
      </div>

      <!-- 详情 def-list — 90px 1fr grid 对齐 ADetail line 358-366 -->
      <div class="px-7 pt-5">
        <div class="text-[11px] font-semibold uppercase mb-3"
          style="color: var(--color-ink-3); letter-spacing: 1px;">{{ t('project.detDetail') }}</div>
        <div class="grid text-[14px]"
          style="grid-template-columns: 90px 1fr; row-gap: 12px; column-gap: 16px;">
          <span style="color: var(--color-ink-3);">{{ t('project.detOwner') }}</span>
          <span>{{ project.owner_name || '—' }}</span>

          <span style="color: var(--color-ink-3);">{{ t('project.detActivity') }}</span>
          <span class="inline-flex items-center gap-1.5"
            :style="{ color: ACTIVITY_COLORS[project.activity_status] || 'var(--color-ink)', fontWeight: 600 }">
            <span class="w-[5px] h-[5px] rounded-[3px]"
              :style="{ background: ACTIVITY_COLORS[project.activity_status] || 'var(--color-ink-3)' }" />
            {{ project.activity_label || '—' }}
          </span>

          <template v-if="project.city || project.address">
            <span style="color: var(--color-ink-3);">{{ t('project.detAddress') }}</span>
            <span>{{ [project.city, project.address].filter(Boolean).join(' ') }}</span>
          </template>

          <template v-if="project.delivery_forecast">
            <span style="color: var(--color-ink-3);">{{ t('project.detDelivery') }}</span>
            <span class="tabular">{{ formatDelivery(project.delivery_forecast) }}</span>
          </template>

          <template v-if="project.project_type">
            <span style="color: var(--color-ink-3);">{{ t('project.detType') }}</span>
            <span>{{ project.project_type_label || project.project_type }}</span>
          </template>

          <template v-if="project.end_user">
            <span style="color: var(--color-ink-3);">{{ t('project.detEndUser') }}</span>
            <span>{{ project.end_user }}</span>
          </template>
        </div>
      </div>

      <!-- 主要联系人 — 单卡（首联系人）对齐 ADetail line 369-393 -->
      <div v-if="project.contacts?.length" class="px-7 pt-5">
        <div class="text-[11px] font-semibold uppercase mb-3"
          style="color: var(--color-ink-3); letter-spacing: 1px;">{{ t('project.detPrimaryContact') }}</div>
        <div class="rounded-2xl p-4 flex items-center gap-3.5"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <Avatar :text="project.contacts[0].name" :size="40" />
          <div class="flex-1 min-w-0">
            <div class="text-[15px] font-semibold truncate">{{ project.contacts[0].name }}</div>
            <div class="text-[12px] mt-0.5 truncate" style="color: var(--color-ink-3);">
              {{ [project.contacts[0].title || project.contacts[0].position, project.contacts[0].company_name].filter(Boolean).join(' · ') || '—' }}
            </div>
          </div>
          <button v-if="project.contacts[0].phone" @click="callPhone(project.contacts[0].phone)"
            class="w-9 h-9 rounded-full flex items-center justify-center active:opacity-70"
            style="background: transparent; border: 1px solid var(--color-divider);">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M3 2l2 3-1.5 1.5a8 8 0 004 4L9 9l3 2-1 2.5a1 1 0 01-1 .5C5.5 14 0 8.5 0 4a1 1 0 01.5-1L3 2z"
                fill="var(--color-ink-2)" />
            </svg>
          </button>
        </div>
      </div>

      <!-- 关联客户 -->
      <div class="px-7 pt-5">
        <div class="flex items-center justify-between mb-3">
          <div class="text-[11px] font-semibold uppercase"
            style="color: var(--color-ink-3); letter-spacing: 1px;">
            {{ t('project.detLinkedCustomer') }}<span v-if="project.customers?.length" style="opacity: 0.7;"> · {{ project.customers.length }}</span>
          </div>
          <button @click="customerPickerOpen = true"
            class="text-[12px] font-medium active:opacity-60"
            style="color: var(--color-accent);">
            + {{ t('project.detLinkedCustomerAdd') }}
          </button>
        </div>
        <div v-if="project.customers?.length" class="rounded-2xl overflow-hidden"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <SwipeRowAction v-for="(c, i) in project.customers" :key="c.association_id || c.id"
            :disabled="!c.can_remove"
            :actions="[{ label: t('common.delete'), color: 'red', handler: () => removeLinkedCustomer(c) }]">
            <button @click="router.push(`/customers/${c.id}`)"
              class="w-full px-4 py-3 flex items-center justify-between active:bg-bg"
              :style="i < project.customers.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
              <span class="text-[14px]" style="color: var(--color-ink);">{{ c.name }}</span>
              <svg width="7" height="11" viewBox="0 0 7 11" fill="none">
                <path d="M1 1l4 4.5L1 10" stroke="var(--color-ink-3)" stroke-width="1.4" stroke-linecap="round" />
              </svg>
            </button>
          </SwipeRowAction>
        </div>
        <div v-else class="text-center text-[13px] py-3" style="color: var(--color-ink-3);">
          {{ t('project.detLinkedCustomerEmpty') }}
        </div>
      </div>

      <!-- 报价单 -->
      <div class="px-7 pt-5">
        <div class="flex items-center justify-between mb-3">
          <div class="text-[11px] font-semibold uppercase"
            style="color: var(--color-ink-3); letter-spacing: 1px;">
            {{ t('project.detQuotation') }} <span v-if="project.quotation_count" style="opacity: 0.7;">· {{ project.quotation_count }}</span>
          </div>
          <button v-if="project.quotations?.length > 2"
            @click="showAllQuotations = !showAllQuotations"
            class="text-[12px] font-medium active:opacity-60"
            style="color: var(--color-accent);">
            {{ showAllQuotations ? t('project.detCollapse') : t('project.detExpand') }}
          </button>
        </div>
        <div v-if="project.quotations?.length" class="rounded-2xl overflow-hidden"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <div v-for="(q, i) in (showAllQuotations ? project.quotations : project.quotations.slice(0, 2))" :key="q.id"
            @click="openQuotation(q.id)"
            class="px-4 py-3 flex items-center justify-between cursor-pointer active:bg-bg"
            :style="i < (showAllQuotations ? project.quotations.length : Math.min(2, project.quotations.length)) - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
            <div class="min-w-0 flex-1">
              <div class="text-[14px] font-medium truncate"
                style="color: var(--color-accent);">{{ q.number }}</div>
              <div class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">{{ q.created_at }}</div>
            </div>
            <div class="text-right shrink-0">
              <div class="text-[14px] font-semibold tabular">{{ q.amount_display || '—' }}</div>
              <div class="text-[11px] mt-0.5"
                :style="{ color: q.status?.includes('approved') ? 'var(--color-green)' : q.status === 'pending' ? '#B45309' : 'var(--color-ink-3)' }">
                {{ q.status?.includes('approved') ? t('project.detQuotApproved') : q.status === 'pending' ? t('project.detQuotPending') : t('project.detQuotDraft') }}
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-[13px] py-3" style="color: var(--color-ink-3);">{{ t('project.detNoQuotation') }}</div>
      </div>

      <!-- 项目讨论预览卡 —— 对齐 chat-bridge.jsx ProjectDetailWithChat (line 50-87) -->
      <div class="px-7 pt-5">
        <div class="flex items-center justify-between mb-3">
          <div class="text-[11px] font-semibold uppercase"
            style="color: var(--color-ink-3); letter-spacing: 1px;">{{ t('project.detDiscussion') }}</div>
          <button v-if="hasGroup"
            @click="router.push({ path: `/messages/group/${realConvId}`, query: { name: project.name } })"
            class="text-[12px] font-medium active:opacity-60"
            style="color: var(--color-accent);">{{ t('project.detEnterDiscussion') }}</button>
        </div>

        <!-- 未建立讨论群：极简卡 + 创建入口 -->
        <div v-if="!hasGroup" class="rounded-2xl px-5 py-6 flex flex-col items-center gap-3"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <div class="w-10 h-10 rounded-2xl inline-flex items-center justify-center font-serif font-semibold text-[16px]"
            style="background: var(--color-accent-soft); color: var(--color-accent);">#</div>
          <div class="text-[13px] text-center" style="color: var(--color-ink-3);">
            {{ t('project.detNoDiscussion') }}<br />
            <span class="text-[11px]">{{ t('project.detNoDiscussionHint') }}</span>
          </div>
          <button @click="openCreateGroup"
            class="mt-1 px-5 py-2 rounded-full text-[13px] font-medium text-white active:opacity-80"
            style="background: var(--color-accent);">{{ t('project.detCreateDiscussion') }}</button>
        </div>

        <div v-else class="rounded-2xl relative"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <!-- 群头 -->
          <div class="px-4 py-3 flex items-center gap-3"
            style="border-bottom: 1px solid var(--color-divider);">
            <div class="w-9 h-9 rounded-xl inline-flex items-center justify-center font-serif font-semibold text-[15px]"
              style="background: var(--color-accent-soft); color: var(--color-accent);">
              {{ (project.name || '上')[0] }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-[14px] font-semibold">项目群 · {{ projectMembers.length }} 人</div>
              <div v-if="memberSummary" class="text-[11px] mt-0.5 truncate" style="color: var(--color-ink-3);">
                {{ memberSummary }}
              </div>
              <div v-else class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">
                {{ t('project.noMembers') }}
              </div>
            </div>
          </div>

          <!-- 最近消息预览（动态：发送后我的消息会插到顶部，含 @ token 着色 + 引用卡 + 阶段推进卡）-->
          <div class="px-4 pt-2">
            <template v-for="(m, i) in chatPreviewMessages" :key="i">
              <!-- 阶段推进卡（系统消息富卡，与 GroupChatView 复用同一个组件）-->
              <div v-if="m.kind === 'stage-advance'" class="py-2"
                :style="i < chatPreviewMessages.length - 1 ? 'border-bottom: 1px dashed var(--color-divider);' : ''">
                <StageAdvanceCard
                  :from-stage="m.fromStage" :to-stage="m.toStage"
                  :by-name="m.byName" :by-initial="m.byInitial"
                  :time="m.time" :note="m.note" />
              </div>

              <!-- 普通消息 / 我的消息 -->
              <div v-else class="py-2"
                :style="i < chatPreviewMessages.length - 1 ? 'border-bottom: 1px dashed var(--color-divider);' : ''">
                <div class="flex items-baseline gap-2">
                  <span class="text-[12px] font-semibold"
                    :style="{ color: m.from === '我' ? 'var(--color-accent)' : 'var(--color-ink-2)' }">{{ m.from }}</span>
                  <span class="text-[11px]" style="color: var(--color-ink-3);">{{ m.time }}</span>
                  <span v-if="m.mention === true" class="text-[10px] font-semibold px-1.5 py-px rounded"
                    style="color: var(--color-accent); background: var(--color-accent-bg);">@我</span>
                </div>
                <div class="text-[13px] mt-0.5"
                  :class="m.italic ? 'italic font-serif' : ''"
                  :style="{ color: m.italic ? 'var(--color-ink-3)' : 'var(--color-ink-2)', lineHeight: '1.4' }">
                  <MessageText :text="m.text" />
                </div>
                <MessageRefs v-if="m.refs?.length" :refs="m.refs" class="mt-2" />
              </div>
            </template>
          </div>

          <!-- 行内快速回复（含 @ 提及 popover + 待发引用卡预览）-->
          <div class="px-4 pt-2 pb-3 relative">
            <!-- @ 提及选择器（向上弹出） -->
            <MentionPopover
              :visible="chatMention.popoverVisible.value"
              :type="chatMention.popoverType.value"
              :query="chatMention.popoverQuery.value"
              :conv-id="realConvId"
              @select="handleChatMentionSelect"
              @switch-type="chatMention.switchType" />

            <!-- 待发引用卡预览 -->
            <PendingRefsPreview class="mb-2"
              :refs="chatMention.pendingRefs.value"
              @remove="chatMention.removeRef" />

            <div class="flex items-center gap-2">
              <div class="flex-1 h-9 rounded-full flex items-center gap-2 px-3.5"
                :style="{
                  background: 'var(--color-bg)',
                  border: (chatReplyText || chatMention.popoverVisible.value)
                    ? '1.5px solid var(--color-accent)'
                    : '1px solid var(--color-divider-strong)',
                }">
                <input ref="chatReplyInput" v-model="chatReplyText"
                  type="text"
                  placeholder="在群里说点什么…  @ 通知某人"
                  @input="handleChatInput"
                  @keyup.enter="sendChatReply"
                  :disabled="chatReplySending"
                  class="flex-1 bg-transparent outline-none font-serif text-[13px]"
                  style="color: var(--color-ink);" />
                <span class="text-[10px]" style="color: var(--color-ink-4); font-family: ui-monospace, monospace;">@</span>
              </div>
              <button v-if="chatReplyText.trim()"
                @click="sendChatReply" :disabled="chatReplySending"
                class="w-9 h-9 rounded-full inline-flex items-center justify-center text-[14px] font-bold text-white disabled:opacity-40"
                style="background: var(--color-accent);">↑</button>
              <button v-else
                @click="router.push({ path: `/messages/group/${realConvId}`, query: { name: project.name } })"
                class="w-9 h-9 rounded-full inline-flex items-center justify-center text-[14px] text-white"
                style="background: var(--color-ink);" title="进群">›</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 跟进记录 —— 严格对齐 customer-screens.jsx 时间轴样式
           (左 2px 竖线: 首条 accent / 其他 divider · serif 16px · tabular 日期) -->
      <div class="px-7 pt-5 pb-10">
        <div class="flex items-center justify-between mb-3">
          <div class="text-[11px] font-semibold uppercase"
            style="color: var(--color-ink-3); letter-spacing: 1px;">{{ t('project.followLog') }}</div>
          <button @click="openNoteBox"
            class="text-[12px] font-medium active:opacity-60"
            style="color: var(--color-accent);">{{ t('project.followAdd') }}</button>
        </div>
        <div v-if="project.actions?.length">
          <div v-for="(a, i) in project.actions" :key="a.id"
            class="pl-3.5"
            :style="{
              borderLeft: '2px solid ' + (i === 0 ? 'var(--color-accent)' : 'var(--color-divider)'),
              marginTop: i ? '16px' : '0',
            }">
            <div class="text-[11px] tabular mb-1" style="color: var(--color-ink-3);">
              {{ a.date }} — {{ a.owner_name }}
            </div>
            <div :style="{
                fontSize: '14px',
                lineHeight: '1.5',
                color: i === 0 ? 'var(--color-ink)' : 'var(--color-ink-2)',
                fontFamily: 'var(--font-sans)',
              }">
              {{ a.communication }}
            </div>
          </div>
        </div>
        <div v-else class="text-center text-[13px] py-4" style="color: var(--color-ink-3);">{{ t('project.noFollow') }}</div>
      </div>
    </div>

    <!-- ── Stage picker bottom sheet ── -->
    <Teleport to="body">
      <Transition name="sheet">
        <div v-if="showStagePicker" class="fixed inset-0 z-50 flex flex-col justify-end">
          <div class="absolute inset-0 bg-black/40" @click="showStagePicker = false" />
          <div class="relative bg-[#F7F5F2] rounded-t-3xl"
            :style="{ paddingBottom: 'calc(24px + env(safe-area-inset-bottom))' }">
            <div class="w-10 h-1 bg-[#D0CBC4] rounded-full mx-auto mt-3 mb-4" />
            <div class="px-5 mb-3">
              <p class="text-[12px] text-[#9CA3AF] font-medium mb-1">{{ t('project.stageAdvanceEyebrow') }}</p>
              <p class="font-serif text-[22px] font-bold text-[#1A1A1A]">
                {{ t('project.fromStageTo', { stage: project?.stage_label }) }}
              </p>
            </div>
            <!-- Stage list -->
            <div class="px-4 space-y-2 max-h-[52vh] overflow-y-auto pb-1">
              <button v-for="s in STAGES_ALL" :key="s.key"
                :disabled="pickerStatus(s.key) === 'past'"
                @click="pickerStatus(s.key) !== 'past' && s.key !== project?.current_stage ? selectedStage = s.key : null"
                class="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-left transition-all"
                :class="{
                  'bg-white border-2 border-[#D97757]': selectedStage === s.key,
                  'bg-white border border-[#F0EDE9]':  selectedStage !== s.key && pickerStatus(s.key) !== 'past',
                  'bg-[#F7F5F2] border border-[#F0EDE9] opacity-40': pickerStatus(s.key) === 'past',
                }">
                <!-- Circle icon -->
                <div class="w-6 h-6 rounded-full flex items-center justify-center shrink-0 border-2"
                  :class="{
                    'bg-[#D97757] border-[#D97757]':    selectedStage === s.key,
                    'bg-[#F4E4D8] border-[#D97757]':    pickerStatus(s.key) === 'past',
                    'border-[#D0CBC4]':                  pickerStatus(s.key) !== 'past' && selectedStage !== s.key,
                  }">
                  <svg v-if="pickerStatus(s.key) === 'past' || selectedStage === s.key"
                    class="w-3 h-3"
                    :class="selectedStage === s.key ? 'text-white' : 'text-[#D97757]'"
                    fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <!-- Text -->
                <div class="flex-1 min-w-0">
                  <p class="text-[14px] font-semibold text-[#1A1A1A]">{{ s.label }}</p>
                  <p class="text-[12px] text-[#9CA3AF]">{{ s.desc }}</p>
                </div>
                <!-- Percentage -->
                <span class="text-[13px] text-[#C2BBB3] shrink-0">{{ s.pct }}%</span>
              </button>
            </div>
            <!-- Confirm -->
            <div class="px-4 mt-4">
              <button @click="confirmStageUpdate" :disabled="!selectedStage || updatingStage"
                class="w-full py-4 rounded-2xl text-white text-[16px] font-semibold disabled:opacity-40 active:opacity-80"
                style="background:#D97757">
                {{ updatingStage
                  ? t('project.advancing')
                  : selectedStage
                    ? t('project.advanceTo', { stage: STAGES_ALL.find(s => s.key === selectedStage)?.label })
                    : t('project.pickTargetStage') }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Note box bottom sheet（公用组件，与 CustomerDetailView 共用） ── -->
    <NoteSheet v-model="showNoteBox" :submit="submitNote" />

    <!-- Customer picker for linking a company to this project (opened by the Add button in the customers section header) -->
    <ExSearchPickerSheet v-model="customerPickerOpen"
      :title="t('project.detLinkedCustomerPickTitle')"
      :placeholder="t('project.detLinkedCustomerPickPh')"
      :search-fn="searchCompaniesForLink"
      @pick="pickCompanyForLink" />


    <!-- 项目提交审批确认 sheet -->
    <ProjectSubmitSheet
      v-model="showAuthModal"
      :project-name="project ? project.name : ''"
      :project-type="project ? project.project_type : ''"
      :customer-name="project ? project.end_user : ''"
      :owner-name="project ? project.owner_name : ''"
      :amount="project ? (project.amount_display || '') : ''"
      :stage="project ? project.stage_label : ''"
      :submitting="submittingAuth"
      @confirm="submitAuthRequest"
    />

    <!-- 创建讨论群 sheet（多选成员）-->
    <Teleport to="body">
      <Transition name="cg">
        <div v-if="showCreateGroupSheet" class="fixed inset-0 z-50 flex flex-col"
          style="background: rgba(0,0,0,0.32);" @click.self="closeCreateGroup">
          <div class="mt-auto rounded-t-3xl flex flex-col"
            style="background: var(--color-bg); max-height: 88vh; min-height: 60vh;">
            <!-- header -->
            <div class="px-5 pt-4 pb-2 flex items-center justify-between shrink-0">
              <button @click="closeCreateGroup" class="text-[13px]"
                style="color: var(--color-ink-3);">取消</button>
              <span class="font-serif" style="font-size: 16px; font-weight: 500;">创建讨论群</span>
              <button @click="confirmCreateGroup"
                :disabled="cgSelected.length < 1 || cgCreating"
                class="text-[13px] font-medium disabled:opacity-40"
                style="color: var(--color-accent);">
                {{ cgCreating ? '创建中…' : `创建${cgSelected.length ? `(${cgSelected.length})` : ''}` }}
              </button>
            </div>

            <!-- 已选 chips -->
            <div v-if="cgSelected.length" class="px-5 pb-2 flex flex-wrap gap-1.5 shrink-0">
              <span v-for="u in cgSelected" :key="u.id"
                class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[12px]"
                style="background: var(--color-accent-soft); color: var(--color-accent);">
                {{ u.name }}
                <button @click="toggleCgSelect(u)"
                  class="ml-0.5 text-[14px] leading-none active:opacity-60">×</button>
              </span>
            </div>

            <!-- search -->
            <div class="px-5 pb-3 shrink-0">
              <input v-model="cgSearch" @input="onCgSearchInput"
                type="text" placeholder="搜索姓名 / 部门"
                class="w-full px-4 py-2.5 rounded-xl text-[14px]"
                style="background: var(--color-card); border: 1px solid var(--color-divider); outline: none;" />
            </div>

            <!-- list -->
            <div class="flex-1 overflow-y-auto px-3 pb-6">
              <div v-if="cgSearching" class="flex justify-center py-6">
                <div class="w-5 h-5 border-2 rounded-full animate-spin"
                  style="border-color: var(--color-accent); border-top-color: transparent;" />
              </div>
              <div v-else-if="!cgResults.length" class="text-center py-8 text-[13px]"
                style="color: var(--color-ink-3);">
                {{ cgSearch ? t('project.noMatchUsers') : t('project.noSelectableUsers') }}
              </div>
              <button v-else v-for="u in cgResults" :key="u.id"
                @click="toggleCgSelect(u)"
                class="w-full flex items-center gap-3 px-3 py-3 active:bg-bg text-left rounded-xl">
                <div class="w-9 h-9 rounded-full inline-flex items-center justify-center font-serif text-[13px] font-semibold"
                  style="background: var(--color-accent-soft); color: var(--color-accent);">{{ u.avatar || u.name?.[0] || '?' }}</div>
                <div class="flex-1 min-w-0">
                  <div class="font-serif truncate" style="font-size: 14px; font-weight: 500;">{{ u.name }}</div>
                  <div v-if="u.dept" class="text-[11px] truncate" style="color: var(--color-ink-3);">{{ u.dept }}</div>
                </div>
                <div class="w-5 h-5 rounded-full inline-flex items-center justify-center text-[11px] text-white"
                  :style="{
                    background: isCgSelected(u) ? 'var(--color-accent)' : 'transparent',
                    border: isCgSelected(u) ? 'none' : '1.5px solid var(--color-divider-strong)',
                  }">
                  <span v-if="isCgSelected(u)">✓</span>
                </div>
              </button>
            </div>

            <!-- footer 提示：至少 1 人 -->
            <div v-if="cgSelected.length < 1" class="px-5 pb-4 text-center text-[11px] shrink-0"
              style="color: var(--color-ink-3);">
              至少选择 1 名成员才能创建讨论群
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 审批流程 sheet (授权 chip 点击触发) -->
    <ExFlowSheet v-model="flowSheetOpen" :nodes="flowNodes" :empty-hint="flowLoadError"
      @recall="flowSheetOpen = false; openRecall()" />

    <!-- 召回确认 sheet -->
    <ExConfirmSheet
      v-model="recallSheetOpen"
      eyebrow="召回"
      title="确认召回此项目?"
      :sub="project ? project.name : ''"
      confirm-label="确认召回"
      color="warn"
      :submitting="recalling"
      @confirm="confirmRecall"
    />
  </div>
</template>

<style scoped>
.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.2s ease;
}
.sheet-enter-active .relative,
.sheet-leave-active .relative {
  transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
}
.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}
.sheet-enter-from .relative,
.sheet-leave-to .relative {
  transform: translateY(100%);
}
</style>
