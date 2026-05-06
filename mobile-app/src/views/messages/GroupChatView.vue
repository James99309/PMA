<script setup>
// 群聊 + @AI —— 严格对齐 ai-chat.jsx GroupAtAI (line 309-381)
// + 引用项目卡用 components/common/refs/ProjectRefCard.vue
// + 共享 chat store：与 ProjectDetailView 项目讨论卡同源
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import PixelP from '@/components/common/PixelP.vue'
import MentionPopover from '@/components/common/MentionPopover.vue'
import MessageText from '@/components/common/MessageText.vue'
import MessageRefs from '@/components/common/MessageRefs.vue'
import MessageAttachment from '@/components/common/MessageAttachment.vue'
import ChatPlusPanel from '@/components/common/ChatPlusPanel.vue'
import VoiceRecordSheet from '@/components/common/VoiceRecordSheet.vue'
import LocationSheet from '@/components/common/LocationSheet.vue'
import { processImage } from '@/utils/imageProcessor'
import PendingRefsPreview from '@/components/common/PendingRefsPreview.vue'
import StageAdvanceCard from '@/components/common/StageAdvanceCard.vue'
import MessageActions from '@/components/common/MessageActions.vue'
import { useLongPress } from '@/composables/useLongPress'
import { useChatStore } from '@/stores/chat'
import { useMention } from '@/composables/useMention'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'
import { getMessages, sendMessage as apiSend, markAsRead, streamAi, getConversation, uploadChatFile } from '@/api/chat'
import { formatChatTime } from '@/utils/chatTime'

const inputRef = ref(null)
const mention = useMention(inputRef)

function handleInput(e) {
  mention.onInput(e.target.value, e.target.selectionStart)
}
function handleMentionSelect(payload) {
  mention.onSelect(payload, inputText.value, t => { inputText.value = t })
}

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const auth = useAuthStore()

// 跨区入口标记: 进入时记下来源区，离开时切回去
const fromRegion = route.query.fromRegion || null
function returnToOriginRegion() {
  if (fromRegion && fromRegion !== auth.regionId && auth.tokens[fromRegion]) {
    auth.switchRegion(fromRegion)
  }
}
function goBack() {
  returnToOriginRegion()
  router.back()
}
onBeforeRouteLeave(() => { returnToOriginRegion() })

// 群信息：从后端拉详情，proj-* 虚拟群退化为 query 字段
const group = ref({
  name: route.query.name || '群聊',
  members: '',
  stage: '',
})

// 群 id（route.params.id 来自 URL；项目群约定 'proj-{id}' 形式）
const groupId = route.params.id

// 真后端会话（数字 id）由 loadHistory() 拉真历史；
// proj-* 虚拟群只是入口占位，无后端，亦不再注入 mock 种子。
const SEED = []

const messages = computed(() => chatStore.getGroup(groupId, SEED))

const inputText = ref('')
const sending = ref(false)
const scrollEl = ref(null)

async function scrollToBottom() {
  await nextTick()
  if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
}

function pushUser(text) {
  const now = new Date()
  const hh = String(now.getHours()).padStart(2, '0')
  const mm = String(now.getMinutes()).padStart(2, '0')
  const isAtAi = text.includes('@AI') || text.includes('@源助手')
  const cleanedText = text.replace(/^@(AI|源助手)\s*/, '')
  chatStore.appendToGroup(groupId, {
    kind: 'me',
    from: '我',
    initial: '我',
    time: `${hh}:${mm}`,
    text: cleanedText,
    mention: isAtAi ? '@源助手' : null,
    refs: mention.pendingRefs.value.length ? [...mention.pendingRefs.value] : undefined,
    _local: true,
    _content: cleanedText,
    _created_at_ms: Date.now(),
  })
  mention.clearRefs()
  return isAtAi
}

function pushAiThinking() {
  const now = new Date()
  const id = `ai-${Date.now()}`
  chatStore.appendToGroup(groupId, {
    id, kind: 'ai',
    time: `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`,
    thinking: true,
  })
  return id
}

function replaceAi(id, body) {
  chatStore.replaceMessage(groupId, id, { thinking: false, body })
}

// IME 状态显式跟踪 (iOS Chinese 键盘 e.isComposing / 229 不可靠)
const _isComposing = ref(false)
let _composEndTimer = null
function onCompStart() {
  _isComposing.value = true
  if (_composEndTimer) { clearTimeout(_composEndTimer); _composEndTimer = null }
}
function onCompEnd() {
  _composEndTimer = setTimeout(() => { _isComposing.value = false }, 100)
}
function onEnterKey(e) {
  if (_isComposing.value || e?.isComposing || e?.keyCode === 229) return
  send()
}

// 节流: 800ms 内重复触发的 send 直接吞掉 (iOS IME 双发兜底)
let _lastSendAt = 0

async function send() {
  const now = Date.now()
  if (now - _lastSendAt < 800) return
  const t = inputText.value.trim()
  if (!t || sending.value) return
  _lastSendAt = now
  sending.value = true
  // 抓快照（pushUser 会 clearRefs，要先存）
  const refsSnapshot = mention.pendingRefs.value.length
    ? mention.pendingRefs.value.map(r => ({ type: r.type, item: r.item }))
    : null
  const isAt = pushUser(t)            // 本地立即显示用户消息
  inputText.value = ''
  await scrollToBottom()

  const numericId = /^\d+$/.test(String(groupId)) ? Number(groupId) : null

  // 分支 1：@源助手 走 SSE（streamAi 内部会在后端保存 user message + AI 回复）
  if (isAt) {
    if (!numericId) {
      // proj-* 虚拟群（无后端会话）：保留旧 mock 流程
      setTimeout(async () => {
        const tid = pushAiThinking()
        await scrollToBottom()
        setTimeout(async () => {
          replaceAi(tid, 'reply')
          sending.value = false
          await scrollToBottom()
        }, 1500)
      }, 300)
      return
    }

    // 真 SSE：在群里 @AI
    const tid = pushAiThinking()
    await scrollToBottom()
    let streamed = ''
    try {
      await streamAi({
        content: t,                   // 保留 @源助手 前缀让 AI 知道被点名
        conversationId: numericId,
        onEvent: async (ev) => {
          if (ev.type === 'content') {
            streamed += ev.text || ''
            chatStore.replaceMessage(groupId, tid, { thinking: false, body: { type: 'stream', text: streamed } })
            await scrollToBottom()
          } else if (ev.type === 'status') {
            chatStore.replaceMessage(groupId, tid, { thinking: false, body: { type: 'status', text: ev.message || '思考中…' } })
          } else if (ev.type === 'error' || ev.type === 'context_exhausted') {
            chatStore.replaceMessage(groupId, tid, { thinking: false, body: { type: 'error', text: ev.message || 'AI 服务异常' } })
          }
        },
      })
    } catch (e) {
      console.error('group AI stream failed', e)
      chatStore.replaceMessage(groupId, tid, { thinking: false, body: { type: 'error', text: `连接失败：${e.message}` } })
    } finally {
      sending.value = false
      await scrollToBottom()
    }
    return
  }

  // 分支 2：普通消息直接 apiSend（含可能的 #/$ 引用卡）
  if (numericId) {
    try { await apiSend(numericId, t, null, refsSnapshot) }
    catch (e) { console.error('send message failed', e) }
  }
  sending.value = false
}

// ── 附件上传 / + 面板 / 录音 / 位置 ──
const showPlusPanel = ref(false)
const inputFocused = ref(false)
const { kbOffset } = useKeyboardOffset()
function blurInput() {
  if (inputRef.value) inputRef.value.blur()
  showPlusPanel.value = false
}
let blurTimer = null
function onComposerBlur() {
  blurTimer = setTimeout(() => { inputFocused.value = false }, 150)
}
function onComposerFocus() {
  if (blurTimer) { clearTimeout(blurTimer); blurTimer = null }
  inputFocused.value = true
  showPlusPanel.value = false
}
const showVoiceSheet = ref(false)
const showLocationSheet = ref(false)
const locationView = ref(null)
const locationMode = ref('share')
function _convId() { return /^\d+$/.test(String(groupId)) ? Number(groupId) : null }

// 立即插入气泡（原图预览）→ 后台压缩 + 上传
function insertOptimistic(file, kind, meta) {
  const localId = `local-up-${Date.now()}-${Math.random()}`
  const previewUrl = (kind === 'image') ? URL.createObjectURL(file) : ''
  chatStore.appendToGroup(groupId, {
    id: localId, kind: 'me', from: '我', initial: '我',
    time: formatChatTime(new Date().toISOString()), text: '',
    attachment: {
      type: kind === 'voice' ? 'voice' : (kind === 'image' ? 'image' : 'file'),
      url: previewUrl, meta,
    },
    _local: true, _uploading: true, _previewUrl: previewUrl,
    _content: '', _created_at_ms: Date.now(),
  })
  scrollToBottom()
  return localId
}
async function processAndUpload(localId, file, kind, meta) {
  const cid = _convId()
  if (!cid) return
  let toUpload = file
  if (kind === 'image') { try { toUpload = await processImage(file) } catch {} }
  try {
    const r = await uploadChatFile(toUpload, kind, meta.name)
    const data = r.data?.data || r.data
    if (!data?.file_url) throw new Error('上传失败')
    const list = chatStore.getGroup(groupId, [])
    const local = list.find(m => m.id === localId)
    if (local) {
      local._uploading = false
      local._serverFileUrl = data.file_url
    }
    await apiSend(cid, '', null, null, {
      message_type: kind === 'voice' ? 'voice' : (kind === 'image' ? 'image' : 'file'),
      file_url: data.file_url,
      file_meta: { ...meta, size: toUpload.size || meta.size },
    })
  } catch (e) {
    const list = chatStore.getGroup(groupId, [])
    const local = list.find(m => m.id === localId)
    if (local) local._error = e?.message || '上传失败'
    alert('上传失败：' + (e?.message || e))
  } finally {
    const list = chatStore.getGroup(groupId, [])
    const local = list.find(m => m.id === localId)
    if (local?._previewUrl) setTimeout(() => URL.revokeObjectURL(local._previewUrl), 8000)
  }
}
function onPickImages(files) {
  showPlusPanel.value = false
  for (const f of files) {
    const meta = { name: f.name || 'image', size: f.size || 0 }
    const id = insertOptimistic(f, 'image', meta)
    processAndUpload(id, f, 'image', meta)
  }
}
function onPickCamera(file) {
  showPlusPanel.value = false
  const meta = { name: file.name || 'photo.jpg', size: file.size || 0 }
  const id = insertOptimistic(file, 'image', meta)
  processAndUpload(id, file, 'image', meta)
}
function onPickFile(file) {
  showPlusPanel.value = false
  const meta = { name: file.name || 'file', size: file.size || 0 }
  const id = insertOptimistic(file, 'file', meta)
  processAndUpload(id, file, 'file', meta)
}
function onRequestShareLocation() {
  showPlusPanel.value = false
  locationMode.value = 'share'
  locationView.value = null
  showLocationSheet.value = true
}
function onViewLocation({ lat, lon }) {
  locationMode.value = 'view'
  locationView.value = { lat, lon }
  showLocationSheet.value = true
}
async function sendLocation(lat, lon, meta = {}) {
  const cid = _convId()
  if (!cid) throw new Error('无效会话')
  const fullMeta = { lat, lon, name: meta.name || '', address: meta.address || '' }
  const localId = `local-loc-${Date.now()}`
  chatStore.appendToGroup(groupId, {
    id: localId, kind: 'me', from: '我', initial: '我',
    time: formatChatTime(new Date().toISOString()), text: '',
    attachment: { type: 'location', url: '', meta: fullMeta },
    _local: true, _content: '', _created_at_ms: Date.now(),
  })
  await scrollToBottom()
  await apiSend(cid, '', null, null, {
    message_type: 'location', file_url: null, file_meta: fullMeta,
  })
}
async function onSendVoice(blob, durationSec) {
  const ext = blob.type.includes('webm') ? 'webm' : 'm4a'
  const fname = `voice_${Date.now()}.${ext}`
  const f = new File([blob], fname, { type: blob.type })
  const meta = { name: fname, size: f.size, duration: durationSec }
  const id = insertOptimistic(f, 'voice', meta)
  processAndUpload(id, f, 'voice', meta)
}

// 已知本地最新消息时间（增量轮询用）
let lastMsgIso = null

// 把后端消息 dict 映射到 store 并追加（去重）
function appendBackendMessage(m) {
  const id = `srv-${m.id}`
  // 去重：store 已有则跳过
  const existing = chatStore.getGroup(groupId, []).find(x => x.id === id)
  if (existing) return false

  const isMine = m.is_mine || m.is_self
  const isAi   = m.is_ai_response
  const isStageAdv = m.message_type === 'stage_advance'
  const isTextRefs = m.message_type === 'text_refs'
  const isSystem = !isStageAdv && !isTextRefs && (m.message_type === 'system' || (m.sender_id == null && !isAi))

  // 解析带引用卡的消息：content 是 JSON {text, refs}
  let displayText = m.content
  let attachedRefs
  let attachment
  const isAttachment = ['image', 'file', 'voice', 'location'].includes(m.message_type)
  if (isTextRefs && m.content) {
    try {
      const payload = JSON.parse(m.content)
      displayText = payload.text || ''
      attachedRefs = payload.refs || null
    } catch {}
  } else if (isAttachment) {
    let payload = {}
    try { payload = m.content ? JSON.parse(m.content) : {} } catch {}
    displayText = payload.text || ''
    attachment = { type: m.message_type, url: m.file_url || '', meta: payload }
  }
  // 翻译: 后端按 viewer language_preference 已附带 translation
  let originalText = ''
  if (m.translation && displayText && m.translation !== displayText) {
    originalText = displayText
    displayText = m.translation
  }

  // 自己发的附件消息：靠 file_url 精准替换本地乐观气泡
  if (isMine && isAttachment && m.file_url) {
    const list = chatStore.getGroup(groupId, [])
    const local = list.find(x => x._local && x._serverFileUrl === m.file_url)
    if (local) {
      Object.assign(local, {
        id, _local: false, _uploading: false,
        time: formatChatTime(m.created_at),
        text: displayText, attachment,
        _created_at_ms: m.created_at ? new Date(m.created_at).getTime() : Date.now(),
      })
      return false
    }
  }
  // 自己发的文本消息: 用原文+时间窗匹配本地乐观气泡, 找到就替换不重复显示
  if (isMine && !isAttachment && !isStageAdv) {
    const list = chatStore.getGroup(groupId, [])
    const matchText = originalText || displayText
    const newMs = m.created_at ? new Date(m.created_at).getTime() : Date.now()
    let local = list.find(x => x._local && x._content === matchText &&
      Math.abs((x._created_at_ms || 0) - newMs) < 30000)
    // 兜底: 时间戳漂移时仅原文匹配
    if (!local) local = list.find(x => x._local && x._content === matchText)
    if (local) {
      Object.assign(local, {
        id, _local: false,
        time: formatChatTime(m.created_at),
        text: displayText,
        original: originalText || undefined,
        refs: attachedRefs || undefined,
        _created_at_ms: newMs,
      })
      return false
    }
  }

  if (isStageAdv) {
    let payload = {}
    try { payload = JSON.parse(m.content || '{}') } catch {}
    chatStore.appendToGroup(groupId, {
      id, kind: 'stage-advance',
      fromStage: payload.from_stage_label || '',
      toStage:   payload.to_stage_label || '',
      byName:    payload.by_name || '',
      byInitial: payload.by_initial || (payload.by_name || '?')[0],
      time: formatChatTime(m.created_at),
      note: payload.note || '',
      _created_at_ms: m.created_at ? new Date(m.created_at).getTime() : Date.now(),
    })
    return true
  }

  const kind = isSystem ? 'system' : isAi ? 'ai' : isMine ? 'me' : 'them'
  chatStore.appendToGroup(groupId, {
    id, kind,
    from: isAi ? '源助手' : (m.sender_name || '?'),
    initial: isAi ? 'P' : ((m.sender_name || '?')[0]),
    time: formatChatTime(m.created_at),
    text: displayText,
    original: originalText,
    refs: attachedRefs || undefined,
    attachment,
    _created_at_ms: m.created_at ? new Date(m.created_at).getTime() : Date.now(),
    recalled: !!m.is_deleted,
  })
  return true
}

// 拉真消息历史（项目群 'proj-*' 跳过，仅普通群）
async function loadHistory() {
  const numericId = /^\d+$/.test(String(groupId)) ? Number(groupId) : null
  if (!numericId) return
  try {
    const res = await getMessages(numericId, { limit: 50 })
    if (!res.data?.success) return
    const list = res.data.data || []
    if (list.length) lastMsgIso = list[list.length - 1].created_at
    list.forEach(appendBackendMessage)
    await scrollToBottom()
    try { await markAsRead(numericId) } catch {}
  } catch (e) {
    console.error('load history failed', e)
  }
}

// 增量轮询新消息（每 3 秒）
let msgPollTimer = null
async function pollNewMessages() {
  const numericId = /^\d+$/.test(String(groupId)) ? Number(groupId) : null
  if (!numericId) return
  try {
    const res = await getMessages(numericId, { limit: 50, since: lastMsgIso })
    if (!res.data?.success) return
    const list = res.data.data || []
    let added = 0
    list.forEach(m => { if (appendBackendMessage(m)) added++ })
    if (list.length) lastMsgIso = list[list.length - 1].created_at
    // 同步撤回
    const recalledIds = res.data.recalled_ids || []
    recalledIds.forEach(({ id }) => chatStore.replaceMessage(groupId, `srv-${id}`, { recalled: true, text: '', attachment: null, refs: null }))
    if (added > 0) {
      await scrollToBottom()
      try { await markAsRead(numericId) } catch {}
    }
  } catch (e) {
    console.warn('poll messages failed', e)
  }
}

// ── 消息长按 actions ──
const actionMessage = ref(null)
const lp = useLongPress((m) => { actionMessage.value = m })
function closeActions() { actionMessage.value = null }
function onRecalled({ id }) {
  chatStore.replaceMessage(groupId, id, { recalled: true, text: '', attachment: null, refs: null })
}
function onForwarded() {
  // 弱提示：暂时不打扰用户
  console.log('转发成功')
}

async function loadGroupInfo() {
  const numericId = /^\d+$/.test(String(groupId)) ? Number(groupId) : null
  if (!numericId) return
  try {
    const r = await getConversation(numericId)
    if (!r.data?.success) return
    const d = r.data.data
    group.value.name = d.name || group.value.name
    const cnt = (d.participants || []).length
    group.value.members = cnt ? `${cnt} 人` : ''
    group.value.stage = d.linked_project?.stage || ''
  } catch (e) {
    console.warn('load group info failed', e)
  }
}

function startPolling() {
  if (msgPollTimer) return
  msgPollTimer = setInterval(() => {
    if (document.visibilityState === 'hidden') return
    pollNewMessages()
  }, 5000)
}
function stopPolling() {
  if (msgPollTimer) { clearInterval(msgPollTimer); msgPollTimer = null }
}
function onVisibilityChange() {
  if (document.visibilityState === 'visible') pollNewMessages()
}

onMounted(async () => {
  await scrollToBottom()
  await Promise.all([loadHistory(), loadGroupInfo()])
  startPolling()
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onUnmounted(() => {
  stopPolling()
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<template>
  <div class="flex flex-col h-full"
    :style="{
      background: 'var(--color-bg)',
      paddingBottom: kbOffset + 'px',
      transition: 'padding-bottom 0.25s cubic-bezier(.25,.46,.45,.94)',
    }">

    <!-- Nav -->
    <div class="flex items-center gap-2.5 px-4 py-2 shrink-0"
      style="background: var(--color-card); border-bottom: 1px solid var(--color-divider);">
      <button @click="goBack" class="active:opacity-60 px-1">
        <svg width="9" height="14" viewBox="0 0 9 14">
          <path d="M7 1L1 7l6 6" fill="none" stroke="var(--color-ink-2)" stroke-width="1.6"
            stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <div class="flex-1 min-w-0">
        <div class="font-serif truncate" style="font-size: 15px; font-weight: 600;">{{ group.name }}</div>
        <div v-if="group.members || group.stage" class="text-[11px]" style="color: var(--color-ink-3);">
          <span v-if="group.members">{{ group.members }}</span>
          <span v-if="group.stage"> · <span style="color: var(--color-accent);">{{ group.stage }}</span></span>
        </div>
      </div>
      <button @click="router.push({ path: `/messages/group/${groupId}/settings`, query: { name: group.name } })"
        class="text-[18px] active:opacity-60 px-1"
        style="color: var(--color-ink-3);">···</button>
    </div>

    <!-- Messages -->
    <div ref="scrollEl" class="flex-1 overflow-y-auto py-3" @click="blurInput">
      <template v-for="m in messages" :key="m.id">

        <!-- 阶段推进卡（系统消息富卡）-->
        <StageAdvanceCard v-if="m.kind === 'stage-advance'"
          :from-stage="m.fromStage"
          :to-stage="m.toStage"
          :by-name="m.byName"
          :by-initial="m.byInitial"
          :time="m.time"
          :note="m.note" />

        <!-- 系统消息（居中斜体小字）-->
        <div v-else-if="m.kind === 'system'" class="px-4 py-2 text-center">
          <span class="text-[11px] italic font-serif" style="color: var(--color-ink-3);">
            {{ m.text }}
          </span>
        </div>

        <!-- 我的消息（右对齐，ink 黑底）-->
        <div v-else-if="m.kind === 'me'" class="px-4 py-1.5 flex flex-col items-end">
          <div v-if="m.recalled" class="text-[12px] italic"
            style="color: var(--color-ink-3);">你撤回了一条消息</div>
          <template v-else>
            <div class="text-white max-w-[300px]"
              style="background: var(--color-ink); border-radius: 18px 18px 4px 18px;
                     padding: 9px 13px; font-size: 15px; line-height: 1.4; font-family: var(--font-sans);"
              @touchstart="lp.onTouchStart($event, m)"
              @touchmove="lp.onTouchMove"
              @touchend="lp.onTouchEnd"
              @touchcancel="lp.onTouchCancel">
              <span v-if="m.mention" class="font-semibold" style="color: #5FA5FF;">{{ m.mention }}&nbsp;</span>
              <MessageText v-if="m.text" :text="m.text" inverted />
              <MessageRefs v-if="m.refs?.length" :refs="m.refs" class="mt-2" />
            </div>
            <div v-if="m.original" class="text-[11px] italic mt-1 max-w-[300px] break-words text-right"
              style="color: var(--color-ink-3); line-height: 1.35;">
              <span style="opacity: 0.7;">原文：</span>{{ m.original }}
            </div>
            <div v-if="m.attachment" class="relative" :class="m.text ? 'mt-1.5' : ''"
              @touchstart="lp.onTouchStart($event, m)"
              @touchmove="lp.onTouchMove"
              @touchend="lp.onTouchEnd"
              @touchcancel="lp.onTouchCancel">
              <MessageAttachment inverted
                :type="m.attachment.type" :url="m.attachment.url" :meta="m.attachment.meta"
                @view-location="onViewLocation"
                @media-loaded="scrollToBottom" />
              <span v-if="m._uploading"
                class="absolute inset-0 rounded-xl flex items-center justify-center pointer-events-none"
                style="background: rgba(0,0,0,0.45);">
                <span class="text-white text-[11px] inline-flex items-center gap-1.5">
                  <span class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  上传中
                </span>
              </span>
            </div>
            <div class="text-[10px] mt-1" style="color: var(--color-ink-3);">{{ m.time }}</div>
          </template>
        </div>

        <!-- 别人的消息（带头像）-->
        <div v-else-if="m.kind === 'user' || m.kind === 'them'" class="px-4 py-1.5 flex gap-2.5">
          <div class="w-7 h-7 rounded-full inline-flex items-center justify-center font-serif text-[12px] font-semibold shrink-0"
            style="background: var(--color-accent-soft); color: var(--color-accent);">{{ m.initial }}</div>
          <div class="flex-1 min-w-0">
            <div class="text-[12px] font-semibold mb-1" style="color: var(--color-ink-2);">
              {{ m.from }} · {{ m.time }}
            </div>
            <div v-if="m.recalled" class="text-[12px] italic"
              style="color: var(--color-ink-3);">{{ m.from }} 撤回了一条消息</div>
            <template v-else>
              <div class="inline-block max-w-[300px]"
                style="background: var(--color-card); border: 1px solid var(--color-divider);
                       border-radius: 18px 18px 18px 4px; padding: 9px 13px;
                       font-size: 15px; line-height: 1.4; font-family: var(--font-sans);"
                @touchstart="lp.onTouchStart($event, m)"
                @touchmove="lp.onTouchMove"
                @touchend="lp.onTouchEnd"
                @touchcancel="lp.onTouchCancel">
                <span v-if="m.mention === true || m.mention === '@我'" class="font-semibold"
                  style="color: var(--color-accent);">@我&nbsp;</span>
                <span v-else-if="typeof m.mention === 'string' && m.mention !== '@我'" class="font-semibold" style="color: #2F66D6;">{{ m.mention }}&nbsp;</span>
                <MessageText v-if="m.text" :text="m.text" />
                <MessageRefs v-if="m.refs?.length" :refs="m.refs" class="mt-2" />
              </div>
              <div v-if="m.original" class="text-[11px] italic mt-1 max-w-[300px] break-words"
                style="color: var(--color-ink-3); line-height: 1.35;">
                <span style="opacity: 0.7;">原文：</span>{{ m.original }}
              </div>
              <div v-if="m.attachment"
                :class="m.text ? 'mt-1.5' : ''"
                @touchstart="lp.onTouchStart($event, m)"
                @touchmove="lp.onTouchMove"
                @touchend="lp.onTouchEnd"
                @touchcancel="lp.onTouchCancel">
                <MessageAttachment
                  :type="m.attachment.type" :url="m.attachment.url" :meta="m.attachment.meta"
                  @view-location="onViewLocation"
                  @media-loaded="scrollToBottom" />
              </div>
            </template>
          </div>
        </div>

        <!-- AI 公开回答 -->
        <div v-else class="px-4 py-1.5 flex gap-2.5 items-start">
          <PixelP :size="22" />
          <div class="flex-1 min-w-0">
            <div class="flex items-baseline gap-1.5 mb-1">
              <span class="text-[12px] font-semibold" style="color: #1E4FAA;">源助手</span>
              <span class="text-[10px]" style="color: var(--color-ink-3);">{{ m.time }}</span>
            </div>
            <div class="font-serif"
              style="background: rgba(47,102,214,0.06); border: 1px solid rgba(47,102,214,0.18);
                     border-radius: 4px 14px 14px 14px; padding: 12px 14px;
                     font-size: 14px; line-height: 1.55; color: var(--color-ink);">
              <!-- thinking -->
              <div v-if="m.thinking" class="flex items-center gap-2 py-1">
                <span class="inline-flex gap-1">
                  <span v-for="i in 3" :key="i" class="w-1.5 h-1.5 rounded-full"
                    style="background: #2F66D6;"
                    :style="{ animation: `aiDot 1.4s ${(i-1)*0.16}s infinite` }" />
                </span>
                <span class="text-[12px] italic" style="color: var(--color-ink-3);">正在分析数据…</span>
              </div>

              <!-- 真后端 SSE 流式 -->
              <template v-else-if="m.body && m.body.type === 'stream'">
                <div class="whitespace-pre-wrap">{{ m.body.text }}</div>
              </template>
              <template v-else-if="m.body && m.body.type === 'status'">
                <div class="flex items-center gap-2 py-1">
                  <span class="inline-flex gap-1">
                    <span v-for="i in 3" :key="i" class="w-1.5 h-1.5 rounded-full"
                      style="background: #2F66D6;"
                      :style="{ animation: `aiDot 1.4s ${(i-1)*0.16}s infinite` }" />
                  </span>
                  <span class="text-[12px] italic" style="color: var(--color-ink-3);">{{ m.body.text }}</span>
                </div>
              </template>
              <template v-else-if="m.body && m.body.type === 'error'">
                <div class="text-[13px]" style="color: #A04848;">⚠️ {{ m.body.text }}</div>
              </template>

              <!-- 旧 mock 周报模板（保留兜底，proj-* 虚拟群仍用）-->
              <template v-else-if="m.body === 'weekly'">
                <div class="text-[11px] font-semibold mb-1" style="color: #2F66D6;">📊 项目周报 · 第 17 周</div>
                <div><b>{{ group.name }}</b>本周关键进展：</div>
                <ol style="margin: 8px 0; padding-left: 20px; line-height: 1.8;">
                  <li>04 · 25 阶段从「嵌入」推进到「招标中」(陈刚)</li>
                  <li>04 · 26 客户方案 V1 已交付，正在评审</li>
                  <li>本周新增 2 条跟进 · 群内消息 38 条</li>
                </ol>
                <div class="text-[12px] italic font-serif mt-1.5"
                  style="color: var(--color-ink-3);">
                  ⚠️ 提示：标书 V2 截止 周五，目前进度待跟进
                </div>
              </template>

              <!-- 续写：导出格式 -->
              <template v-else-if="m.body === 'reply'">
                <div>已为你导出飞书富文本格式：</div>
                <div class="rounded-lg p-3 mt-2 font-mono text-[12px] leading-relaxed whitespace-pre-wrap"
                  style="background: var(--color-card); border: 1px dashed var(--color-divider-strong); color: var(--color-ink-2);">📊 项目周报 · 第 17 周
项目：{{ group.name }}

本周关键进展：
1. 阶段：嵌入 → 招标中
2. 客户方案 V1 已交付
3. 群内消息 38 条 / 跟进 2 条

⚠️ 标书 V2 截止 周五</div>
                <button class="mt-2 text-[12px] font-medium active:opacity-60"
                  style="color: #2F66D6;">📋 复制到剪贴板</button>
              </template>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Composer (含 @ 提及 popover) -->
    <div class="shrink-0 safe-bottom relative"
      style="background: var(--color-card); border-top: 1px solid var(--color-divider);">

      <!-- @/#/$ 提及选择器 -->
      <MentionPopover
        :visible="mention.popoverVisible.value"
        :type="mention.popoverType.value"
        :query="mention.popoverQuery.value"
        :conv-id="/^\d+$/.test(String(groupId)) ? Number(groupId) : null"
        @select="handleMentionSelect"
        @switch-type="mention.switchType" />

      <PendingRefsPreview class="px-3 pt-2"
        :refs="mention.pendingRefs.value"
        @remove="mention.removeRef" />

      <div class="px-3 pt-3 pb-1 flex items-center gap-2">
        <button type="button" @click="showPlusPanel = !showPlusPanel"
          class="w-9 h-9 rounded-full inline-flex items-center justify-center text-[18px] shrink-0"
          :style="{
            background: showPlusPanel ? 'var(--color-ink)' : 'var(--color-bg)',
            border: showPlusPanel ? '1px solid var(--color-ink)' : '1px solid var(--color-divider-strong)',
            color: showPlusPanel ? '#fff' : 'var(--color-ink-2)',
            transform: showPlusPanel ? 'rotate(45deg)' : 'none',
            transition: 'transform 0.2s ease, background 0.2s ease, color 0.2s ease',
            fontWeight: 200,
            lineHeight: 1,
          }">+</button>
        <div class="flex-1 rounded-full px-3.5 py-2.5 flex items-center gap-2"
          :style="{
            background: 'var(--color-bg)',
            border: mention.popoverVisible.value ? '1.5px solid var(--color-accent)' : '1px solid var(--color-divider-strong)',
          }">
          <input ref="inputRef" v-model="inputText" type="text"
            placeholder="说点什么… 输入 @ 通知"
            @input="handleInput"
            @compositionstart="onCompStart"
            @compositionend="onCompEnd"
            @keyup.enter="onEnterKey"
            @focus="onComposerFocus"
            @blur="onComposerBlur"
            :disabled="sending"
            class="flex-1 bg-transparent outline-none text-[15px]"
            style="color: var(--color-ink); font-family: var(--font-sans);" />
        </div>
        <button v-if="inputText.trim()" @click="send" :disabled="sending"
          class="w-9 h-9 rounded-full inline-flex items-center justify-center text-[14px] font-bold text-white disabled:opacity-40 shrink-0"
          style="background: var(--color-accent);">↑</button>
        <button v-else type="button" @click="showVoiceSheet = true"
          class="w-9 h-9 rounded-full inline-flex items-center justify-center shrink-0"
          style="background: var(--color-bg); border: 1px solid var(--color-divider-strong);">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="6" y="2" width="4" height="8" rx="2" stroke="var(--color-ink-2)" stroke-width="1.4"/>
            <path d="M3.5 8a4.5 4.5 0 009 0M8 12.5V14" stroke="var(--color-ink-2)" stroke-width="1.4" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <ChatPlusPanel v-if="showPlusPanel"
        @pick-image="onPickImages"
        @pick-camera="onPickCamera"
        @pick-file="onPickFile"
        @share-location="onRequestShareLocation" />

      <!-- 引用快捷入口：项目 / 客户（始终渲染、靠 display 切换避免聚焦时 mount 延迟）-->
      <div v-show="inputFocused" class="px-4 pb-3 flex items-center gap-2">
        <button @mousedown.prevent @click="mention.openPicker('#')"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] active:opacity-70"
          style="background: var(--color-bg); border: 1px solid var(--color-divider-strong); color: var(--color-ink-2);">
          <span class="inline-flex items-center justify-center w-4 h-4 rounded text-[10px] text-white font-bold"
            style="background: var(--color-ink);">#</span>
          项目
        </button>
        <button @mousedown.prevent @click="mention.openPicker('$')"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] active:opacity-70"
          style="background: var(--color-bg); border: 1px solid var(--color-divider-strong); color: var(--color-ink-2);">
          <span class="inline-flex items-center justify-center w-4 h-4 rounded text-[10px] text-white font-bold"
            style="background: var(--color-accent);">$</span>
          客户
        </button>
        <span class="ml-auto text-[10px]" style="color: var(--color-ink-4);">直接输入 @ 通知成员</span>
      </div>
    </div>

    <!-- 消息长按 actions -->
    <MessageActions
      :message="actionMessage"
      :is-mine="actionMessage?.kind === 'me'"
      @close="closeActions"
      @recalled="onRecalled"
      @forwarded="onForwarded" />

    <!-- 语音录制 sheet -->
    <VoiceRecordSheet v-model="showVoiceSheet" :send="onSendVoice" />

    <!-- 位置 sheet（共享 / 查看 共用）-->
    <LocationSheet v-model="showLocationSheet"
      :mode="locationMode"
      :lat="locationView?.lat"
      :lon="locationView?.lon"
      :send="locationMode==='share' ? sendLocation : null" />
  </div>
</template>

<style scoped>
@keyframes aiDot {
  0%, 80%, 100% { opacity: 0.3; }
  40% { opacity: 1; }
}
</style>
