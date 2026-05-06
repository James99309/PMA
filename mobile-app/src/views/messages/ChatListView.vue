<script setup>
// 会话列表 —— 统一融合本区 + 对区 (Federation Lite)
// 本区调 client.getConversations()，对区用 peer token 直接打对端 baseURL
// 点击 peer 项 → 自动 switchRegion 后跳转
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import PixelP from '@/components/common/PixelP.vue'
import { getConversations, getConversationsForRegion, createConversation, searchUsers, searchProjects } from '@/api/chat'
import { REGIONS } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { formatChatTime } from '@/utils/chatTime'

const router = useRouter()
const auth = useAuthStore()
const showPicker = ref(false)
const loading = ref(true)
const allConversations = ref([])

// 把后端 conversation 映射为 UI 行
function mapConv(c, regionId = null) {
  // 后端 type: 'private' / 'group' / 'ai'
  let kind = c.type === 'private' ? 'dm' : c.type === 'ai' ? 'ai' : 'group'
  const name = c.display_name || c.name || c.topic || '未命名'
  // DM 场景：取对方 participant 的 department 作为副标
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
    // 跨区元信息
    _regionId: regionId,                       // 'cn' / 'sg' / null（本区不标）
    _isPeer: !!regionId && regionId !== auth.regionId,
    _updatedAt: c.updated_at || c.last_message?.created_at || '',
  }
}

// 拆 AI 顶置卡 vs 普通会话
const aiConv = computed(() => allConversations.value.find(c => c.kind === 'ai'))
const conversations = computed(() => allConversations.value.filter(c => c.kind !== 'ai'))
const aiPreview = computed(() => aiConv.value
  ? { text: aiConv.value.last || '点开向源助手提问', time: aiConv.value.time }
  : { text: '点开向源助手提问', time: '' })

async function load() {
  loading.value = true
  try {
    const myRegion = auth.regionId
    const peerRegion = myRegion === 'cn' ? 'sg' : 'cn'
    const hasPeer = !!auth.tokens[peerRegion]
    // 并行拉本区 + 对区（对区无 token 时 helper 自动返回空）
    const [localRes, peerRes] = await Promise.all([
      getConversations(),
      hasPeer ? getConversationsForRegion(peerRegion) : Promise.resolve({ data: { success: false, data: [] } }),
    ])
    const localList = (localRes.data?.success ? localRes.data.data : []) || []
    const peerList  = (peerRes.data?.success  ? peerRes.data.data  : []) || []
    const merged = [
      ...localList.map(c => mapConv(c, myRegion)),
      ...peerList.map(c => mapConv(c, peerRegion)),
    ]
    // 按 updated_at 倒序混排（peer 的对话和本区对话穿插显示）
    merged.sort((a, b) => (b._updatedAt || '').localeCompare(a._updatedAt || ''))
    allConversations.value = merged
  } catch (e) {
    console.error('load conversations failed', e)
    allConversations.value = []
  } finally {
    loading.value = false
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

function openConversation(c) {
  // 跨区项 → 先记当前区，切区，进入聊天后由聊天页负责返回时切回来
  let fromRegion = null
  if (c._isPeer && c._regionId) {
    fromRegion = auth.regionId   // 进入前的本区, 返回时要切回
    if (!auth.switchRegion(c._regionId)) {
      alert(`无法切换到${REGIONS[c._regionId]?.label || c._regionId}区域`)
      return
    }
  }
  // 公司广播 → 公告列表
  if (c.kind === 'broadcast') {
    router.push('/messages/broadcast')
    return
  }
  // 项目群 → GroupChatView
  if (c.kind === 'group') {
    router.push({
      path: `/messages/group/${c.id}`,
      query: { name: c.name, ...(fromRegion ? { fromRegion } : {}) },
    })
    return
  }
  // 私聊 → DmChatView，把对方部门一起带过去
  if (c.kind === 'dm') {
    router.push({
      path: `/messages/dm/${c.id}`,
      query: { name: c.name, role: c.peerDept || '', ...(fromRegion ? { fromRegion } : {}) },
    })
  }
}

// 选择器步骤：'main'（三选一）/ 'dm'（选联系人）/ 'group'（选项目）
const pickerStep = ref('main')
const pickerSearch = ref('')
const pickerResults = ref([])
const pickerSearching = ref(false)
const pickerCreating = ref(false)

function pickStart(kind) {
  if (kind === 'ai') {
    showPicker.value = false
    openAi()
    return
  }
  // 私聊或群：切到对应步骤，先拉一次默认列表（空 q）
  pickerStep.value = kind
  pickerSearch.value = ''
  pickerResults.value = []
  doPickerSearch()
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
        alert(data?.message || '创建私聊失败')
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
        alert(data?.message || '创建项目群失败')
      }
    }
  } catch (e) {
    console.error('create conversation failed', e)
    alert(`创建失败：${e.message || e}`)
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
</script>

<template>
  <div class="flex flex-col h-full" style="background: var(--color-bg);">

    <!-- PageHead -->
    <div class="px-6 pt-3.5 pb-2 flex items-start justify-between shrink-0">
      <div>
        <div class="text-[11px] font-medium uppercase"
          style="color: var(--color-ink-3); letter-spacing: 1.2px;">消息</div>
        <h1 class="font-serif m-0 mt-1"
          style="font-size: 30px; font-weight: 500; letter-spacing: -0.4px; color: var(--color-ink);">聊天</h1>
      </div>
      <button @click="showPicker = true"
        class="w-9 h-9 rounded-full inline-flex items-center justify-center"
        style="background: var(--color-ink); color: #fff; font-size: 20px; font-weight: 300;">+</button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading && !allConversations.length" class="flex justify-center items-center py-10">
      <div class="w-6 h-6 border-2 rounded-full animate-spin"
        style="border-color: var(--color-accent); border-top-color: transparent;" />
    </div>

    <div v-else class="flex-1 overflow-y-auto pb-4">
      <!-- AI 助手置顶卡 (设计 line 474-492) -->
      <div class="px-4 pt-2 pb-1">
        <button @click="openAi"
          class="w-full rounded-2xl p-3.5 flex gap-3 items-center active:opacity-80 text-left"
          style="background: linear-gradient(135deg, rgba(47,102,214,0.06) 0%, rgba(26,180,200,0.07) 100%); border: 1px solid rgba(47,102,214,0.25);">
          <PixelP :size="34" />
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5">
              <span class="font-serif" style="font-size: 15px; font-weight: 600; color: var(--color-ink);">源助手</span>
              <span class="text-[9px] font-bold px-1.5 py-px rounded"
                style="color: #2F66D6; background: #E5EEFB; letter-spacing: 0.5px;">BETA</span>
              <span class="text-[11px] ml-auto" style="color: var(--color-ink-3);">{{ aiPreview.time }}</span>
            </div>
            <div class="text-[12px] mt-1 font-serif truncate"
              style="color: var(--color-ink-2); line-height: 1.4;">
              {{ aiPreview.text }}
            </div>
          </div>
        </button>
      </div>

      <!-- 普通会话 -->
      <div class="mt-2" style="background: var(--color-card);">
        <button v-for="(c, i) in conversations" :key="c.id"
          @click="openConversation(c)"
          class="w-full px-4 py-3.5 flex gap-3 active:bg-bg text-left"
          :style="i < conversations.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
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
                <!-- 跨区角标 (本区不标，仅 peer 项显示) -->
                <span v-if="c._isPeer && c._regionId" class="text-[9px] font-semibold px-1.5 py-px rounded inline-flex items-center gap-0.5"
                  :style="{ color: '#2F66D6', background: '#E5EEFB' }">
                  🌏 {{ REGIONS[c._regionId]?.label || c._regionId }}
                </span>
              </div>
              <span class="text-[11px]" style="color: var(--color-ink-3);">{{ c.time }}</span>
            </div>
            <div class="flex items-baseline justify-between mt-0.5 gap-2">
              <span class="text-[12px] truncate flex-1"
                style="color: var(--color-ink-3);">
                <span v-if="c.draft" style="color: #2F66D6; font-weight: 600;">[AI 草稿] </span>{{ c.last }}
              </span>
              <span v-if="c.unread > 0"
                class="text-[10px] font-bold tabular px-2 py-0.5 rounded-full text-white shrink-0"
                style="background: var(--color-accent);">{{ c.unread }}</span>
            </div>
          </div>
        </button>
      </div>
    </div>

    <!-- 发起聊天 sheet -->
    <Transition name="sheet">
      <div v-if="showPicker" class="absolute inset-0 z-40">
        <div class="absolute inset-0 bg-black/40" @click="closePicker" />
        <div class="absolute left-0 right-0 bottom-0 rounded-t-3xl pt-3 pb-8 max-h-[85vh] overflow-y-auto"
          style="background: var(--color-bg);">
          <div class="mx-auto w-9 h-1 rounded-full mb-3" style="background: rgba(0,0,0,0.15);" />

          <div class="flex items-center justify-between px-5 mb-2">
            <button v-if="pickerStep === 'main'" @click="closePicker" class="text-[15px]"
              style="color: var(--color-accent);">取消</button>
            <button v-else @click="backToPickerMain" class="text-[15px] inline-flex items-center gap-1"
              style="color: var(--color-accent);">
              <svg width="9" height="14" viewBox="0 0 9 14"><path d="M7 1L1 7l6 6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
              返回
            </button>
            <span class="font-serif text-[16px] font-medium">{{
              pickerStep === 'dm' ? '选择联系人' : pickerStep === 'group' ? '选择项目' : '发起聊天'
            }}</span>
            <span class="w-[30px]" />
          </div>

          <!-- ─── Step: dm 选联系人 ─── -->
          <template v-if="pickerStep === 'dm'">
            <div class="px-5 mt-3">
              <div class="rounded-full h-10 flex items-center px-4 gap-2"
                style="background: var(--color-card); border: 1px solid var(--color-divider-strong);">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <circle cx="7" cy="7" r="5" stroke="var(--color-ink-3)" stroke-width="1.4"/>
                  <path d="M11 11l3 3" stroke="var(--color-ink-3)" stroke-width="1.4" stroke-linecap="round"/>
                </svg>
                <input v-model="pickerSearch" @input="doPickerSearch" type="search"
                  placeholder="搜索同事姓名、用户名、部门"
                  class="flex-1 bg-transparent outline-none text-[14px] font-serif"
                  style="color: var(--color-ink);" />
              </div>
            </div>
            <div class="px-5 mt-3">
              <div v-if="pickerSearching && !pickerResults.length" class="text-center py-6 text-[13px]"
                style="color: var(--color-ink-3);">搜索中…</div>
              <div v-else-if="!pickerResults.length" class="text-center py-6 text-[13px]"
                style="color: var(--color-ink-3);">{{ pickerSearch ? '无匹配联系人' : '输入关键词搜索' }}</div>
              <div v-else class="rounded-2xl"
                style="background: var(--color-card); border: 1px solid var(--color-divider);">
                <button v-for="(u, i) in pickerResults" :key="u.id" @click="pickResult(u)"
                  class="w-full px-4 py-3 flex items-center gap-3 active:bg-bg text-left"
                  :style="i < pickerResults.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''"
                  :disabled="pickerCreating">
                  <div class="w-9 h-9 rounded-full inline-flex items-center justify-center font-serif text-[14px] font-semibold"
                    style="background: var(--color-accent-soft); color: var(--color-accent);">{{ u.avatar || u.name?.[0] || '?' }}</div>
                  <div class="flex-1 min-w-0">
                    <div class="font-serif text-[15px] font-medium">{{ u.name }}</div>
                    <div v-if="u.dept" class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">{{ u.dept }}</div>
                  </div>
                  <span class="text-[18px]" style="color: var(--color-ink-3);">›</span>
                </button>
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
                  placeholder="搜索项目名称"
                  class="flex-1 bg-transparent outline-none text-[14px] font-serif"
                  style="color: var(--color-ink);" />
              </div>
            </div>
            <div class="px-5 mt-3">
              <div v-if="pickerSearching && !pickerResults.length" class="text-center py-6 text-[13px]"
                style="color: var(--color-ink-3);">搜索中…</div>
              <div v-else-if="!pickerResults.length" class="text-center py-6 text-[13px]"
                style="color: var(--color-ink-3);">{{ pickerSearch ? '无匹配项目' : '输入关键词搜索' }}</div>
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
                      <span v-if="p.quotation_customer">{{ p.current_stage ? ' · ' : '' }}<span class="tabular" style="color: var(--color-ink); font-weight: 600;">¥{{ (p.quotation_customer / 10000).toFixed(2) }}万</span></span>
                    </div>
                  </div>
                  <span class="text-[18px]" style="color: var(--color-ink-3);">›</span>
                </button>
              </div>
              <div class="text-[11px] font-serif italic mt-3 text-center"
                style="color: var(--color-ink-3);">
                选中后会自动创建群聊，群名 = 项目名（成员可在群设置里手动添加）
              </div>
            </div>
          </template>

          <!-- ─── Step: main 三选一 ─── -->
          <template v-else>

          <div class="px-7 mt-3 mb-1">
            <div class="font-serif" style="font-size: 22px; font-weight: 500; line-height: 1.3;">想和谁聊?</div>
            <div class="font-serif italic mt-1.5"
              style="font-size: 13px; color: var(--color-ink-3);">选一个开始 · 也可以先问 AI 助手</div>
          </div>

          <div class="px-5 mt-5 flex flex-col gap-3">
            <!-- AI 助手 主推 -->
            <button @click="pickStart('ai')"
              class="rounded-2xl p-4 flex gap-3.5 items-start active:opacity-80 text-left relative"
              style="background: var(--color-card); border: 2px solid #2F66D6;">
              <PixelP :size="36" />
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-1.5">
                  <span class="font-serif" style="font-size: 17px; font-weight: 600;">源助手 AI</span>
                  <span class="text-[9px] font-bold px-1.5 py-px rounded"
                    style="color: #2F66D6; background: #E5EEFB;">BETA</span>
                </div>
                <div class="text-[12px] mt-1" style="color: var(--color-ink-3); line-height: 1.5;">
                  你的销售助理 · 知道你所有项目、客户、跟进记录，可以总结、起草、分析。
                </div>
                <div class="flex flex-wrap gap-1.5 mt-2.5">
                  <span v-for="t in ['/分析赢率','/起草回复','/总结群消息']" :key="t"
                    class="text-[10px] px-2 py-0.5 rounded-full"
                    style="color: #2F66D6; background: #E5EEFB; font-family: ui-monospace, monospace;">{{ t }}</span>
                </div>
              </div>
              <span class="absolute text-[11px] font-semibold"
                style="top: 14px; right: 14px; color: #2F66D6;">推荐 →</span>
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
                <div class="font-serif" style="font-size: 16px; font-weight: 500;">私聊同事</div>
                <div class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">从通讯录选 1 人，开始一对一对话</div>
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
                <div class="font-serif" style="font-size: 16px; font-weight: 500;">项目群</div>
                <div class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">选一个项目 · 自动拉相关人 · 群内可 @AI</div>
              </div>
              <span class="text-[18px]" style="color: var(--color-ink-3);">›</span>
            </button>
          </div>

          <div class="px-7 mt-6 text-center text-[11px] font-serif italic"
            style="color: var(--color-ink-3);">
            群和私聊里都可以 @源助手 提问，无需切换
          </div>
          </template>
        </div>
      </div>
    </Transition>
  </div>
</template>
