<script setup>
// 会话列表 — 严格本区 (Federation Lite v2 简化方案)
// 不再合并对区会话; 对区有未读时, 顶部琥珀卡提示, 点卡片切到对区即可
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import PixelP from '@/components/common/PixelP.vue'
import CrossRegionMsgCard from '@/components/common/CrossRegionMsgCard.vue'
import { getConversations, getUnreadCountForRegion, createConversation, searchUsers, searchProjects } from '@/api/chat'
import client from '@/api/client'
import SwipeRowAction from '@/components/common/SwipeRowAction.vue'
import { REGIONS } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'
import { formatChatTime } from '@/utils/chatTime'

const router = useRouter()
const auth = useAuthStore()
const { t } = useI18n()
const { kbOffset } = useKeyboardOffset()
const showPicker = ref(false)
const loading = ref(true)
const allConversations = ref([])

// 对区未读数 (用于顶部琥珀卡)
const peerUnread = ref(0)
const peerRegionId = computed(() => auth.regionId === 'cn' ? 'sg' : 'cn')
const peerRegion = computed(() => REGIONS[peerRegionId.value])
const showPeerCard = computed(() => !!auth.tokens[peerRegionId.value] && peerUnread.value > 0)

// 把后端 conversation 映射为 UI 行
function mapConv(c) {
  // 后端 type: 'private' / 'group' / 'ai'
  let kind = c.type === 'private' ? 'dm' : c.type === 'ai' ? 'ai' : 'group'
  const name = c.display_name || c.name || c.topic || t('chat.unnamed')
  // DM 场景: 取对方 participant 的 department 作为副标
  let peerDept = ''
  if (kind === 'dm' && Array.isArray(c.participants)) {
    const other = c.participants.find(p => p.user_name === name) || c.participants.find(p => p.user_id !== c.current_user_id)
    peerDept = other?.department || ''
  }
  return {
    id: c.id,
    kind,
    type: c.type,
    name,
    initial: name[0] || '?',
    peerDept,
    last: c.last_message?.content || '',
    time: c.last_message ? formatChatTime(c.last_message.created_at) : '',
    unread: c.unread_count || 0,
    pinned: false,
    ai: c.type !== 'ai' && c.has_ai,
    draft: c.has_draft,
  }
}

// 拆 AI 顶置卡 vs 普通会话
const aiConv = computed(() => allConversations.value.find(c => c.kind === 'ai'))
const conversations = computed(() => allConversations.value.filter(c => c.kind !== 'ai'))
const aiPreview = computed(() => aiConv.value
  ? { text: aiConv.value.last || t('chat.aiPreviewDefault'), time: aiConv.value.time }
  : { text: t('chat.aiPreviewDefault'), time: '' })

async function load() {
  loading.value = true
  try {
    const hasPeer = !!auth.tokens[peerRegionId.value]
    // 并行: 本区会话 + 对区未读总数 (只用于决定琥珀卡)
    const [localRes, peerUnreadRes] = await Promise.all([
      getConversations(),
      hasPeer ? getUnreadCountForRegion(peerRegionId.value) : Promise.resolve({ data: { data: { total_unread: 0 } } }),
    ])
    const localList = (localRes.data?.success ? localRes.data.data : []) || []
    allConversations.value = localList.map(mapConv)
    peerUnread.value = peerUnreadRes.data?.data?.total_unread || 0
  } catch (e) {
    console.error('load conversations failed', e)
    allConversations.value = []
    peerUnread.value = 0
  } finally {
    loading.value = false
  }
}

// 点琥珀卡 → 切到对区, 重载让 ChatListView 重新挂载并加载对区列表
// Capacitor WebView 下 router.go(0) 是 no-op, 用 location.reload 真刷新
function gotoPeerRegion() {
  if (auth.switchRegion(peerRegionId.value)) {
    window.location.reload()
  }
}

// 简单 30s 轮询刷新（未读+新消息），后续可换 SSE / WebSocket
let pollTimer = null
onMounted(() => {
  load()
  pollTimer = setInterval(load, 30000)
})
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })

function openAi() {
  // 如果有现成 AI 会话则带 id 进入；否则进 AI 页时由后端自动建一个
  router.push({ path: '/messages/ai', query: aiConv.value ? { id: aiConv.value.id } : {} })
}

// 滑动列表时收起键盘, 避免被键盘遮挡
function dismissKeyboard() {
  const el = document.activeElement
  if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA')) {
    el.blur()
  }
}

// 从列表移出 (仅自己列表隐藏 — 对方再发消息会自动 unhide 重新出现)
async function onHideConversation(c) {
  try {
    await client.delete(`/mobile/chat/conversations/${c.id}`)
    // 立即从本地列表移除, 体感顺滑
    allConversations.value = allConversations.value.filter(x => x.id !== c.id)
  } catch (e) {
    alert(e.response?.data?.message || t('chat.hideFail'))
  }
}

function openConversation(c) {
  // 公司广播 → 公告列表
  if (c.kind === 'broadcast') {
    router.push('/messages/broadcast')
    return
  }
  // 项目群 → GroupChatView
  if (c.kind === 'group') {
    router.push({ path: `/messages/group/${c.id}`, query: { name: c.name } })
    return
  }
  // 私聊 → DmChatView，把对方部门一起带过去
  if (c.kind === 'dm') {
    router.push({
      path: `/messages/dm/${c.id}`,
      query: { name: c.name, role: c.peerDept || '' },
    })
  }
}

// 选择器步骤：'main'（三选一）/ 'dm'（选联系人）/ 'group'（选项目）
const pickerStep = ref('main')
const pickerSearch = ref('')
const pickerResults = ref([])         // group/project step 用 (后端搜)
const allDmUsers = ref([])            // dm step 一次拉全员, 后续本地过滤
const pickerSearching = ref(false)
const pickerCreating = ref(false)
// Vue 3 reactive 支持 Set 的 add/delete 触发更新; ref(new Set()) 不触发
const expandedCompanies = reactive(new Set())
const expandedDepts = reactive(new Set())

// 本地过滤 — 替代后端搜索, 避免中文 IME debounce 竞态
const filteredDmUsers = computed(() => {
  const q = pickerSearch.value.trim().toLowerCase()
  if (!q) return allDmUsers.value
  return allDmUsers.value.filter(u =>
    (u.name || '').toLowerCase().includes(q) ||
    (u.username || '').toLowerCase().includes(q) ||
    (u.dept || '').toLowerCase().includes(q) ||
    (u.company_name || '').toLowerCase().includes(q)
  )
})

// 是否在搜索状态(q 非空)
const isSearching = computed(() => !!pickerSearch.value.trim())

// 搜索状态: 直接平铺命中的人员, 不再分组(避免 IME 期间 watch + reactive Set
// 触发渲染递归导致 iOS WebView 卡死)
const flatSearchResults = computed(() =>
  isSearching.value ? filteredDmUsers.value.slice(0, 50) : []
)

// 非搜索状态: 公司 → 部门 → 人员 三级树; 自己公司排最前
const dmTree = computed(() => {
  if (pickerStep.value !== 'dm' || isSearching.value) return []
  const me = auth.user
  const myCompany = me?.company_name || ''
  const companies = new Map()
  for (const u of allDmUsers.value) {
    const c = u.company_name || t('chat.unspecifiedCompany')
    const d = u.dept || t('chat.unspecifiedDept')
    if (!companies.has(c)) companies.set(c, { name: c, depts: new Map(), total: 0 })
    const co = companies.get(c)
    if (!co.depts.has(d)) co.depts.set(d, { name: d, users: [] })
    co.depts.get(d).users.push(u)
    co.total++
  }
  return [...companies.values()]
    .sort((a, b) => {
      if (a.name === myCompany) return -1
      if (b.name === myCompany) return 1
      return a.name.localeCompare(b.name, 'zh')
    })
    .map(co => ({
      name: co.name,
      total: co.total,
      depts: [...co.depts.values()].sort((a, b) => a.name.localeCompare(b.name, 'zh')),
    }))
})

function toggleCompany(name) {
  if (expandedCompanies.has(name)) expandedCompanies.delete(name)
  else expandedCompanies.add(name)
}
function toggleDept(companyName, deptName) {
  const key = `${companyName}|${deptName}`
  if (expandedDepts.has(key)) expandedDepts.delete(key)
  else expandedDepts.add(key)
}

function pickStart(kind) {
  if (kind === 'ai') {
    showPicker.value = false
    openAi()
    return
  }
  pickerStep.value = kind
  pickerSearch.value = ''
  pickerResults.value = []
  if (kind === 'dm') {
    loadAllUsers()
  } else {
    doPickerSearch()
  }
}

// 一次拉全员 (后端已过滤 is_active=True 且最多 500), 后续本地实时过滤
// 避开了中文 IME composition 与 debounce 的竞态(原方案 2 字符以上不匹配)
async function loadAllUsers() {
  pickerSearching.value = true
  try {
    const r = await searchUsers('')
    allDmUsers.value = r.data?.success ? (r.data.data || []) : []
    // 默认展开当前用户的公司 + 部门
    const me = auth.user
    if (me?.company_name) expandedCompanies.add(me.company_name)
    if (me?.company_name && me?.department) expandedDepts.add(`${me.company_name}|${me.department}`)
  } catch (e) {
    console.error('load users failed', e)
    allDmUsers.value = []
  } finally {
    pickerSearching.value = false
  }
}

let pickerSearchTimer = null
async function doPickerSearch() {
  if (pickerSearchTimer) clearTimeout(pickerSearchTimer)
  pickerSearchTimer = setTimeout(async () => {
    pickerSearching.value = true
    try {
      const q = pickerSearch.value.trim()
      if (pickerStep.value === 'dm') {
        const r = await searchUsers(q)
        pickerResults.value = r.data?.success ? (r.data.data || []) : []
      } else if (pickerStep.value === 'group') {
        const r = await searchProjects(q)
        pickerResults.value = r.data?.success ? (r.data.data || []) : []
      }
    } catch (e) {
      console.error('picker search failed', e)
      pickerResults.value = []
    } finally {
      pickerSearching.value = false
    }
  }, 250)
}

async function pickResult(item) {
  if (pickerCreating.value) return
  pickerCreating.value = true
  try {
    if (pickerStep.value === 'dm') {
      // 创建私聊（type='private'，1 对 1）
      const r = await createConversation({ type: 'private', participant_ids: [item.id] })
      const data = r.data
      if (data?.success && data?.data?.id) {
        showPicker.value = false
        pickerStep.value = 'main'
        await load()  // 刷新列表
        router.push({
          path: `/messages/dm/${data.data.id}`,
          query: { name: item.name, role: item.dept || '' },
        })
      } else {
        alert(data?.message || t('chat.createDmFail'))
      }
    } else if (pickerStep.value === 'group') {
      // 创建项目群（type='group'，名字用项目名，仅创建人；后续可在群设置加成员）
      // sync_metadata.project_id 让后端知道这是项目群，
      // 之后加成员时会自动把项目共享给新成员
      const r = await createConversation({
        type: 'group',
        name: item.project_name,
        participant_ids: [],
        sync_metadata: { project_id: item.id },
      })
      const data = r.data
      if (data?.success && data?.data?.id) {
        showPicker.value = false
        pickerStep.value = 'main'
        await load()
        router.push({
          path: `/messages/group/${data.data.id}`,
          query: { name: item.project_name },
        })
      } else {
        alert(data?.message || t('chat.createGroupFail'))
      }
    }
  } catch (e) {
    console.error('create conversation failed', e)
    alert(`${t('chat.createFail')}${e.message || e}`)
  } finally {
    pickerCreating.value = false
  }
}

function backToPickerMain() {
  pickerStep.value = 'main'
  pickerSearch.value = ''
  pickerResults.value = []
}

function closePicker() {
  showPicker.value = false
  pickerStep.value = 'main'
}

function openPicker() {
  showPicker.value = true
}

// ─── DIAG: + 按钮触摸/点击诊断（临时） ─────────────────────────
const dbg = ref({ click: 0, touchStart: 0, touchEnd: 0, pointerDown: 0, openCalls: 0, lastEvt: '', lastTarget: '', topAtPoint: '' })
function _evtTag(e) {
  const t = e.target
  if (!t) return ''
  return `${t.tagName}.${(t.className || '').toString().slice(0, 30)}`
}
function _topAt(x, y) {
  const el = document.elementFromPoint(x, y)
  if (!el) return '(none)'
  return `${el.tagName}.${(el.className || '').toString().slice(0, 40)}`
}
function onPlusClick(e) {
  dbg.value.click++
  dbg.value.lastEvt = 'click'
  dbg.value.lastTarget = _evtTag(e)
  dbg.value.openCalls++
  showPicker.value = true
}
function onPlusTouchStart(e) {
  dbg.value.touchStart++
  dbg.value.lastEvt = 'touchstart'
  dbg.value.lastTarget = _evtTag(e)
  const t = e.touches?.[0]
  if (t) dbg.value.topAtPoint = _topAt(t.clientX, t.clientY)
}
function onPlusTouchEnd(e) {
  dbg.value.touchEnd++
  dbg.value.lastEvt = 'touchend'
  dbg.value.lastTarget = _evtTag(e)
}
function onPlusPointerDown(e) {
  dbg.value.pointerDown++
  dbg.value.lastEvt = 'pointerdown'
  dbg.value.lastTarget = _evtTag(e)
}
</script>

<template>
  <div class="flex flex-col h-full" style="background: var(--color-bg);">

    <!-- DIAG 浮标（临时）— 排查 + 按钮无响应 -->
    <div
      style="position: fixed; top: 60px; left: 8px; right: 8px; z-index: 9999;
             background: rgba(0,0,0,0.85); color: #0F0; font-size: 10px;
             font-family: ui-monospace, monospace; padding: 6px 8px;
             border-radius: 6px; line-height: 1.45; pointer-events: none;">
      <div>click={{ dbg.click }} touchStart={{ dbg.touchStart }} touchEnd={{ dbg.touchEnd }} pointerDown={{ dbg.pointerDown }}</div>
      <div>openCalls={{ dbg.openCalls }} showPicker={{ showPicker }} lastEvt={{ dbg.lastEvt }}</div>
      <div style="color: #FFC;">target={{ dbg.lastTarget }}</div>
      <div style="color: #FFC;">topAtPoint={{ dbg.topAtPoint }}</div>
    </div>


    <!-- PageHead -->
    <div class="px-6 pt-3.5 pb-2 flex items-start justify-between shrink-0">
      <div>
        <div class="text-[11px] font-medium uppercase"
          style="color: var(--color-ink-3); letter-spacing: 1.2px;">{{ t('chat.eyebrow') }}</div>
        <h1 class="font-serif m-0 mt-1"
          style="font-size: 30px; font-weight: 500; letter-spacing: -0.4px; color: var(--color-ink);">{{ t('chat.title') }}</h1>
      </div>
      <button
        @click="onPlusClick"
        @touchstart="onPlusTouchStart"
        @touchend="onPlusTouchEnd"
        @pointerdown="onPlusPointerDown"
        type="button"
        class="w-9 h-9 rounded-full inline-flex items-center justify-center"
        style="background: var(--color-ink); color: #fff; font-size: 20px; font-weight: 300;">+</button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading && !allConversations.length" class="flex justify-center items-center py-10">
      <div class="w-6 h-6 border-2 rounded-full animate-spin"
        style="border-color: var(--color-accent); border-top-color: transparent;" />
    </div>

    <div v-else class="flex-1 overflow-y-auto pb-4">
      <!-- 跨区域提示卡: 对区有未读时显示, 点击切到对区 -->
      <CrossRegionMsgCard v-if="showPeerCard"
        :region-flag="peerRegion.flag"
        :region-label="peerRegion.label"
        :unread-count="peerUnread"
        @goto="gotoPeerRegion" />

      <!-- AI 助手置顶卡 (设计 line 474-492) -->
      <div class="px-4 pt-2 pb-1">
        <button @click="openAi"
          class="w-full rounded-2xl p-3.5 flex gap-3 items-center active:opacity-80 text-left"
          style="background: linear-gradient(135deg, rgba(47,102,214,0.06) 0%, rgba(26,180,200,0.07) 100%); border: 1px solid rgba(47,102,214,0.25);">
          <PixelP :size="34" />
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5">
              <span class="font-serif" style="font-size: 15px; font-weight: 600; color: var(--color-ink);">{{ t('chat.aiAssistant') }}</span>
              <span class="text-[9px] font-bold px-1.5 py-px rounded"
                style="color: #2F66D6; background: #E5EEFB; letter-spacing: 0.5px;">{{ t('chat.aiBeta') }}</span>
              <span class="text-[11px] ml-auto" style="color: var(--color-ink-3);">{{ aiPreview.time }}</span>
            </div>
            <div class="text-[12px] mt-1 font-serif truncate"
              style="color: var(--color-ink-2); line-height: 1.4;">
              {{ aiPreview.text }}
            </div>
          </div>
        </button>
      </div>

      <!-- 普通会话 (左滑「移出」: 仅自己列表隐藏, 对方再发消息会自动重现) -->
      <div class="mt-2" style="background: var(--color-card);">
        <SwipeRowAction
          v-for="(c, i) in conversations" :key="c.id"
          :actions="[{ label: t('chat.hideFromList'), color: 'red', handler: () => onHideConversation(c) }]">
        <button @click="openConversation(c)"
          class="w-full px-4 py-3.5 flex gap-3 active:bg-bg text-left"
          :style="{
            background: 'var(--color-card)',
            borderBottom: i < conversations.length - 1 ? '1px solid var(--color-divider)' : 'none',
          }">
          <!-- 头像（广播=方形 + ink；其他=圆形 + accent-soft）-->
          <div class="w-[42px] h-[42px] inline-flex items-center justify-center font-serif font-semibold shrink-0"
            :style="{
              borderRadius: c.kind === 'broadcast' ? '14px' : '21px',
              background: c.kind === 'broadcast' ? 'var(--color-ink)' : 'var(--color-accent-soft)',
              color: c.kind === 'broadcast' ? '#fff' : 'var(--color-accent)',
              fontSize: '16px',
            }">{{ c.initial }}</div>

          <div class="flex-1 min-w-0">
            <div class="flex items-baseline justify-between">
              <div class="font-serif flex items-center gap-1.5"
                style="font-size: 15px; font-weight: 500; color: var(--color-ink);">
                <span v-if="c.pinned" style="color: var(--color-accent);">★</span>{{ c.name }}
                <span v-if="c.ai" class="text-[9px] font-bold px-1.5 py-px rounded"
                  style="color: #2F66D6; background: #E5EEFB;">AI</span>
              </div>
              <span class="text-[11px]" style="color: var(--color-ink-3);">{{ c.time }}</span>
            </div>
            <div class="flex items-baseline justify-between mt-0.5 gap-2">
              <span class="text-[12px] truncate flex-1"
                style="color: var(--color-ink-3);">
                <span v-if="c.draft" style="color: #2F66D6; font-weight: 600;">{{ t('chat.aiDraftPrefix') }}</span>{{ c.last }}
              </span>
              <span v-if="c.unread > 0"
                class="text-[10px] font-bold tabular px-2 py-0.5 rounded-full text-white shrink-0"
                style="background: var(--color-accent);">{{ c.unread }}</span>
            </div>
          </div>
        </button>
        </SwipeRowAction>
      </div>
    </div>

    <!-- 发起聊天 sheet -->
    <Transition name="sheet">
      <div v-if="showPicker" class="absolute inset-0 z-40">
        <!-- 遮罩点击关闭 sheet -->
        <div class="absolute inset-0 bg-black/40" @click="closePicker" />
        <!-- panel: bottom 跟随键盘抬升, max-h 减去键盘, 避免被键盘挤压
             @click.stop 防止 panel 内点击冒泡到遮罩误触发 closePicker -->
        <div class="absolute left-0 right-0 rounded-t-3xl pt-3 pb-8 overflow-y-auto"
          @click.stop
          :style="{
            background: 'var(--color-bg)',
            bottom: kbOffset + 'px',
            maxHeight: `calc(85vh - ${kbOffset}px)`,
            transition: 'bottom 0.2s ease, max-height 0.2s ease',
          }">
          <div class="mx-auto w-9 h-1 rounded-full mb-3" style="background: rgba(0,0,0,0.15);" />

          <div class="flex items-center justify-between px-5 mb-2">
            <button v-if="pickerStep === 'main'" @click="closePicker" class="text-[15px]"
              style="color: var(--color-accent);">{{ t('common.cancel') }}</button>
            <button v-else @click="backToPickerMain" class="text-[15px] inline-flex items-center gap-1"
              style="color: var(--color-accent);">
              <svg width="9" height="14" viewBox="0 0 9 14"><path d="M7 1L1 7l6 6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
              {{ t('common.back') }}
            </button>
            <span class="font-serif text-[16px] font-medium">{{
              pickerStep === 'dm' ? t('chat.selectContact') : pickerStep === 'group' ? t('chat.selectProject') : t('chat.startChat')
            }}</span>
            <span class="w-[30px]" />
          </div>

          <!-- ─── Step: dm 选联系人 (三级 公司 → 部门 → 人员) ─── -->
          <template v-if="pickerStep === 'dm'">
            <div class="px-5 mt-3">
              <div class="rounded-full h-10 flex items-center px-4 gap-2"
                style="background: var(--color-card); border: 1px solid var(--color-divider-strong);">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <circle cx="7" cy="7" r="5" stroke="var(--color-ink-3)" stroke-width="1.4"/>
                  <path d="M11 11l3 3" stroke="var(--color-ink-3)" stroke-width="1.4" stroke-linecap="round"/>
                </svg>
                <input v-model="pickerSearch" type="search"
                  :placeholder="t('chat.searchContact')"
                  class="flex-1 bg-transparent outline-none text-[14px] font-serif"
                  style="color: var(--color-ink);" />
              </div>
            </div>
            <!-- 列表 — 滑动收键盘, 避免遮挡 -->
            <div class="px-5 mt-3" @touchmove="dismissKeyboard">
              <div v-if="pickerSearching" class="text-center py-6 text-[13px]"
                style="color: var(--color-ink-3);">{{ t('chat.pickerLoading') }}</div>
              <!-- 搜索态: 平铺命中结果 (避免树+reactive Set 在 IME 期间卡死) -->
              <template v-else-if="isSearching">
                <div v-if="!flatSearchResults.length" class="text-center py-6 text-[13px]"
                  style="color: var(--color-ink-3);">{{ t('chat.noMatch') }}</div>
                <div v-else class="rounded-2xl overflow-hidden"
                  style="background: var(--color-card); border: 1px solid var(--color-divider);">
                  <button v-for="(u, i) in flatSearchResults" :key="u.id" @click="pickResult(u)"
                    class="w-full px-4 py-3 flex items-center gap-3 active:bg-bg text-left"
                    :style="i < flatSearchResults.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''"
                    :disabled="pickerCreating">
                    <div class="w-9 h-9 rounded-full inline-flex items-center justify-center font-serif text-[14px] font-semibold shrink-0"
                      style="background: var(--color-accent-soft); color: var(--color-accent);">{{ u.avatar || u.name?.[0] || '?' }}</div>
                    <div class="flex-1 min-w-0">
                      <div class="font-serif text-[15px] font-medium">{{ u.name }}</div>
                      <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">
                        {{ [u.company_name, u.dept].filter(Boolean).join(' · ') || '—' }}
                      </div>
                    </div>
                    <span class="text-[16px]" style="color: var(--color-ink-3);">›</span>
                  </button>
                </div>
              </template>
              <!-- 非搜索态: 树形分组 -->
              <div v-else-if="!dmTree.length" class="text-center py-6 text-[13px]"
                style="color: var(--color-ink-3);">{{ t('chat.noColleagues') }}</div>
              <div v-else class="rounded-2xl overflow-hidden"
                style="background: var(--color-card); border: 1px solid var(--color-divider);">
                <template v-for="(co, ci) in dmTree" :key="co.name">
                  <!-- 公司行 (Level 1) -->
                  <button @click="toggleCompany(co.name)"
                    class="w-full px-4 py-3 flex items-center gap-2 active:bg-bg text-left"
                    :style="(ci > 0 ? 'border-top: 1px solid var(--color-divider);' : '')">
                    <span class="inline-block transition-transform" :style="{
                      transform: expandedCompanies.has(co.name) ? 'rotate(90deg)' : 'rotate(0)',
                      color: 'var(--color-ink-3)',
                      fontSize: '12px',
                      width: '12px',
                    }">›</span>
                    <span class="font-serif text-[14px] font-semibold flex-1"
                      style="color: var(--color-ink);">{{ co.name }}</span>
                    <span class="text-[11px]" style="color: var(--color-ink-3);">{{ co.total }}</span>
                  </button>
                  <!-- 部门行 + 人员 (Level 2 + 3, 仅公司展开时显示) -->
                  <template v-if="expandedCompanies.has(co.name)">
                    <template v-for="d in co.depts" :key="`${co.name}|${d.name}`">
                      <button @click="toggleDept(co.name, d.name)"
                        class="w-full px-4 py-2.5 flex items-center gap-2 active:bg-bg text-left"
                        style="border-top: 1px solid var(--color-divider-soft); padding-left: 32px; background: var(--color-bg);">
                        <span class="inline-block transition-transform" :style="{
                          transform: expandedDepts.has(`${co.name}|${d.name}`) ? 'rotate(90deg)' : 'rotate(0)',
                          color: 'var(--color-ink-3)',
                          fontSize: '11px',
                          width: '11px',
                        }">›</span>
                        <span class="text-[13px] flex-1" style="color: var(--color-ink-2);">{{ d.name }}</span>
                        <span class="text-[10px]" style="color: var(--color-ink-3);">{{ d.users.length }}</span>
                      </button>
                      <!-- 人员行 (Level 3, 仅部门展开时显示) -->
                      <template v-if="expandedDepts.has(`${co.name}|${d.name}`)">
                        <button v-for="u in d.users" :key="u.id" @click="pickResult(u)"
                          class="w-full px-4 py-3 flex items-center gap-3 active:bg-bg text-left"
                          style="border-top: 1px solid var(--color-divider-soft); padding-left: 52px;"
                          :disabled="pickerCreating">
                          <div class="w-8 h-8 rounded-full inline-flex items-center justify-center font-serif text-[13px] font-semibold shrink-0"
                            style="background: var(--color-accent-soft); color: var(--color-accent);">{{ u.avatar || u.name?.[0] || '?' }}</div>
                          <div class="flex-1 min-w-0">
                            <div class="font-serif text-[14px] font-medium">{{ u.name }}</div>
                          </div>
                          <span class="text-[16px]" style="color: var(--color-ink-3);">›</span>
                        </button>
                      </template>
                    </template>
                  </template>
                </template>
              </div>
            </div>
          </template>

          <!-- ─── Step: group 选项目 ─── -->
          <template v-else-if="pickerStep === 'group'">
            <div class="px-5 mt-3">
              <div class="rounded-full h-10 flex items-center px-4 gap-2"
                style="background: var(--color-card); border: 1px solid var(--color-divider-strong);">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <circle cx="7" cy="7" r="5" stroke="var(--color-ink-3)" stroke-width="1.4"/>
                  <path d="M11 11l3 3" stroke="var(--color-ink-3)" stroke-width="1.4" stroke-linecap="round"/>
                </svg>
                <input v-model="pickerSearch" @input="doPickerSearch" type="search"
                  :placeholder="t('chat.searchProject')"
                  class="flex-1 bg-transparent outline-none text-[14px] font-serif"
                  style="color: var(--color-ink);" />
              </div>
            </div>
            <div class="px-5 mt-3">
              <div v-if="pickerSearching && !pickerResults.length" class="text-center py-6 text-[13px]"
                style="color: var(--color-ink-3);">{{ t('chat.pickerSearching') }}</div>
              <div v-else-if="!pickerResults.length" class="text-center py-6 text-[13px]"
                style="color: var(--color-ink-3);">{{ pickerSearch ? t('chat.noMatchProject') : t('chat.searchHint') }}</div>
              <div v-else class="rounded-2xl"
                style="background: var(--color-card); border: 1px solid var(--color-divider);">
                <button v-for="(p, i) in pickerResults" :key="p.id" @click="pickResult(p)"
                  class="w-full px-4 py-3 flex items-center gap-3 active:bg-bg text-left"
                  :style="i < pickerResults.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''"
                  :disabled="pickerCreating">
                  <div class="w-9 h-9 rounded-lg inline-flex items-center justify-center text-[14px] font-bold"
                    style="background: var(--color-ink); color: #fff;">#</div>
                  <div class="flex-1 min-w-0">
                    <div class="font-serif text-[15px] font-medium truncate">{{ p.project_name }}</div>
                    <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">
                      <span v-if="p.current_stage" style="color: var(--color-accent); font-weight: 600;">● {{ p.current_stage }}</span>
                      <span v-if="p.quotation_customer">{{ p.current_stage ? ' · ' : '' }}<span class="tabular" style="color: var(--color-ink); font-weight: 600;">{{ t('project.amountWan', { amount: (p.quotation_customer / 10000).toFixed(2) }) }}</span></span>
                    </div>
                  </div>
                  <span class="text-[18px]" style="color: var(--color-ink-3);">›</span>
                </button>
              </div>
              <div class="text-[11px] font-serif italic mt-3 text-center"
                style="color: var(--color-ink-3);">
                {{ t('chat.groupCreateHint') }}
              </div>
            </div>
          </template>

          <!-- ─── Step: main 三选一 ─── -->
          <template v-else>

          <div class="px-7 mt-3 mb-1">
            <div class="font-serif" style="font-size: 22px; font-weight: 500; line-height: 1.3;">{{ t('chat.mainQ') }}</div>
            <div class="font-serif italic mt-1.5"
              style="font-size: 13px; color: var(--color-ink-3);">{{ t('chat.mainSub') }}</div>
          </div>

          <div class="px-5 mt-5 flex flex-col gap-3">
            <!-- AI 助手 主推 -->
            <button @click="pickStart('ai')"
              class="rounded-2xl p-4 flex gap-3.5 items-start active:opacity-80 text-left relative"
              style="background: var(--color-card); border: 2px solid #2F66D6;">
              <PixelP :size="36" />
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-1.5">
                  <span class="font-serif" style="font-size: 17px; font-weight: 600;">{{ t('chat.aiFull') }}</span>
                  <span class="text-[9px] font-bold px-1.5 py-px rounded"
                    style="color: #2F66D6; background: #E5EEFB;">{{ t('chat.aiBeta') }}</span>
                </div>
                <div class="text-[12px] mt-1" style="color: var(--color-ink-3); line-height: 1.5;">
                  {{ t('chat.aiTagline') }}
                </div>
                <div class="flex flex-wrap gap-1.5 mt-2.5">
                  <span v-for="sug in [t('chat.sugAnalyze'), t('chat.sugDraft'), t('chat.sugSummary')]" :key="sug"
                    class="text-[10px] px-2 py-0.5 rounded-full"
                    style="color: #2F66D6; background: #E5EEFB; font-family: ui-monospace, monospace;">{{ sug }}</span>
                </div>
              </div>
              <span class="absolute text-[11px] font-semibold"
                style="top: 14px; right: 14px; color: #2F66D6;">{{ t('chat.recommended') }}</span>
            </button>

            <!-- 私聊同事 -->
            <button @click="pickStart('dm')"
              class="rounded-2xl p-4 flex gap-3.5 items-center active:opacity-80 text-left"
              style="background: var(--color-card); border: 1px solid var(--color-divider);">
              <div class="w-11 h-11 rounded-2xl inline-flex items-center justify-center"
                style="background: var(--color-accent-soft); color: var(--color-accent);">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <circle cx="10" cy="6" r="3" stroke="currentColor" stroke-width="1.6" />
                  <path d="M3 17c0-3.5 3-6.5 7-6.5s7 3 7 6.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
                </svg>
              </div>
              <div class="flex-1">
                <div class="font-serif" style="font-size: 16px; font-weight: 500;">{{ t('chat.dmTitle') }}</div>
                <div class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">{{ t('chat.dmHint') }}</div>
              </div>
              <span class="text-[18px]" style="color: var(--color-ink-3);">›</span>
            </button>

            <!-- 项目群 -->
            <button @click="pickStart('group')"
              class="rounded-2xl p-4 flex gap-3.5 items-center active:opacity-80 text-left"
              style="background: var(--color-card); border: 1px solid var(--color-divider);">
              <div class="w-11 h-11 rounded-2xl inline-flex items-center justify-center"
                style="background: var(--color-ink); color: #fff;">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <circle cx="7" cy="7" r="2.5" stroke="currentColor" stroke-width="1.5" />
                  <circle cx="14" cy="8" r="2" stroke="currentColor" stroke-width="1.5" />
                  <path d="M2 16c0-2.5 2-4.5 5-4.5s5 2 5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
                  <path d="M11 16c0-2 1.5-3.5 3.5-3.5s3.5 1.5 3.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
                </svg>
              </div>
              <div class="flex-1">
                <div class="font-serif" style="font-size: 16px; font-weight: 500;">{{ t('chat.groupTitle') }}</div>
                <div class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">{{ t('chat.groupHint') }}</div>
              </div>
              <span class="text-[18px]" style="color: var(--color-ink-3);">›</span>
            </button>
          </div>

          <div class="px-7 mt-6 text-center text-[11px] font-serif italic"
            style="color: var(--color-ink-3);">
            {{ t('chat.atAiTip') }}
          </div>
          </template>
        </div>
      </div>
    </Transition>
  </div>
</template>
