<script setup>
// Multi-select people sheet (reviewers / collaborators).
// Dedicated component (do NOT modify single-select PersonPickerSheet).
// All UI text via t() (i18n rule).
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title:      { type: String,  default: '' },
  options:    { type: Array,   default: () => [] },   // [{id,name,department}]
  selected:   { type: Array,   default: () => [] },   // [id,...]
})
const emit = defineEmits(['update:modelValue', 'update:selected'])

const open = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})

const search = ref('')
const ALL = computed(() => t('task.fAll'))
const activeDept = ref('')
const temp = ref([])

watch(() => props.modelValue, v => {
  if (v) {
    temp.value = [...(props.selected || [])]
    search.value = ''
    activeDept.value = ALL.value
  }
})

const departments = computed(() => {
  const set = new Set([ALL.value])
  props.options.forEach(o => { if (o.department) set.add(o.department) })
  return [...set]
})

const filtered = computed(() => {
  const q = search.value.trim()
  return props.options.filter(o => {
    if (activeDept.value !== ALL.value && o.department !== activeDept.value) return false
    if (q) {
      const text = (o.name || '') + (o.department || '')
      if (!text.includes(q)) return false
    }
    return true
  })
})

function toggle(o) {
  const i = temp.value.indexOf(o.id)
  if (i >= 0) temp.value.splice(i, 1)
  else temp.value.push(o.id)
}
function isSel(o) { return temp.value.includes(o.id) }
function clear() { temp.value = [] }
function confirm() { emit('update:selected', [...temp.value]); open.value = false }
function close() { open.value = false }
</script>

<template>
  <Teleport to="body">
    <transition name="mps">
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

          <div class="flex gap-1.5 overflow-x-auto shrink-0 no-scrollbar" style="padding: 6px 16px 10px;">
            <button v-for="dp in departments" :key="dp" type="button"
              @click="activeDept = dp" class="shrink-0 active:opacity-70"
              :style="{
                fontSize: '12px', padding: '6px 12px', borderRadius: '999px',
                background: activeDept === dp ? 'var(--color-ink)' : 'var(--color-card)',
                color: activeDept === dp ? '#fff' : 'var(--color-ink-2)',
                border: activeDept === dp ? 'none' : '1px solid var(--color-divider)',
                fontWeight: activeDept === dp ? 600 : 400, whiteSpace: 'nowrap',
              }">{{ dp }}</button>
          </div>

          <div class="flex-1 overflow-y-auto flex flex-wrap gap-2"
            style="padding: 8px 16px 16px; align-content: flex-start;">
            <button v-for="o in filtered" :key="o.id" type="button"
              @click="toggle(o)" class="active:opacity-80"
              :style="{
                padding: '8px 14px', borderRadius: '999px',
                background: isSel(o) ? 'var(--color-ink)' : 'var(--color-card)',
                color: isSel(o) ? '#fff' : 'var(--color-ink-2)',
                border: isSel(o) ? 'none' : '1px solid var(--color-divider)',
                fontSize: '13px', fontWeight: isSel(o) ? 600 : 400, whiteSpace: 'nowrap',
              }">
              {{ o.name }}<span v-if="o.department"
                :style="{ opacity: isSel(o) ? 0.7 : 0.6, marginLeft: '4px' }"> · {{ o.department }}</span>
            </button>
            <div v-if="!filtered.length" class="w-full text-center"
              style="font-size: 13px; color: var(--color-ink-3); padding: 24px 0;">
              {{ t('task.pickNoPerson') }}
            </div>
          </div>

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
.mps-enter-active, .mps-leave-active { transition: opacity .2s; }
.mps-enter-from, .mps-leave-to { opacity: 0; }
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { scrollbar-width: none; }
</style>
