<script setup>
// @/#/$ 3 维提及选择器
// 接真后端搜索：@用户（按 conv/project scope 限制）/ #项目 / $客户
import { computed, ref, watch } from 'vue'
import { searchUsers, searchProjects, searchCompanies } from '@/api/chat'

const props = defineProps({
  visible: { type: Boolean, default: false },
  type:    { type: String, default: '@' },   // '@' | '#' | '$'
  query:   { type: String, default: '' },
  aiOnly:  { type: Boolean, default: false }, // 私聊场景：@ 只显示源助手
  // 群成员 scope（@ 用户搜索时强制限制范围，避免全局 @）
  convId:    { type: [Number, String], default: null },
  projectId: { type: [Number, String], default: null },
})

const emit = defineEmits(['select', 'switch-type', 'close'])

// 真后端结果缓存
const apiResults = ref({ '@': [], '#': [], '$': [] })
const loading = ref(false)
const lastFetchKey = ref('')

const TYPE_META = {
  '@': { label: '提及成员' },
  '#': { label: '引用项目' },
  '$': { label: '引用客户' },
}

const meta = computed(() => TYPE_META[props.type] || TYPE_META['@'])

// 把后端返回标准化为 { id, name, ... } 形式（render 里要 name 字段）
function normalizeUsers(rows) {
  return rows.map(u => ({
    id: u.id,
    name: u.name,
    role: u.dept || '',
    initial: u.avatar || (u.name || '?')[0],
  }))
}
function normalizeProjects(rows) {
  return rows.map(p => ({
    id: p.id,
    name: p.project_name,
    stage: p.current_stage || '',
    amount: ((p.quotation_customer || 0) / 10000).toFixed(2),
    owner: p.owner_name || '',
    region: p.city || '',
  }))
}
function normalizeCompanies(rows) {
  return rows.map(c => ({
    id: c.id,
    name: c.company_name,
    tier: '',
    value: '',
    contact: [c.contact_name, c.contact_position].filter(Boolean).join(' · '),
  }))
}

// AI-only 模式（私聊场景）：@ 只显示源助手，不调用 /users/search
const AI_ONLY_USERS = [
  { id: 'ai', name: '源助手', role: 'AI 助手 · BETA', initial: 'P', isAi: true },
]

// 真后端搜索（防抖式：每个 type+query 只发一次）
async function fetchIfNeeded() {
  const t = props.type
  const q = props.query
  const key = `${t}::${q}::${props.aiOnly}::${props.convId}::${props.projectId}`
  if (key === lastFetchKey.value) return
  lastFetchKey.value = key

  // 私聊 @ 限制
  if (t === '@' && props.aiOnly) {
    const ql = (q || '').toLowerCase()
    apiResults.value['@'] = ql
      ? AI_ONLY_USERS.filter(u => u.name.toLowerCase().includes(ql))
      : AI_ONLY_USERS
    return
  }

  loading.value = true
  try {
    if (t === '@') {
      const scope = {
        conversationId: props.convId || undefined,
        projectId: props.projectId || undefined,
      }
      const r = await searchUsers(q, scope)
      let list = r.data?.success ? normalizeUsers(r.data.data || []) : []
      // 在群聊 / 项目讨论：AI（源助手）总是可被 @
      if (props.convId || props.projectId) {
        const ql = (q || '').toLowerCase()
        if (!ql || '源助手'.includes(ql) || 'ai'.includes(ql)) {
          list = [{ id: 'ai', name: '源助手', role: 'AI 助手 · BETA', initial: 'P', isAi: true }, ...list]
        }
      }
      apiResults.value['@'] = list
    } else if (t === '#') {
      const r = await searchProjects(q)
      if (r.data?.success) apiResults.value['#'] = normalizeProjects(r.data.data || [])
    } else if (t === '$') {
      const r = await searchCompanies(q)
      if (r.data?.success) apiResults.value['$'] = normalizeCompanies(r.data.data || [])
    }
  } catch (e) {
    console.error('mention search failed', t, q, e)
  } finally {
    loading.value = false
  }
}

// 监听 visible / type / query / scope 变化触发搜索
watch(() => [props.visible, props.type, props.query, props.convId, props.projectId],
  ([visible]) => { if (visible) fetchIfNeeded() }, { immediate: true })

const filtered = computed(() => apiResults.value[props.type] || [])

function pick(item) {
  emit('select', { type: props.type, item })
}

function switchTo(t) {
  emit('switch-type', t)
}
</script>

<template>
  <Transition name="popover">
    <div v-if="visible"
      class="absolute left-3 right-3 rounded-2xl overflow-hidden z-30"
      style="bottom: 8px; background: var(--color-card);
             border: 1px solid var(--color-divider);
             box-shadow: 0 8px 24px rgba(0,0,0,0.12);">

      <!-- 头部 -->
      <div class="px-3.5 pt-2.5 pb-1.5 flex items-center justify-between">
        <div class="text-[11px] font-semibold uppercase"
          style="color: var(--color-ink-3); letter-spacing: 1px;">{{ meta.label }}</div>
        <div class="text-[11px]" style="color: var(--color-ink-3);">{{ filtered.length }} 项</div>
      </div>

      <!-- 列表 -->
      <div class="max-h-[210px] overflow-y-auto"
        style="border-top: 1px solid var(--color-divider);">

        <div v-if="!filtered.length" class="px-4 py-6 text-center text-[12px]"
          style="color: var(--color-ink-3);">无匹配结果</div>

        <!-- 成员 -->
        <template v-if="type === '@'">
          <button v-for="(m, i) in filtered" :key="m.id"
            @click="pick(m)"
            class="w-full px-3.5 py-2.5 flex items-center gap-2.5 active:bg-bg text-left"
            :style="i < filtered.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
            <div class="w-[30px] h-[30px] rounded-full inline-flex items-center justify-center font-serif text-[13px] font-semibold shrink-0"
              :style="m.isAi
                ? { background: '#E5EEFB', color: '#2F66D6' }
                : { background: 'var(--color-accent-soft)', color: 'var(--color-accent)' }">{{ m.initial }}</div>
            <div class="flex-1 min-w-0">
              <div class="font-serif" style="font-size: 14px; font-weight: 500; color: var(--color-ink);">{{ m.name }}</div>
              <div class="text-[11px]" style="color: var(--color-ink-3);">{{ m.role }}</div>
            </div>
          </button>
        </template>

        <!-- 项目 -->
        <template v-if="type === '#'">
          <button v-for="(p, i) in filtered" :key="p.id"
            @click="pick(p)"
            class="w-full px-3.5 py-2.5 flex items-center gap-2.5 active:bg-bg text-left"
            :style="i < filtered.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
            <div class="w-[30px] h-[30px] rounded-[8px] inline-flex items-center justify-center text-[14px] font-bold shrink-0"
              style="background: var(--color-ink); color: #fff;">#</div>
            <div class="flex-1 min-w-0">
              <div class="font-serif truncate" style="font-size: 14px; font-weight: 500;">{{ p.name }}</div>
              <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">
                <span style="color: var(--color-accent); font-weight: 600;">● {{ p.stage }}</span>
                · <span class="tabular" style="color: var(--color-ink); font-weight: 600;">¥{{ p.amount }}万</span>
              </div>
            </div>
          </button>
        </template>

        <!-- 客户 -->
        <template v-if="type === '$'">
          <button v-for="(c, i) in filtered" :key="c.id"
            @click="pick(c)"
            class="w-full px-3.5 py-2.5 flex items-center gap-2.5 active:bg-bg text-left"
            :style="i < filtered.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
            <div class="w-[30px] h-[30px] rounded-[8px] inline-flex items-center justify-center text-[13px] font-bold text-white shrink-0"
              style="background: var(--color-accent);">$</div>
            <div class="flex-1 min-w-0">
              <div class="font-serif truncate" style="font-size: 14px; font-weight: 500;">{{ c.name }}</div>
              <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">
                {{ c.tier }} 类 · <span class="tabular" style="color: var(--color-ink); font-weight: 600;">¥{{ c.value }}万</span>
              </div>
            </div>
          </button>
        </template>

      </div>

      <!-- 底部切换条 -->
      <div class="px-3.5 py-2 flex items-center gap-3"
        style="border-top: 1px solid var(--color-divider); background: var(--color-bg);">
        <span class="text-[11px] font-semibold" style="color: var(--color-ink-3);">切换：</span>
        <button v-for="t in ['@','#','$']" :key="t"
          @click="switchTo(t)"
          class="text-[11px] font-semibold active:opacity-70"
          :style="type === t
            ? { color: 'var(--color-accent)' }
            : { color: 'var(--color-ink-3)', fontWeight: 400 }">
          {{ t }} {{ TYPE_META[t]?.label?.replace(/^(提及|引用)/, '') || '' }}
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.popover-enter-active, .popover-leave-active {
  transition: opacity 0.15s, transform 0.18s cubic-bezier(.34,1.56,.64,1);
}
.popover-enter-from, .popover-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
