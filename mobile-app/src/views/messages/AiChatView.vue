<script setup>
// AI 一对一对话 —— 严格对齐 ai-chat.jsx AIOneOnOne (line 148-223)
// 真接 SSE：POST /api/v1/mobile/chat/ai/stream
import { ref, nextTick, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import PixelP from '@/components/common/PixelP.vue'
import { streamAi, getMessages, markAsRead } from '@/api/chat'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'

const { kbStyle } = useKeyboardOffset()

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// 现有 AI 会话 id（从 ChatListView 跳过来时带 query.id；否则首次发消息时由后端创建）
const conversationId = ref(route.query.id ? Number(route.query.id) : null)

const messages = ref([
  // 设计稿初始 demo 对话（line 169-194）
  { id: 1, kind: 'user', time: '14:21', text: '帮我分析一下宝山节能这个客户的赢率怎么样？最近的项目有几个有戏？' },
  {
    id: 2, kind: 'ai', time: '14:21', thinking: false,
    body: 'rich-1',
    showActions: true,
  },
])

const showSuggest1 = ref(true)
const inputText = ref('')
const sending = ref(false)
const scrollEl = ref(null)

const QUICK_CMDS = computed(() => [
  t('chat.aiSugDraft'), t('chat.aiSugWinrate'), t('chat.aiSugSummarize'),
  t('chat.aiSugContract'), t('chat.aiSugContacts'),
])
// SUGGEST_TAGS_1 是 demo seed 提示, 暂保留中文(只在没有 backend mock 时显示)
const SUGGEST_TAGS_1 = ['这个项目下一步该做什么？', '帮我起草约见短信', '其他客户对比一下']

async function scrollToBottom() {
  await nextTick()
  if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
}

function pushUser(text) {
  const now = new Date()
  const hh = String(now.getHours()).padStart(2, '0')
  const mm = String(now.getMinutes()).padStart(2, '0')
  messages.value.push({
    id: Date.now(),
    kind: 'user',
    time: `${hh}:${mm}`,
    text,
  })
}

function pushAiThinking() {
  const now = new Date()
  const hh = String(now.getHours()).padStart(2, '0')
  const mm = String(now.getMinutes()).padStart(2, '0')
  const id = Date.now() + 1
  messages.value.push({
    id, kind: 'ai', time: `${hh}:${mm}`, thinking: true, body: null, showActions: false,
  })
  return id
}

function replaceAiResponse(id, body) {
  const idx = messages.value.findIndex(m => m.id === id)
  if (idx >= 0) {
    messages.value[idx] = { ...messages.value[idx], thinking: false, body, showActions: true }
  }
}

// Mock 回复内容（不同 query 显示不同内容）
function mockReply(query) {
  if (query.includes('约见') || query.includes('短信')) {
    return {
      type: 'draft',
      label: '建议回复 · 已结合客户偏好与历史互动',
      text: '李经理您好，关于您说的方案，我希望本周能登门拜访 30 分钟，把更新版当面对一遍，您看周三或周四下午方便吗？',
    }
  }
  if (query.includes('对比')) {
    return {
      type: 'compare',
      title: '已为你对比 3 家客户（按累计价值倒序）',
      items: [
        { name: '深圳明远半导体', value: '620.00 万', tag: 'A 类活跃' },
        { name: '上海宝山节能科技', value: '380.50 万', tag: 'A 类活跃' },
        { name: '南京数据港集团', value: '256.00 万', tag: 'A 类活跃' },
      ],
    }
  }
  // 默认
  return {
    type: 'analysis',
    intro: '结合我看到的数据，宝山节能整体赢率较高（约 72%），主要原因有三点：',
    points: [
      '是老客户，过往合作 2 个签约项目',
      '主要联系人 李华（采购部经理）对你信任度高',
      '名下进行中 3 个项目，其中 1 个已到「招标中」',
    ],
    cardLead: '名下项目中，「宝山节能改造项目」最值得重点跟进：',
    refCard: { name: '宝山节能改造项目', stage: '招标中', amount: '42.50' },
    footer: '数据来源：6 个名下项目 · 12 条跟进记录 · 上次拜访 04 · 22',
  }
}

async function send(text) {
  const t = (text ?? inputText.value).trim()
  if (!t || sending.value) return
  sending.value = true
  showSuggest1.value = false
  pushUser(t)
  inputText.value = ''
  await scrollToBottom()

  // AI 流式回复
  const tid = pushAiThinking()
  await scrollToBottom()

  // 在 thinking 气泡里累加 streamed content（用临时 body 'streaming' + streamText）
  let streamedText = ''
  const streamMsg = messages.value.find(m => m.id === tid)
  if (streamMsg) {
    streamMsg.body = { type: 'stream', text: '' }
    streamMsg.thinking = false  // 流开始就不再显示 ... 转圈
  }

  try {
    await streamAi({
      content: t,
      conversationId: conversationId.value,
      onEvent: async (ev) => {
        if (ev.type === 'content') {
          streamedText += ev.text || ''
          if (streamMsg) {
            streamMsg.body = { type: 'stream', text: streamedText }
          }
          await scrollToBottom()
        } else if (ev.type === 'status') {
          if (streamMsg) streamMsg.body = { type: 'status', text: ev.message || t('chat.aiThinking') }
        } else if (ev.type === 'done') {
          // 后端把 conversation_id 回传，存下来，后续消息复用同一个会话
          if (ev.conversation_id) conversationId.value = ev.conversation_id
          if (streamMsg) streamMsg.showActions = true
        } else if (ev.type === 'error') {
          if (streamMsg) streamMsg.body = { type: 'error', text: ev.message || t('chat.aiServiceError') }
        } else if (ev.type === 'context_exhausted') {
          if (streamMsg) streamMsg.body = { type: 'error', text: t('chat.aiCtxFull') }
        }
      },
    })
  } catch (e) {
    console.error('AI stream failed', e)
    if (streamMsg) streamMsg.body = { type: 'error', text: `${t('chat.connectFail')}${e.message}` }
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

// 进入页面时拉历史（如果有 conversationId）
async function loadHistory() {
  if (!conversationId.value) return
  try {
    const res = await getMessages(conversationId.value, { limit: 50 })
    if (!res.data?.success) return
    const list = res.data.data || []
    // 替换初始 demo 消息为真历史
    if (list.length > 0) messages.value = []
    list.forEach(m => {
      const isMine = m.is_mine || m.is_self
      const isAi = m.is_ai_response
      messages.value.push({
        id: `srv-${m.id}`,
        kind: isAi ? 'ai' : 'user',
        time: m.created_at_short || m.created_at,
        text: isAi ? undefined : m.content,
        body: isAi ? { type: 'stream', text: m.content } : undefined,
        showActions: isAi,
      })
    })
    await scrollToBottom()
    try { await markAsRead(conversationId.value) } catch {}
  } catch (e) {
    console.error('load AI history failed', e)
  }
}

function pickQuick(cmd) {
  inputText.value = cmd + ' '
}

function pickSuggest(tag) {
  send(tag)
}

onMounted(async () => {
  await scrollToBottom()
  await loadHistory()
})
</script>

<template>
  <div class="flex flex-col h-full" :style="[{ background: 'var(--color-bg)' }, kbStyle]">

    <!-- Nav -->
    <div class="flex items-center gap-2.5 px-4 py-2 shrink-0"
      style="background: var(--color-card); border-bottom: 1px solid var(--color-divider);">
      <button @click="router.back()" class="active:opacity-60 px-1">
        <svg width="9" height="14" viewBox="0 0 9 14">
          <path d="M7 1L1 7l6 6" fill="none" stroke="var(--color-ink-2)" stroke-width="1.6"
            stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <PixelP :size="26" />
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-1.5">
          <span class="font-serif" style="font-size: 15px; font-weight: 600;">{{ t('chat.aiAssistant') }}</span>
          <span class="text-[9px] font-bold px-1.5 py-px rounded"
            style="color: #2F66D6; background: #E5EEFB;">BETA</span>
        </div>
        <div class="text-[11px] mt-px" style="color: var(--color-green);">{{ t('chat.aiOnline') }}</div>
      </div>
      <span class="text-[18px]" style="color: var(--color-ink-3);">···</span>
    </div>

    <!-- Messages -->
    <div ref="scrollEl" class="flex-1 overflow-y-auto py-3">
      <template v-for="m in messages" :key="m.id">
        <!-- User bubble -->
        <div v-if="m.kind === 'user'" class="px-4 py-1.5 flex flex-col items-end">
          <div class="font-serif"
            style="background: var(--color-ink); color: #fff; border-radius: 14px 14px 4px 14px;
                   padding: 10px 14px; max-width: 300px; font-size: 14px; line-height: 1.5;">
            {{ m.text }}
          </div>
          <div class="text-[10px] mt-1" style="color: var(--color-ink-3);">{{ m.time }}</div>
        </div>

        <!-- AI bubble -->
        <div v-else class="px-4 py-1.5 flex gap-2.5 items-start">
          <PixelP :size="22" />
          <div class="flex-1 min-w-0">
            <div class="flex items-baseline gap-1.5 mb-1">
              <span class="text-[12px] font-semibold" style="color: #1E4FAA;">{{ t('chat.aiAssistant') }}</span>
              <span class="text-[10px]" style="color: var(--color-ink-3);">{{ m.time }}</span>
            </div>
            <!-- bubble container -->
            <div class="font-serif"
              style="background: rgba(47,102,214,0.06); border: 1px solid rgba(47,102,214,0.18);
                     border-radius: 4px 14px 14px 14px; padding: 12px 14px;
                     font-size: 14px; line-height: 1.55; color: var(--color-ink);">
              <!-- thinking -->
              <div v-if="m.thinking" class="flex items-center gap-2 py-1">
                <span class="inline-flex gap-1">
                  <span v-for="i in 3" :key="i"
                    class="w-1.5 h-1.5 rounded-full" style="background: #2F66D6;"
                    :style="{ animation: `aiDot 1.4s ${(i-1)*0.16}s infinite` }" />
                </span>
                <span class="text-[12px] italic" style="color: var(--color-ink-3);">{{ t('chat.aiAnalyzingData') }}</span>
              </div>

              <!-- 真后端流式输出 -->
              <template v-else-if="m.body && m.body.type === 'stream'">
                <div class="whitespace-pre-wrap">{{ m.body.text }}</div>
              </template>
              <!-- AI 工具状态 -->
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
              <!-- 错误 -->
              <template v-else-if="m.body && m.body.type === 'error'">
                <div class="text-[13px]" style="color: #A04848;">⚠️ {{ m.body.text }}</div>
              </template>

              <!-- mock 分析回复（保留为兜底，后端不到时可手动触发）-->
              <template v-else-if="m.body && m.body.type === 'analysis'">
                <div>{{ m.body.intro }}</div>
                <ol style="margin: 8px 0; padding-left: 20px; line-height: 1.8;">
                  <li v-for="(p, i) in m.body.points" :key="i">{{ p }}</li>
                </ol>
                <div>{{ m.body.cardLead }}</div>
                <!-- 引用项目卡 -->
                <div class="mt-2 flex gap-2.5 items-center rounded-xl px-3 py-2.5"
                  style="background: var(--color-card); border: 1px solid var(--color-divider-strong);">
                  <div class="w-8 h-8 rounded-lg inline-flex items-center justify-center text-[13px] font-bold"
                    style="background: var(--color-ink); color: #fff;">#</div>
                  <div class="flex-1 min-w-0">
                    <div class="font-serif" style="font-size: 13px; font-weight: 500; line-height: 1.3;">{{ m.body.refCard.name }}</div>
                    <div class="flex gap-2 mt-0.5 text-[11px]" style="color: var(--color-ink-3);">
                      <span style="color: var(--color-accent); font-weight: 600;">● {{ m.body.refCard.stage }}</span>
                      <span>·</span>
                      <span class="tabular" style="color: var(--color-ink); font-weight: 600;">{{ t('project.amountWan', { amount: m.body.refCard.amount }) }}</span>
                    </div>
                  </div>
                  <span class="text-[14px]" style="color: var(--color-ink-3);">›</span>
                </div>
                <div class="text-[11px] mt-2.5 italic" style="color: var(--color-ink-3);">{{ m.body.footer }}</div>
              </template>

              <!-- 起草回复 -->
              <template v-else-if="m.body && m.body.type === 'draft'">
                <div class="text-[11px] font-semibold mb-1.5" style="color: #2F66D6;">{{ m.body.label }}</div>
                <div class="rounded-lg p-3 mt-1"
                  style="background: var(--color-card); border: 1px dashed var(--color-divider-strong); line-height: 1.6;">
                  {{ m.body.text }}
                </div>
                <button @click="inputText = m.body.text"
                  class="mt-2 text-[12px] font-medium active:opacity-60"
                  style="color: #2F66D6;">{{ t('chat.aiAdoptDraft') }}</button>
              </template>

              <!-- 对比客户 -->
              <template v-else-if="m.body && m.body.type === 'compare'">
                <div class="text-[11px] font-semibold mb-1.5" style="color: #2F66D6;">📊 {{ m.body.title }}</div>
                <div v-for="(it, i) in m.body.items" :key="i"
                  class="flex items-center justify-between py-2"
                  :style="i < m.body.items.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
                  <div>
                    <div class="font-serif" style="font-size: 13px; font-weight: 500;">{{ it.name }}</div>
                    <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">{{ it.tag }}</div>
                  </div>
                  <div class="text-[14px] font-semibold tabular">¥{{ it.value }}</div>
                </div>
              </template>
            </div>

            <!-- 操作行 -->
            <div v-if="m.showActions" class="flex gap-3.5 mt-1.5 text-[11px]" style="color: var(--color-ink-3);">
              <span class="inline-flex items-center gap-1 active:opacity-60">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M3 6h6M6 3l3 3-3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
                </svg>{{ t('chat.aiRegen') }}
              </span>
              <span class="inline-flex items-center gap-1 active:opacity-60">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <rect x="2" y="2" width="6" height="8" rx="1" stroke="currentColor" stroke-width="1.2" />
                  <path d="M4 5h2M4 7h2" stroke="currentColor" stroke-width="1.2" />
                </svg>{{ t('chat.aiCopy') }}
              </span>
              <span>👍</span>
              <span>👎</span>
            </div>
          </div>
        </div>
      </template>

      <!-- 第一轮回复后的建议追问 chip -->
      <div v-if="showSuggest1" class="px-4 pl-[54px] py-1.5 flex flex-wrap gap-1.5">
        <button v-for="t in SUGGEST_TAGS_1" :key="t"
          @click="pickSuggest(t)"
          class="text-[12px] font-serif italic px-3 py-1.5 rounded-full active:opacity-70"
          style="background: var(--color-card); color: var(--color-ink-2);
                 border: 1px solid var(--color-divider-strong);">{{ t }}</button>
      </div>
    </div>

    <!-- Composer -->
    <div class="shrink-0 safe-bottom"
      style="background: var(--color-card); border-top: 1px solid var(--color-divider);">
      <!-- 快速指令 chip 行 -->
      <div class="px-3 pt-2 pb-1.5 flex gap-1.5 overflow-x-auto no-scrollbar">
        <button v-for="cmd in QUICK_CMDS" :key="cmd"
          @click="pickQuick(cmd)"
          class="shrink-0 text-[11px] px-2.5 py-1 rounded-full"
          style="color: #2F66D6; background: #E5EEFB; font-family: ui-monospace, monospace;">{{ cmd }}</button>
      </div>
      <!-- 输入框行 -->
      <div class="px-3 pt-1 pb-3 flex items-center gap-2">
        <button class="w-9 h-9 rounded-full inline-flex items-center justify-center text-[18px]"
          style="background: var(--color-bg); border: 1px solid var(--color-divider-strong); color: var(--color-ink-2);">+</button>
        <div class="flex-1 rounded-full px-3.5 py-2.5 flex items-center"
          style="background: var(--color-bg); border: 1.5px solid #2F66D6;">
          <input v-model="inputText" type="text"
            :placeholder="t('chat.aiAskPh')"
            @keyup.enter="send()"
            :disabled="sending"
            class="flex-1 bg-transparent outline-none font-serif text-[14px]"
            style="color: var(--color-ink);" />
        </div>
        <button @click="send()" :disabled="sending || !inputText.trim()"
          class="w-9 h-9 rounded-full inline-flex items-center justify-center text-[14px] font-bold text-white disabled:opacity-40"
          style="background: #2F66D6;">↑</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes aiDot {
  0%, 80%, 100% { opacity: 0.3; }
  40% { opacity: 1; }
}
</style>
