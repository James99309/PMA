<!--
  OrgTreePickerSheet · reusable 3-level org picker (company → department → user)
  - Drill-down navigation with breadcrumb; lands on the current user's own
    company+department by default (via :home).
  - Cascade tri-state selection: tapping a company/department toggles all
    descendant users (matches web tree selector). Users are multi-selected.
  - Data source is the backend get_shareable_users_tree (same as web), so the
    node shape is { id, name, type:'company'|'department'|'user', user_id?, children? }.
  - Emits update:selected with a flat array of user_id.
-->
<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title:      { type: String,  default: '' },
  tree:       { type: Array,   default: () => [] },   // [companyNode,...]
  selected:   { type: Array,   default: () => [] },   // [user_id,...]
  home:       { type: Object,  default: () => ({}) }, // {company_name, department}
})
const emit = defineEmits(['update:modelValue', 'update:selected'])

const open = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})

const temp = ref([])
const path = ref([])        // [companyNode, deptNode] — current drill location
const search = ref('')

// On open: seed selection + jump to the user's own company/department
watch(() => props.modelValue, v => {
  if (!v) return
  temp.value = [...(props.selected || [])]
  search.value = ''
  path.value = defaultPath()
})

function defaultPath() {
  const co = (props.tree || []).find(c => c.name === props.home?.company_name)
  if (!co) return []
  const dept = (co.children || []).find(
    n => n.type === 'department' && n.name === props.home?.department)
  return dept ? [co, dept] : [co]
}

// ── selection helpers (cascade) ──
function collectIds(node) {
  if (!node) return []
  if (node.type === 'user') return node.user_id != null ? [node.user_id] : []
  return (node.children || []).flatMap(collectIds)
}
function nodeState(node) {
  if (node.type === 'user') {
    return temp.value.includes(node.user_id) ? 'all' : 'none'
  }
  const ids = collectIds(node)
  if (!ids.length) return 'none'
  const inN = ids.filter(id => temp.value.includes(id)).length
  if (inN === 0) return 'none'
  return inN === ids.length ? 'all' : 'some'
}
function toggleNode(node) {
  const ids = node.type === 'user'
    ? (node.user_id != null ? [node.user_id] : [])
    : collectIds(node)
  if (!ids.length) return
  const allIn = ids.every(id => temp.value.includes(id))
  if (allIn) {
    temp.value = temp.value.filter(id => !ids.includes(id))
  } else {
    const set = new Set(temp.value)
    ids.forEach(id => set.add(id))
    temp.value = [...set]
  }
}

// ── navigation ──
function drill(node) {
  if (node.type === 'user') { toggleNode(node); return }
  path.value = [...path.value, node]
}
function gotoCrumb(i) {
  // i = -1 → root (companies); else slice to depth i+1
  path.value = i < 0 ? [] : path.value.slice(0, i + 1)
}
const crumbs = computed(() => path.value.map(n => n.name))

// ── current visible rows ──
const currentNodes = computed(() => {
  if (path.value.length === 0) return props.tree || []
  return path.value[path.value.length - 1].children || []
})

// ── search across all users (flattened) ──
const allUsers = computed(() => {
  const out = []
  for (const co of props.tree || []) {
    for (const child of co.children || []) {
      if (child.type === 'user') {
        out.push({ ...child, _co: co.name, _dept: '' })
      } else if (child.type === 'department') {
        for (const u of child.children || []) {
          if (u.type === 'user') out.push({ ...u, _co: co.name, _dept: child.name })
        }
      }
    }
  }
  return out
})
const searchResults = computed(() => {
  const q = search.value.trim()
  if (!q) return []
  return allUsers.value.filter(u => (u.name || '').includes(q))
})

function countUsers(node) { return collectIds(node).length }

function clear() { temp.value = [] }
function confirm() { emit('update:selected', [...temp.value]); open.value = false }
function close() { open.value = false }

// tri-state checkbox box style
function boxStyle(state) {
  const on = state === 'all' || state === 'some'
  return {
    width: '20px', height: '20px', borderRadius: '6px',
    background: on ? 'var(--color-accent)' : 'transparent',
    border: on ? 'none' : '1.5px solid var(--color-divider-strong)',
  }
}
</script>

<template>
  <Teleport to="body">
    <transition name="otp">
      <div v-if="open" class="fixed inset-0 z-50 flex flex-col"
        style="background: rgba(20,20,20,0.36);" @click.self="close">
        <div class="mt-auto flex flex-col"
          style="background: var(--color-bg); border-radius: 24px 24px 0 0;
                 box-shadow: 0 -10px 40px rgba(0,0,0,0.18); height: 82vh;">
          <div class="flex justify-center" style="padding-top: 8px;">
            <div style="width: 36px; height: 4px; background: var(--color-divider-strong); border-radius: 2px;" />
          </div>

          <div class="flex items-center justify-between" style="padding: 14px 20px 10px;">
            <button @click="close" type="button" class="active:opacity-60"
              style="font-size: 14px; color: var(--color-ink-2); font-weight: 500;">{{ t('common.cancel') }}</button>
            <span class="font-serif" style="font-size: 16px; font-weight: 500;">{{ title }}</span>
            <button @click="clear" type="button" class="active:opacity-60"
              style="font-size: 14px; color: var(--color-accent); font-weight: 500;">{{ t('task.pickClear') }}</button>
          </div>

          <!-- search -->
          <div style="padding: 0 20px 8px;">
            <div class="flex items-center gap-2.5"
              :style="{
                background: 'var(--color-card)', borderRadius: '12px', padding: '10px 14px',
                border: search ? '1.5px solid var(--color-accent)' : '1px solid var(--color-divider)',
              }">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <circle cx="6" cy="6" r="4.5" :stroke="search ? 'var(--color-ink-2)' : 'var(--color-ink-3)'" stroke-width="1.4" />
                <path d="M9.5 9.5L13 13" :stroke="search ? 'var(--color-ink-2)' : 'var(--color-ink-3)'" stroke-width="1.4" stroke-linecap="round" />
              </svg>
              <input v-model="search" type="text" :placeholder="t('task.pickSearchPerson')"
                class="flex-1 bg-transparent outline-none"
                :style="{ fontSize: '13px', color: 'var(--color-ink)', fontFamily: 'var(--font-sans)' }" />
            </div>
          </div>

          <!-- breadcrumb (hidden while searching) -->
          <div v-if="!search.trim()" class="flex items-center gap-1 overflow-x-auto no-scrollbar shrink-0"
            style="padding: 4px 20px 10px; font-size: 13px;">
            <button type="button" @click="gotoCrumb(-1)" class="active:opacity-60 shrink-0"
              :style="{ color: crumbs.length ? 'var(--color-accent)' : 'var(--color-ink-3)', fontWeight: crumbs.length ? 500 : 400 }">
              {{ t('task.fAll') }}
            </button>
            <template v-for="(c, i) in crumbs" :key="i">
              <span style="color: var(--color-ink-4);">/</span>
              <button type="button" @click="gotoCrumb(i)" class="active:opacity-60 shrink-0 whitespace-nowrap"
                :style="{ color: i === crumbs.length - 1 ? 'var(--color-ink)' : 'var(--color-accent)',
                          fontWeight: i === crumbs.length - 1 ? 600 : 500 }">
                {{ c }}
              </button>
            </template>
          </div>

          <!-- rows -->
          <div class="flex-1 overflow-y-auto" style="padding: 0 12px 16px;">
            <!-- search mode: flat user results -->
            <template v-if="search.trim()">
              <button v-for="u in searchResults" :key="u.user_id" type="button"
                @click="toggleNode(u)" class="w-full flex items-center gap-3 active:opacity-70"
                style="padding: 12px 10px; border-bottom: 1px solid var(--color-divider);">
                <span class="shrink-0 inline-flex items-center justify-center" :style="boxStyle(nodeState(u))">
                  <svg v-if="nodeState(u) === 'all'" width="12" height="12" viewBox="0 0 14 14" fill="none">
                    <path d="M2.5 7.5l3 3 6-7" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </span>
                <span class="flex-1 text-left" style="font-size: 14px; color: var(--color-ink);">
                  {{ u.name }}
                  <span style="font-size: 12px; color: var(--color-ink-3);"> · {{ [u._co, u._dept].filter(Boolean).join(' / ') }}</span>
                </span>
              </button>
              <div v-if="!searchResults.length" class="text-center" style="font-size: 13px; color: var(--color-ink-3); padding: 24px 0;">
                {{ t('task.pickNoPerson') }}
              </div>
            </template>

            <!-- drill mode: companies / departments / users at current level -->
            <template v-else>
              <div v-for="node in currentNodes" :key="node.id"
                class="flex items-center" style="border-bottom: 1px solid var(--color-divider);">
                <!-- checkbox (cascade toggle) -->
                <button type="button" @click="toggleNode(node)" class="shrink-0 active:opacity-60"
                  style="padding: 12px 8px 12px 10px;">
                  <span class="inline-flex items-center justify-center" :style="boxStyle(nodeState(node))">
                    <svg v-if="nodeState(node) === 'all'" width="12" height="12" viewBox="0 0 14 14" fill="none">
                      <path d="M2.5 7.5l3 3 6-7" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                    <span v-else-if="nodeState(node) === 'some'" style="width: 8px; height: 2px; background: #fff; border-radius: 1px;" />
                  </span>
                </button>
                <!-- label: drill for group, toggle for user -->
                <button type="button" @click="drill(node)"
                  class="flex-1 flex items-center justify-between gap-2 active:opacity-70" style="padding: 12px 10px 12px 2px;">
                  <span class="text-left" style="font-size: 14px; color: var(--color-ink);">{{ node.name }}</span>
                  <span v-if="node.type !== 'user'" class="flex items-center gap-1.5 shrink-0">
                    <span style="font-size: 12px; color: var(--color-ink-3);">{{ countUsers(node) }}</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                      <path d="M9 6l6 6-6 6" stroke="var(--color-ink-4)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </span>
                </button>
              </div>
              <div v-if="!currentNodes.length" class="text-center" style="font-size: 13px; color: var(--color-ink-3); padding: 24px 0;">
                {{ t('task.pickNoPerson') }}
              </div>
            </template>
          </div>

          <!-- footer -->
          <div class="flex items-center gap-2.5 shrink-0"
            style="padding: 10px 20px; padding-bottom: calc(10px + env(safe-area-inset-bottom));
                   border-top: 1px solid var(--color-divider); background: var(--color-card);">
            <div class="flex-1" style="font-size: 12px; color: var(--color-ink-3);">
              {{ t('task.pickSelectedN', { n: temp.length }) }}
            </div>
            <button @click="confirm" type="button" class="active:opacity-80"
              style="background: var(--color-accent); color: #fff; border: none;
                     padding: 10px 22px; border-radius: 999px; font-size: 14px; font-weight: 600;">
              {{ t('task.pickConfirm') }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.otp-enter-active, .otp-leave-active { transition: opacity .2s; }
.otp-enter-from, .otp-leave-to { opacity: 0; }
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { scrollbar-width: none; }
</style>
