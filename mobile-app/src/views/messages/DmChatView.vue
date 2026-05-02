<script setup>
// 私聊 + AI 草稿区 —— 严格对齐 ai-chat.jsx DMAIDraft (line 383-459)
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
import FileCard from '@/components/common/FileCard.vue'
import VoiceMsg from '@/components/common/VoiceMsg.vue'
import MessageActions from '@/components/common/MessageActions.vue'
import ReadReceipt from '@/components/common/ReadReceipt.vue'
import { useMention } from '@/composables/useMention'
import { useLongPress } from '@/composables/useLongPress'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'
import { getMessages, sendMessage as apiSend, markAsRead, streamAi, uploadChatFile } from '@/api/chat'
import { formatChatTime } from '@/utils/chatTime'

const route = useRoute()
const router = useRouter()

const inputRef = ref(null)
const mention = useMention(inputRef)
function handleInput(e) {
  mention.onInput(e.target.value, e.target.selectionStart)
}
function handleMentionSelect(payload) {
  mention.onSelect(payload, inputText.value, t => { inputText.value = t })
}

// 联系人信息（从 query 串接，实际拉历史时由后端 participants 补全）
const peer = ref({
  name: route.query.name || '私聊',
  initial: (route.query.name || '?')[0],
  role: route.query.role || '',
  company: route.query.company || '',
})

// 消息列表
// 真后端 DM（数字 id）：空数组，loadHistory 拉真历史
// 非数字 id（罕见，比如未来的虚拟会话）：保留富媒体演示种子
const isRealDm = /^\d+$/.test(String(route.params.id))
const messages = ref(isRealDm ? [] : [
  { id: 1, kind: 'them', day: '昨天', time: '昨天 17:42',
    text: '深圳那个项目方案 PDF 你有吗？' },
  { id: 2, kind: 'me', time: '昨天 17:45', text: '有，我现在发给你。', read: true },
  { id: 3, kind: 'me', time: '昨天 17:45',
    file: { name: '深圳半导体方案 V3.pdf', size: '2.4 MB', pages: 12, type: 'PDF' }, read: true },
  { id: 4, kind: 'them', day: '今天', time: '今天 09:02',
    text: '收到了，谢谢！客户那边什么时候反馈？' },
  { id: 5, kind: 'them', time: '今天 09:03',
    voice: { duration: '00:08', waveform: [6, 11, 8, 15, 12, 18, 9, 14, 7, 11, 5, 9, 12, 8] } },
])

// AI 草稿（独立浮层）
const draft = ref({
  visible: true,
  time: '今天 09:12',
  label: '建议回复 · 已结合客户偏好与历史报价',
  text: '李经理您好，报价方面我这边已经申请到约 5% 的让利空间，稍后单独发您。工期方面，90 天是有挑战但可以做，前提是设备分两批进场。今晚我先把更新版方案发您，明天我们当面对一遍？',
  meta: ['语气：专业但温暖', '引用：历史 5% 让利记录'],
})

const SUGGEST_TAGS = ['更简短一点', '更正式一点', '加一句关于产能的']

const inputText = ref('')
const sending = ref(false)
const scrollEl = ref(null)
// AI 草稿区只在 mock 场景默认显示；真后端 DM 默认隐藏（用户主动 @AI 才弹 AI 气泡）
const showDraftSection = ref(!isRealDm)

async function scrollToBottom() {
  await nextTick()
  if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
}

function adoptDraft() {
  inputText.value = draft.value.text
  draft.value.visible = false
  showDraftSection.value = false
}

function regenerateDraft() {
  draft.value = {
    ...draft.value,
    text: '李经理，关于报价和工期我都听到了，给我半天时间打个新版方案，今晚发您；同时我会争取约个见面机会，把细节当面对一下。',
    meta: ['语气：直接果断', '换一版 · 更短'],
  }
}

function dismissDraft() {
  draft.value.visible = false
  showDraftSection.value = false
}

function adjustDraft(tag) {
  // 假装重新生成，把 tag 加入 meta
  draft.value = {
    ...draft.value,
    text: tag.includes('简短') ?
      '李经理您好，报价我争取 5% 让利、工期 90 天可行。明天面聊一下细节？' :
      tag.includes('正式') ?
      '尊敬的李经理：关于您提到的报价及工期事项，我方已重新评估，可让利约 5%，工期也可压缩至 90 天（需分两批进场）。建议明日面谈细节。' :
      '李经理，报价 5% 让利 + 工期 90 天可行（设备分两批）。补充：产能方面我们二期已扩产 30%，可保进度。',
    meta: [`语气：${tag.replace('一点', '').replace('加一句关于', '加')}`, ...draft.value.meta.slice(1)],
  }
}

// route.params.id：纯数字 → 真后端 conversation id；非数字 → 仅 mock
const convId = /^\d+$/.test(String(route.params.id)) ? Number(route.params.id) : null

async function send() {
  const t = inputText.value.trim()
  if (!t || sending.value) return
  sending.value = true
  const now = new Date()
  const hh = String(now.getHours()).padStart(2, '0')
  const mm = String(now.getMinutes()).padStart(2, '0')
  // 检测 @AI
  const isAtAi = t.includes('@AI') || t.includes('@源助手')
  // 抓引用快照（clearRefs 之前）
  const refsSnapshot = mention.pendingRefs.value.length
    ? mention.pendingRefs.value.map(r => ({ type: r.type, item: r.item }))
    : null
  // 乐观插入用户消息（标记 _local + 内容 hash 用于轮询去重）
  const localId = `local-${Date.now()}`
  const nowMs = Date.now()
  messages.value.push({
    id: localId, kind: 'me', time: `今天 ${hh}:${mm}`, text: t,
    refs: refsSnapshot || undefined,
    _created_at_ms: nowMs,
    _local: true,
    _content: t,
  })
  inputText.value = ''
  mention.clearRefs()
  draft.value.visible = false
  showDraftSection.value = false
  await scrollToBottom()

  // 分支 1：私聊里 @源助手 → 走 AI SSE，AI 回复仅你可见（写入 DM 会话历史）
  if (isAtAi && convId) {
    const aiId = `ai-${Date.now()}`
    messages.value.push({
      id: aiId, kind: 'ai', time: `今天 ${String(new Date().getHours()).padStart(2,'0')}:${String(new Date().getMinutes()).padStart(2,'0')}`,
      body: { type: 'stream', text: '' },
    })
    await scrollToBottom()
    let streamed = ''
    try {
      await streamAi({
        content: t,
        conversationId: convId,
        onEvent: async (ev) => {
          const aiMsg = messages.value.find(m => m.id === aiId)
          if (!aiMsg) return
          if (ev.type === 'content') {
            streamed += ev.text || ''
            aiMsg.body = { type: 'stream', text: streamed }
            await scrollToBottom()
          } else if (ev.type === 'status') {
            aiMsg.body = { type: 'status', text: ev.message || '思考中…' }
          } else if (ev.type === 'error' || ev.type === 'context_exhausted') {
            aiMsg.body = { type: 'error', text: ev.message || 'AI 服务异常' }
          }
        },
      })
    } catch (e) {
      console.error('dm AI stream failed', e)
      const aiMsg = messages.value.find(m => m.id === aiId)
      if (aiMsg) aiMsg.body = { type: 'error', text: `连接失败：${e.message}` }
    } finally {
      sending.value = false
      await scrollToBottom()
    }
    return
  }

  // 分支 2：普通 DM 消息（含可能的 #/$ 引用卡）
  if (convId) {
    try { await apiSend(convId, t, null, refsSnapshot) }
    catch (e) { console.error('dm send failed', e) }
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
// 延迟 blur，防止点击 chip 时先触发 blur 把 chip 隐藏导致点击落空
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
const locationView = ref(null)        // {lat, lon} 用于查看模式
const locationMode = ref('share')

// 立即插入气泡（用原图预览）→ 后台压缩 + 上传
function insertOptimistic(file, kind, meta) {
  const localId = `local-up-${Date.now()}-${Math.random()}`
  const previewUrl = (kind === 'image') ? URL.createObjectURL(file) : ''
  messages.value.push({
    id: localId,
    kind: 'me',
    time: formatChatTime(new Date().toISOString()),
    text: '',
    attachment: {
      type: kind === 'voice' ? 'voice' : (kind === 'image' ? 'image' : 'file'),
      url: previewUrl,
      meta,
    },
    _local: true,
    _uploading: true,
    _previewUrl: previewUrl,
    _content: '',
    _created_at_ms: Date.now(),
  })
  scrollToBottom()
  return localId
}

async function processAndUpload(localId, file, kind, meta) {
  if (!convId) return
  let toUpload = file
  // 图片：后台压缩 + EXIF 翻正
  if (kind === 'image') {
    try { toUpload = await processImage(file) } catch {}
  }
  try {
    const r = await uploadChatFile(toUpload, kind, meta.name)
    const data = r.data?.data || r.data
    if (!data?.file_url) throw new Error('上传失败')
    const local = messages.value.find(m => m.id === localId)
    if (local) {
      local._uploading = false
      local._serverFileUrl = data.file_url   // 用作 server 消息精准匹配
    }
    await apiSend(convId, '', null, null, {
      message_type: kind === 'voice' ? 'voice' : (kind === 'image' ? 'image' : 'file'),
      file_url: data.file_url,
      file_meta: { ...meta, size: toUpload.size || meta.size },
    })
  } catch (e) {
    const local = messages.value.find(m => m.id === localId)
    if (local) local._error = e?.message || '上传失败'
    alert('上传失败：' + (e?.message || e))
  } finally {
    const local = messages.value.find(m => m.id === localId)
    if (local?._previewUrl) {
      setTimeout(() => URL.revokeObjectURL(local._previewUrl), 8000)
    }
  }
}

function onPickImages(files) {
  showPlusPanel.value = false
  // 立即所有原图气泡插入；压缩+上传都在背景里跑
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
  if (!convId) throw new Error('无效会话')
  const fullMeta = { lat, lon, name: meta.name || '', address: meta.address || '' }
  const localId = `local-loc-${Date.now()}`
  messages.value.push({
    id: localId, kind: 'me',
    time: formatChatTime(new Date().toISOString()), text: '',
    attachment: { type: 'location', url: '', meta: fullMeta },
    _local: true, _content: '', _created_at_ms: Date.now(),
  })
  await scrollToBottom()
  await apiSend(convId, '', null, null, {
    message_type: 'location', file_url: null, file_meta: fullMeta,
  })
}
async function onSendVoice(blob, durationSec) {
  const ext = (blob.type.includes('webm') ? 'webm' : 'm4a')
  const fname = `voice_${Date.now()}.${ext}`
  const f = new File([blob], fname, { type: blob.type })
  const meta = { name: fname, size: f.size, duration: durationSec }
  const id = insertOptimistic(f, 'voice', meta)
  processAndUpload(id, f, 'voice', meta)
}

// ── 消息长按 actions ──
const actionMessage = ref(null)
const lp = useLongPress((m) => { actionMessage.value = m })
function closeActions() { actionMessage.value = null }
function onRecalled({ id }) {
  const idx = messages.value.findIndex(m => m.id === id)
  if (idx >= 0) messages.value[idx] = { ...messages.value[idx], recalled: true, text: '', attachment: null, refs: null }
}
function onForwarded() { console.log('转发成功') }

// 增量轮询 + 已读回执
let lastMsgIso = null
const peerLastReadMs = ref(0)  // 对方上次已读时间（ms）
let msgPollTimer = null

function appendBackendMessage(m) {
  const id = `srv-${m.id}`
  if (messages.value.some(x => x.id === id)) return false

  const isMine = m.is_mine || m.is_self

  // 解析消息正文 + 引用卡 + 附件 meta
  let displayText = m.content
  let attachedRefs
  let attachment
  const isAttachment = ['image', 'file', 'voice', 'location'].includes(m.message_type)
  if (m.message_type === 'text_refs' && m.content) {
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

  const newMsg = {
    id,
    kind: isMine ? 'me' : 'them',
    time: formatChatTime(m.created_at),
    text: displayText,
    refs: attachedRefs || undefined,
    attachment,
    _created_at_ms: m.created_at ? new Date(m.created_at).getTime() : Date.now(),
    recalled: !!m.is_deleted,
  }

  // 如果是自己发的消息，找匹配的本地乐观消息 → 替换
  if (isMine) {
    let localIdx = -1
    if (isAttachment && m.file_url) {
      // 附件消息：上传完成后我们把 file_url 写到 local._serverFileUrl，靠它精准匹配
      localIdx = messages.value.findIndex(x => x._local && x._serverFileUrl === m.file_url)
    }
    if (localIdx < 0) {
      // 文本消息：用 _content + 30s 时间窗
      localIdx = messages.value.findIndex(x =>
        x._local && x._content === displayText &&
        Math.abs((x._created_at_ms || 0) - newMsg._created_at_ms) < 30000
      )
    }
    if (localIdx >= 0) {
      messages.value[localIdx] = newMsg
      return false
    }
  }

  messages.value.push(newMsg)
  return true
}

async function loadHistory() {
  if (!convId) return
  try {
    const res = await getMessages(convId, { limit: 50 })
    if (!res.data?.success) return
    const list = res.data.data || []
    list.forEach(appendBackendMessage)
    if (list.length) lastMsgIso = list[list.length - 1].created_at
    if (res.data.peer_last_read_at) {
      peerLastReadMs.value = new Date(res.data.peer_last_read_at).getTime()
    }
    // 顺便从消息里推断 peer 真实姓名（取第一条非我的消息的 sender_name）
    const otherMsg = list.find(m => !(m.is_mine || m.is_self) && m.sender_name)
    if (otherMsg && !route.query.name) {
      peer.value.name = otherMsg.sender_name
      peer.value.initial = otherMsg.sender_name[0]
    }
    await scrollToBottom()
    try { await markAsRead(convId) } catch {}
  } catch (e) {
    console.error('load dm history failed', e)
  }
}

async function pollNewMessages() {
  if (!convId) return
  try {
    const res = await getMessages(convId, { limit: 50, since: lastMsgIso })
    if (!res.data?.success) return
    const list = res.data.data || []
    let added = 0
    list.forEach(m => { if (appendBackendMessage(m)) added++ })
    if (list.length) lastMsgIso = list[list.length - 1].created_at
    if (res.data.peer_last_read_at) {
      peerLastReadMs.value = new Date(res.data.peer_last_read_at).getTime()
    }
    const recalledIds = res.data.recalled_ids || []
    recalledIds.forEach(({ id }) => {
      const idx = messages.value.findIndex(x => x.id === `srv-${id}`)
      if (idx >= 0) messages.value[idx] = { ...messages.value[idx], recalled: true, text: '', attachment: null, refs: null }
    })
    if (added > 0) {
      await scrollToBottom()
      try { await markAsRead(convId) } catch {}
    }
  } catch (e) {
    console.warn('dm poll failed', e)
  }
}

// 我发的某条消息 → 状态
//   'sending'   = 本地乐观（_local），尚未到服务器
//   'delivered' = 已到服务器（id 以 srv- 开头），对方未读
//   'read'      = 对方 last_read_at >= 该消息时间
function messageStatus(m) {
  if (m.kind !== 'me' || m.recalled) return null
  if (m._local) return 'sending'
  if (peerLastReadMs.value && m._created_at_ms && m._created_at_ms <= peerLastReadMs.value) {
    return 'read'
  }
  return 'delivered'
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
  await loadHistory()
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
      <button @click="router.back()" class="active:opacity-60 px-1">
        <svg width="9" height="14" viewBox="0 0 9 14">
          <path d="M7 1L1 7l6 6" fill="none" stroke="var(--color-ink-2)" stroke-width="1.6"
            stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <div class="w-[30px] h-[30px] rounded-full inline-flex items-center justify-center font-serif text-[13px] font-semibold"
        style="background: var(--color-accent-soft); color: var(--color-accent);">{{ peer.initial }}</div>
      <div class="flex-1 min-w-0">
        <div class="font-serif" style="font-size: 15px; font-weight: 600;">{{ peer.name }}</div>
        <div v-if="peer.role || peer.company" class="text-[11px]" style="color: var(--color-ink-3);">
          {{ [peer.role, peer.company].filter(Boolean).join(' · ') }}
        </div>
      </div>
      <span class="text-[18px]" style="color: var(--color-ink-3);">···</span>
    </div>

    <!-- Messages -->
    <div ref="scrollEl" class="flex-1 overflow-y-auto py-3" @click="blurInput">
      <template v-for="m in messages" :key="m.id">

        <!-- 日期分隔条 -->
        <div v-if="m.day" class="flex justify-center py-2">
          <span class="text-[10px] uppercase font-semibold px-3 py-1 rounded-full"
            style="background: var(--color-card); color: var(--color-ink-3);
                   border: 1px solid var(--color-divider); letter-spacing: 0.5px;">{{ m.day }}</span>
        </div>

        <!-- AI 流式回复（私聊里 @源助手 触发）-->
        <div v-if="m.kind === 'ai'" class="px-4 py-1.5 flex gap-2.5 items-start">
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
              <template v-if="m.body && m.body.type === 'stream'">
                <div class="whitespace-pre-wrap">{{ m.body.text || '…' }}</div>
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
            </div>
          </div>
        </div>

        <!-- 对方消息（带头像）-->
        <div v-else-if="m.kind === 'them'" class="px-4 py-1.5 flex gap-2.5">
          <div class="w-7 h-7 rounded-full inline-flex items-center justify-center font-serif text-[12px] font-semibold shrink-0"
            style="background: var(--color-accent-soft); color: var(--color-accent);">{{ peer.initial }}</div>
          <div class="flex-1 min-w-0">
            <div class="text-[11px] mb-1" style="color: var(--color-ink-3);">{{ m.time }}</div>
            <div v-if="m.recalled" class="text-[12px] italic"
              style="color: var(--color-ink-3);">{{ peer.name }} 撤回了一条消息</div>
            <template v-else>
              <!-- 文本气泡（含可能的引用卡）-->
              <div v-if="m.text || m.refs?.length" class="inline-block max-w-[300px]"
                style="background: var(--color-card); border: 1px solid var(--color-divider);
                       border-radius: 18px 18px 18px 4px; padding: 9px 13px;
                       font-size: 15px; line-height: 1.4; font-family: var(--font-sans);"
                @touchstart="lp.onTouchStart($event, m)"
                @touchmove="lp.onTouchMove"
                @touchend="lp.onTouchEnd"
                @touchcancel="lp.onTouchCancel">
                <MessageText v-if="m.text" :text="m.text" />
                <MessageRefs v-if="m.refs?.length" :refs="m.refs" :class="m.text ? 'mt-2' : ''" />
              </div>
              <!-- 附件（image / file / voice / location）-->
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
              <!-- 文件 -->
              <FileCard v-if="m.file" v-bind="m.file" :inverted="false" />
              <!-- 语音 -->
              <VoiceMsg v-if="m.voice" v-bind="m.voice" :inverted="false" />
            </template>
          </div>
        </div>

        <!-- 我的消息（右对齐 ink 黑底）-->
        <div v-else class="px-4 py-1.5 flex flex-col items-end">
          <div v-if="m.recalled" class="text-[12px] italic"
            style="color: var(--color-ink-3);">你撤回了一条消息</div>
          <template v-else>
          <!-- 文本气泡（含可能的引用卡）-->
          <div v-if="m.text || m.refs?.length" class="text-white max-w-[300px]"
            style="background: var(--color-ink); border-radius: 18px 18px 4px 18px;
                   padding: 9px 13px; font-size: 15px; line-height: 1.4; font-family: var(--font-sans);"
            @touchstart="lp.onTouchStart($event, m)"
            @touchmove="lp.onTouchMove"
            @touchend="lp.onTouchEnd"
            @touchcancel="lp.onTouchCancel">
            <MessageText v-if="m.text" :text="m.text" inverted />
            <MessageRefs v-if="m.refs?.length" :refs="m.refs" :class="m.text ? 'mt-2' : ''" />
          </div>
          <!-- 附件（image / file / voice / location）-->
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
          <!-- 文件 -->
          <FileCard v-if="m.file" v-bind="m.file" inverted class="mt-1.5" />
          <!-- 语音 -->
          <VoiceMsg v-if="m.voice" v-bind="m.voice" inverted class="mt-1.5" />
          <!-- 时间 + 已读回执 -->
          <div class="text-[10px] mt-1 inline-flex items-center gap-1" style="color: var(--color-ink-3);">
            <span>{{ m.time }}</span>
            <ReadReceipt :status="messageStatus(m)" />
          </div>
          </template>
        </div>
      </template>

      <!-- AI 草稿区（仅你可见）-->
      <template v-if="showDraftSection">
        <div class="py-3 px-4 flex justify-center">
          <span class="text-[10px] font-semibold tracking-wide px-2.5 py-1 rounded-full"
            style="color: #2F66D6; background: #E5EEFB;">✨ 仅你可见 · AI 草稿区</span>
        </div>

        <div v-if="draft.visible" class="px-4 py-1.5 flex gap-2.5 items-start">
          <PixelP :size="22" />
          <div class="flex-1 min-w-0">
            <div class="flex items-baseline gap-1.5 mb-1">
              <span class="text-[12px] font-semibold" style="color: #1E4FAA;">源助手</span>
              <span class="text-[10px]" style="color: var(--color-ink-3);">{{ draft.time }}</span>
            </div>
            <div class="font-serif"
              style="background: rgba(47,102,214,0.06); border: 1px solid rgba(47,102,214,0.18);
                     border-radius: 4px 14px 14px 14px; padding: 12px 14px;
                     font-size: 14px; line-height: 1.55; color: var(--color-ink);">
              <div class="text-[11px] font-semibold mb-1.5" style="color: #2F66D6;">{{ draft.label }}</div>
              <div class="rounded-lg p-3 mt-1 font-serif"
                style="background: var(--color-card); border: 1px dashed var(--color-divider-strong);
                       line-height: 1.6; color: var(--color-ink);">
                {{ draft.text }}
              </div>
              <div class="flex flex-wrap gap-1.5 mt-2">
                <span v-for="(tag, i) in draft.meta" :key="i"
                  class="text-[10px] px-2 py-0.5 rounded-full font-serif italic"
                  style="background: rgba(47,102,214,0.06); color: var(--color-ink-3);">{{ tag }}</span>
              </div>
            </div>

            <!-- 操作行 -->
            <div class="flex gap-2 mt-2">
              <button @click="adoptDraft"
                class="flex-1 py-2.5 rounded-xl text-white text-[13px] font-semibold active:opacity-80"
                style="background: #2F66D6; border: none;">采用 · 填入输入框</button>
              <button @click="regenerateDraft"
                class="px-3.5 py-2.5 rounded-xl text-[13px] active:opacity-70"
                style="background: var(--color-card); color: var(--color-ink-2); border: 1px solid var(--color-divider-strong);">换一版</button>
              <button @click="dismissDraft"
                class="px-3.5 py-2.5 rounded-xl text-[13px] active:opacity-70"
                style="background: var(--color-card); color: var(--color-ink-2); border: 1px solid var(--color-divider-strong);">×</button>
            </div>

            <!-- 微调追问 chip -->
            <div class="flex flex-wrap gap-1.5 mt-2">
              <button v-for="t in SUGGEST_TAGS" :key="t" @click="adjustDraft(t)"
                class="text-[12px] font-serif italic px-3 py-1.5 rounded-full active:opacity-70"
                style="background: var(--color-card); color: var(--color-ink-2);
                       border: 1px solid var(--color-divider-strong);">{{ t }}</button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Composer (含 @ 提及 popover) -->
    <div class="shrink-0 safe-bottom relative"
      style="background: var(--color-card); border-top: 1px solid var(--color-divider);">

      <MentionPopover
        :visible="mention.popoverVisible.value"
        :type="mention.popoverType.value"
        :query="mention.popoverQuery.value"
        ai-only
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
            :placeholder="`给${peer.name}回复…`"
            @input="handleInput"
            @keyup.enter="send"
            @focus="onComposerFocus"
            @blur="onComposerBlur"
            :disabled="sending"
            class="flex-1 bg-transparent outline-none text-[15px]"
            style="color: var(--color-ink); font-family: var(--font-sans);" />
        </div>
        <button v-if="inputText.trim()" @click="send" :disabled="sending"
          class="w-9 h-9 rounded-full inline-flex items-center justify-center text-[14px] font-bold text-white disabled:opacity-40 shrink-0"
          style="background: var(--color-accent);">↑</button>
        <!-- 麦克风 → 打开录音 sheet -->
        <button v-else type="button" @click="showVoiceSheet = true"
          class="w-9 h-9 rounded-full inline-flex items-center justify-center shrink-0"
          style="background: var(--color-bg); border: 1px solid var(--color-divider-strong);">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="6" y="2" width="4" height="8" rx="2" stroke="var(--color-ink-2)" stroke-width="1.4"/>
            <path d="M3.5 8a4.5 4.5 0 009 0M8 12.5V14" stroke="var(--color-ink-2)" stroke-width="1.4" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <!-- + 展开面板 -->
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
