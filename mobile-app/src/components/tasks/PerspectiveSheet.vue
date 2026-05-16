<!--
  PerspectiveSheet - "Switch perspective" account picker (task list).
  Sections: Self (current) / Recently viewed (localStorage) / Direct reports /
  Others. Manager-visible, permission-scoped (backend /mobile/tasks/perspectives).
  All UI text via t() (i18n rule).
-->
<template>
  <Teleport to="body">
    <transition name="psh">
      <div v-if="open" class="fixed inset-0 z-50 flex flex-col"
        style="background: rgba(20,20,20,0.36);" @click.self="close">
        <div class="mt-auto flex flex-col"
          style="background: var(--color-bg, #F7F5F2); border-radius: 24px 24px 0 0;
                 box-shadow: 0 -10px 40px rgba(0,0,0,0.18); height: 80vh;">
          <div class="flex justify-center" style="padding-top: 8px;">
            <div style="width: 36px; height: 4px; background: #D8D2C6; border-radius: 2px;" />
          </div>

          <div style="padding: 14px 20px 4px;">
            <div style="font-family: var(--font-serif); font-size: 19px; font-weight: 600;
              color: #1A1A1A;">{{ t('task.perspTitle') }}</div>
            <div style="font-size: 12.5px; color: #7A7570; margin-top: 3px;">
              {{ t('task.perspSub') }}</div>
          </div>

          <div style="padding: 10px 20px 8px;">
            <input v-model="q" type="text" :placeholder="t('task.perspSearch')"
              style="width: 100%; box-sizing: border-box; background: #FFF;
                border: 1px solid #EBE6DD; border-radius: 12px; padding: 10px 14px;
                font-size: 13px; color: #1A1A1A; outline: none;" />
          </div>

          <div class="flex-1 overflow-y-auto" style="padding: 4px 0 calc(16px + env(safe-area-inset-bottom));">
            <div v-if="loading" style="padding: 30px 0; text-align: center;
              color: #B5AEA3; font-size: 13px;">···</div>
            <template v-else>
              <!-- Self -->
              <div v-if="match(selfEntry)">
                <div :style="secStyle">{{ t('task.perspSelf') }}</div>
                <div @click="pick(selfEntry)" class="active:opacity-70" :style="rowStyle">
                  <span :style="ava(selfEntry)">{{ selfEntry.short }}</span>
                  <div style="flex: 1; min-width: 0;">
                    <div style="font-size: 14px; font-weight: 600; color: #1A1A1A;">
                      {{ selfEntry.name }}
                      <span style="color: #7A7570; font-weight: 400;">{{ t('task.perspMe') }}</span>
                      <span style="margin-left: 6px; font-size: 10px; color: #2F7A4F;
                        background: #E9F1EB; padding: 1px 6px; border-radius: 3px;
                        font-weight: 700;">{{ t('task.perspCurrent') }}</span>
                    </div>
                    <div style="font-size: 11.5px; color: #7A7570; margin-top: 2px;">
                      {{ selfEntry.department }}</div>
                  </div>
                  <div :style="cntStyle(selfEntry)">
                    <div>{{ selfEntry.count }}</div>
                    <div v-if="selfEntry.overdue" style="font-size: 10px; color: #B5453A;
                      font-weight: 600;">{{ t('task.overdueN', { n: selfEntry.overdue }) }}</div>
                  </div>
                  <span style="color: #B5AEA3; font-size: 16px;">›</span>
                </div>
              </div>

              <!-- Recently viewed -->
              <div v-if="recentList.length">
                <div :style="secStyle">{{ t('task.perspRecent') }}</div>
                <div v-for="e in recentList" :key="'r' + e.id" @click="pick(e)"
                  class="active:opacity-70" :style="rowStyle">
                  <span :style="ava(e)">{{ e.short }}</span>
                  <div style="flex: 1; min-width: 0;">
                    <div style="font-size: 14px; font-weight: 600; color: #1A1A1A;">{{ e.name }}</div>
                    <div style="font-size: 11.5px; color: #7A7570; margin-top: 2px;">{{ e.department }}</div>
                  </div>
                  <div :style="cntStyle(e)">
                    <div>{{ e.count }}</div>
                    <div v-if="e.overdue" style="font-size: 10px; color: #B5453A;
                      font-weight: 600;">{{ t('task.overdueN', { n: e.overdue }) }}</div>
                  </div>
                  <span style="color: #B5AEA3; font-size: 16px;">›</span>
                </div>
              </div>

              <!-- Direct reports -->
              <div v-if="subList.length">
                <div :style="secStyle" style="display: flex; align-items: baseline; gap: 8px;">
                  <span>{{ t('task.perspSubs', { n: subList.length }) }}</span>
                  <span style="margin-left: auto; font-size: 10.5px; color: #B5AEA3;
                    text-transform: none; letter-spacing: 0;">{{ t('task.perspSubTotal', { n: subTotal }) }}</span>
                </div>
                <div v-for="e in subList" :key="'s' + e.id" @click="pick(e)"
                  class="active:opacity-70" :style="rowStyle">
                  <span :style="ava(e)">{{ e.short }}</span>
                  <div style="flex: 1; min-width: 0;">
                    <div style="font-size: 14px; font-weight: 600; color: #1A1A1A;">{{ e.name }}</div>
                    <div style="font-size: 11.5px; color: #7A7570; margin-top: 2px;">{{ e.department }}</div>
                  </div>
                  <div :style="cntStyle(e)">
                    <div>{{ e.count }}</div>
                    <div v-if="e.overdue" style="font-size: 10px; color: #B5453A;
                      font-weight: 600;">{{ t('task.overdueN', { n: e.overdue }) }}</div>
                  </div>
                  <span style="color: #B5AEA3; font-size: 16px;">›</span>
                </div>
              </div>

              <!-- Others -->
              <div v-if="otherList.length">
                <div :style="secStyle">{{ t('task.perspOthers') }}</div>
                <div v-for="e in otherList" :key="'o' + e.id" @click="pick(e)"
                  class="active:opacity-70" :style="rowStyle">
                  <span :style="ava(e)">{{ e.short }}</span>
                  <div style="flex: 1; min-width: 0;">
                    <div style="font-size: 14px; font-weight: 600; color: #1A1A1A;">{{ e.name }}</div>
                    <div style="font-size: 11.5px; color: #7A7570; margin-top: 2px;">{{ e.department }}</div>
                  </div>
                  <div :style="cntStyle(e)">
                    <div>{{ e.count }}</div>
                    <div v-if="e.overdue" style="font-size: 10px; color: #B5453A;
                      font-weight: 600;">{{ t('task.overdueN', { n: e.overdue }) }}</div>
                  </div>
                  <span style="color: #B5AEA3; font-size: 16px;">›</span>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getTaskPerspectives } from '@/api/tasks'

const { t } = useI18n()
const props = defineProps({
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'pick'])

const open = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})
const q = ref('')
const loading = ref(false)
const selfEntry = ref({ id: null, name: '', short: '?', department: '', count: 0, overdue: 0 })
const subs = ref([])
const others = ref([])
const subTotal = ref(0)

const _AVA = ['#3A6FB7', '#7B5BAC', '#C77B22', '#2F7A4F', '#B5453A', '#D97757']
function ava(e) {
  let h = 0
  for (const c of (e.name || '?')) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return { width: '38px', height: '38px', borderRadius: '19px', flexShrink: 0,
    background: _AVA[h % _AVA.length], color: '#fff', display: 'inline-flex',
    alignItems: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: 700 }
}
const secStyle = { padding: '14px 20px 6px', fontSize: '11px', color: '#7A7570',
  fontWeight: 600, letterSpacing: '0.5px', textTransform: 'uppercase' }
const rowStyle = { padding: '11px 20px', display: 'flex', alignItems: 'center',
  gap: '12px', background: '#FFF', borderBottom: '1px solid #F2EEE6' }
function cntStyle() {
  return { textAlign: 'right', flexShrink: 0, minWidth: '34px',
    fontSize: '15px', fontWeight: 700, color: '#1A1A1A', lineHeight: 1.2 }
}

function match(e) {
  const s = q.value.trim()
  if (!s) return true
  return ((e.name || '') + (e.department || '')).includes(s)
}
function _recentIds() {
  try { return JSON.parse(localStorage.getItem('task_recent_owners') || '[]') }
  catch (e) { return [] }
}
const all = computed(() => [selfEntry.value, ...subs.value, ...others.value])
const recentList = computed(() => {
  const ids = _recentIds()
  return ids
    .map(id => all.value.find(e => e.id === id && e.id !== selfEntry.value.id))
    .filter(Boolean).filter(match)
})
const subList = computed(() => subs.value.filter(match))
const otherList = computed(() => others.value.filter(match))

function pick(e) {
  if (e && e.id) {
    const ids = _recentIds().filter(x => x !== e.id)
    if (e.id !== selfEntry.value.id) ids.unshift(e.id)
    localStorage.setItem('task_recent_owners', JSON.stringify(ids.slice(0, 5)))
  }
  emit('pick', e)
  close()
}
function close() { open.value = false }

async function fetchData() {
  loading.value = true
  try {
    const r = await getTaskPerspectives()
    const d = r.data?.data || {}
    selfEntry.value = d.self || selfEntry.value
    subs.value = d.subordinates || []
    others.value = d.others || []
    subTotal.value = d.subordinate_total || 0
  } catch (e) { /* noop */ } finally {
    loading.value = false
  }
}
watch(() => props.modelValue, v => { if (v) { q.value = ''; fetchData() } })
</script>

<style scoped>
.psh-enter-active, .psh-leave-active { transition: opacity .2s; }
.psh-enter-from, .psh-leave-to { opacity: 0; }
</style>
