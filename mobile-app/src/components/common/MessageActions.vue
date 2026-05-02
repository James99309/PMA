<script setup>
// 消息长按 action sheet（复制 / 转发 / 撤回） + 转发 sheet
// 父组件传入 message（null 关闭），通过 events 收回结果
import { ref, computed, watch } from 'vue'
import { recallMessage, forwardMessage, getConversations, searchUsers } from '@/api/chat'

const props = defineProps({
  message: { type: Object, default: null },
  isMine: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'recalled', 'forwarded'])

// ── 转发 sheet 状态
const showForward = ref(false)
const fwdNote = ref('')
const fwdConvs = ref([])
const fwdConvsLoading = ref(false)
const fwdSelected = ref(new Set())
const fwdUserSearch = ref('')
const fwdUserResults = ref([])
const fwdUserSelected = ref([])
const fwdSearching = ref(false)
const fwdSubmitting = ref(false)
let fwdSearchTimer = null

// 关闭时重置子 sheet
watch(() => props.message, (m) => { if (!m) showForward.value = false })

// 解析真实后端消息 ID（'srv-123' → 123；纯数字 → 123；其他 → null）
const realMsgId = computed(() => {
  const id = props.message?.id
  if (id == null) return null
  const s = String(id)
  const m = s.match(/^srv-(\d+)$/)
  if (m) return Number(m[1])
  if (/^\d+$/.test(s)) return Number(s)
  return null
})

const canRecall = computed(() => {
  if (!props.isMine || !realMsgId.value) return false
  // 没时间戳就让后端校验
  const t = props.message?._created_at_ms
  if (!t) return true
  return Date.now() - t < 2 * 60 * 1000
})

async function openForward() {
  showForward.value = true
  fwdSelected.value = new Set()
  fwdUserSelected.value = []
  fwdUserResults.value = []
  fwdUserSearch.value = ''
  fwdNote.value = ''
  fwdConvsLoading.value = true
  try {
    const r = await getConversations()
    fwdConvs.value = r.data?.success
      ? (r.data.data || []).filter(c => c.type !== 'ai')
      : []
  } finally {
    fwdConvsLoading.value = false
  }
}

function toggleConv(c) {
  const next = new Set(fwdSelected.value)
  if (next.has(c.id)) next.delete(c.id)
  else next.add(c.id)
  fwdSelected.value = next
}
function isConvSelected(c) { return fwdSelected.value.has(c.id) }

function onUserSearchInput() {
  clearTimeout(fwdSearchTimer)
  fwdSearchTimer = setTimeout(async () => {
    const q = fwdUserSearch.value.trim()
    if (!q) { fwdUserResults.value = []; return }
    fwdSearching.value = true
    try {
      const r = await searchUsers(q)
      const all = r.data?.success ? (r.data.data || []) : []
      const exist = new Set(fwdUserSelected.value.map(u => u.id))
      fwdUserResults.value = all.filter(u => !exist.has(u.id))
    } finally {
      fwdSearching.value = false
    }
  }, 250)
}

function pickUser(u) {
  if (fwdUserSelected.value.some(x => x.id === u.id)) return
  fwdUserSelected.value.push(u)
  fwdUserResults.value = fwdUserResults.value.filter(x => x.id !== u.id)
}
function unpickUser(u) {
  fwdUserSelected.value = fwdUserSelected.value.filter(x => x.id !== u.id)
}

const fwdCount = computed(() => fwdSelected.value.size + fwdUserSelected.value.length)

async function confirmForward() {
  if (!fwdCount.value || fwdSubmitting.value) return
  if (!realMsgId.value) {
    alert('该消息无法转发（仅本地）')
    return
  }
  fwdSubmitting.value = true
  try {
    const r = await forwardMessage(
      realMsgId.value,
      [...fwdSelected.value],
      fwdUserSelected.value.map(u => u.id),
      fwdNote.value.trim() || null,
    )
    if (r.data?.success) {
      emit('forwarded')
      emit('close')
    } else {
      alert(r.data?.message || '转发失败')
    }
  } catch (e) {
    alert(`转发失败：${e.message || e}`)
  } finally {
    fwdSubmitting.value = false
  }
}

async function doRecall() {
  if (!canRecall.value) return
  if (!confirm('撤回这条消息？')) return
  try {
    const r = await recallMessage(realMsgId.value)
    if (r.data?.success) {
      emit('recalled', { id: props.message.id, realId: realMsgId.value })
      emit('close')
    } else {
      alert(r.data?.message || '撤回失败')
    }
  } catch (e) {
    alert(`撤回失败：${e.message || e}`)
  }
}

async function doCopy() {
  const text = props.message?.text || ''
  try {
    if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(text)
    else {
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select(); document.execCommand('copy'); ta.remove()
    }
  } catch {}
  emit('close')
}

function close() { emit('close') }
</script>

<template>
  <Teleport to="body">
    <!-- 顶级 action sheet：复制 / 转发 / 撤回 -->
    <transition name="ma">
      <div v-if="message && !showForward"
        class="fixed inset-0 z-[60] flex flex-col"
        style="background: rgba(0,0,0,0.32);" @click.self="close">
        <div class="mt-auto"
          style="padding-bottom: calc(env(safe-area-inset-bottom) + 8px);">
          <div class="mx-3 rounded-2xl overflow-hidden"
            style="background: var(--color-card);">
            <button @click="doCopy"
              class="w-full px-4 py-4 text-[15px] active:bg-bg"
              style="border-bottom: 1px solid var(--color-divider);">复制</button>
            <button @click="openForward"
              class="w-full px-4 py-4 text-[15px] active:bg-bg"
              :style="canRecall ? 'border-bottom: 1px solid var(--color-divider);' : ''">转发</button>
            <button v-if="canRecall" @click="doRecall"
              class="w-full px-4 py-4 text-[15px] active:bg-bg"
              style="color: #A04848;">撤回</button>
          </div>
          <div class="mx-3 mt-2 rounded-2xl"
            style="background: var(--color-card);">
            <button @click="close"
              class="w-full px-4 py-4 text-[15px] font-semibold active:bg-bg">取消</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 转发 sheet -->
    <transition name="ma">
      <div v-if="showForward"
        class="fixed inset-0 z-[70] flex flex-col"
        style="background: rgba(0,0,0,0.32);" @click.self="close">
        <div class="mt-auto rounded-t-3xl flex flex-col"
          style="background: var(--color-bg); max-height: 88vh; min-height: 60vh;">
          <div class="px-5 pt-4 pb-2 flex items-center justify-between shrink-0">
            <button @click="close" class="text-[13px]"
              style="color: var(--color-ink-3);">取消</button>
            <span class="font-serif" style="font-size: 16px; font-weight: 500;">转发消息</span>
            <button @click="confirmForward"
              :disabled="!fwdCount || fwdSubmitting"
              class="text-[13px] font-medium disabled:opacity-40"
              style="color: var(--color-accent);">
              {{ fwdSubmitting ? '发送中…' : `转发${fwdCount ? `(${fwdCount})` : ''}` }}
            </button>
          </div>

          <div v-if="fwdUserSelected.length" class="px-5 pb-2 flex flex-wrap gap-1.5 shrink-0">
            <span v-for="u in fwdUserSelected" :key="u.id"
              class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[12px]"
              style="background: var(--color-accent-soft); color: var(--color-accent);">
              {{ u.name }}
              <button @click="unpickUser(u)"
                class="ml-0.5 text-[14px] leading-none active:opacity-60">×</button>
            </span>
          </div>

          <div class="px-5 pb-2 shrink-0">
            <input v-model="fwdUserSearch" @input="onUserSearchInput"
              type="text" placeholder="搜索用户（创建新私聊转发）"
              class="w-full px-4 py-2.5 rounded-xl text-[14px]"
              style="background: var(--color-card); border: 1px solid var(--color-divider); outline: none;" />
          </div>

          <div class="flex-1 overflow-y-auto">
            <div v-if="fwdSearching" class="px-3 py-3 text-center">
              <div class="inline-block w-4 h-4 border-2 rounded-full animate-spin"
                style="border-color: var(--color-accent); border-top-color: transparent;" />
            </div>
            <div v-else-if="fwdUserResults.length" class="px-3 pb-2">
              <div class="text-[11px] font-semibold uppercase px-3 py-1.5"
                style="color: var(--color-ink-3); letter-spacing: 1px;">搜索结果</div>
              <button v-for="u in fwdUserResults" :key="u.id"
                @click="pickUser(u)"
                class="w-full flex items-center gap-3 px-3 py-2.5 active:bg-bg text-left rounded-xl">
                <div class="w-8 h-8 rounded-full inline-flex items-center justify-center font-serif text-[12px] font-semibold"
                  style="background: var(--color-accent-soft); color: var(--color-accent);">{{ u.avatar || u.name?.[0] || '?' }}</div>
                <div class="flex-1 min-w-0">
                  <div class="font-serif truncate" style="font-size: 14px;">{{ u.name }}</div>
                  <div v-if="u.dept" class="text-[11px] truncate" style="color: var(--color-ink-3);">{{ u.dept }}</div>
                </div>
              </button>
            </div>

            <div class="px-3 pb-2">
              <div class="text-[11px] font-semibold uppercase px-3 py-1.5"
                style="color: var(--color-ink-3); letter-spacing: 1px;">最近会话</div>
              <div v-if="fwdConvsLoading" class="py-6 text-center">
                <div class="inline-block w-5 h-5 border-2 rounded-full animate-spin"
                  style="border-color: var(--color-accent); border-top-color: transparent;" />
              </div>
              <div v-else-if="!fwdConvs.length" class="py-6 text-center text-[13px]"
                style="color: var(--color-ink-3);">暂无可转发的会话</div>
              <button v-else v-for="c in fwdConvs" :key="c.id"
                @click="toggleConv(c)"
                class="w-full flex items-center gap-3 px-3 py-2.5 active:bg-bg text-left rounded-xl">
                <div class="w-9 h-9 rounded-2xl inline-flex items-center justify-center font-serif text-[14px] font-semibold shrink-0"
                  style="background: var(--color-accent-soft); color: var(--color-accent);">{{ (c.name || '群')[0] }}</div>
                <div class="flex-1 min-w-0">
                  <div class="font-serif truncate" style="font-size: 14px; font-weight: 500;">{{ c.name || '群聊' }}</div>
                  <div class="text-[11px]" style="color: var(--color-ink-3);">
                    {{ c.type === 'private' ? '私聊' : c.type === 'group' ? '群聊' : c.type }}
                  </div>
                </div>
                <div class="w-5 h-5 rounded inline-flex items-center justify-center text-[11px] text-white"
                  :style="{
                    background: isConvSelected(c) ? 'var(--color-accent)' : 'transparent',
                    border: isConvSelected(c) ? 'none' : '1.5px solid var(--color-divider-strong)',
                  }">
                  <span v-if="isConvSelected(c)">✓</span>
                </div>
              </button>
            </div>

            <div class="px-5 pb-6">
              <div class="text-[11px] font-semibold uppercase mb-1.5"
                style="color: var(--color-ink-3); letter-spacing: 1px;">附言（可选）</div>
              <textarea v-model="fwdNote" rows="2" placeholder="添加附言…"
                class="w-full px-3 py-2 rounded-xl text-[13px]"
                style="background: var(--color-card); border: 1px solid var(--color-divider); outline: none; resize: none;" />
            </div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.ma-enter-active, .ma-leave-active { transition: opacity .18s; }
.ma-enter-from, .ma-leave-to { opacity: 0; }
</style>
