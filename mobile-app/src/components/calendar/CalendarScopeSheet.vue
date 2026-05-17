<!--
  CalendarScopeSheet - "Switch calendar" account picker (work calendar).
  Same bottom-sheet approach as tasks/PerspectiveSheet: Self / Colleagues
  (subordinates + others merged, design-faithful), search, this-week count.
  Permission-scoped by backend /mobile/worklog/accounts. UI text via t().
-->
<template>
  <Teleport to="body">
    <transition name="csh">
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
              color: #1A1A1A;">{{ t('calendar.scopeTitle') }}</div>
            <div style="font-size: 12.5px; color: #7A7570; margin-top: 3px;">
              {{ t('calendar.scopeSub') }}</div>
          </div>

          <div style="padding: 10px 20px 8px;">
            <input v-model="q" type="text" :placeholder="t('calendar.scopeSearch')"
              style="width: 100%; box-sizing: border-box; background: #FFF;
                border: 1px solid #EBE6DD; border-radius: 12px; padding: 10px 14px;
                font-size: 13px; color: #1A1A1A; outline: none;" />
          </div>

          <div class="flex-1 overflow-y-auto"
            style="padding: 4px 0 calc(16px + env(safe-area-inset-bottom));">
            <div v-if="loading" style="padding: 30px 0; text-align: center;
              color: #B5AEA3; font-size: 13px;">···</div>
            <template v-else>
              <!-- Self -->
              <div v-if="match(selfEntry)">
                <div :style="secStyle">{{ t('calendar.scopeSelf') }}</div>
                <div @click="pick(selfEntry)" class="active:opacity-70" :style="rowStyle">
                  <span :style="ava(selfEntry)">{{ selfEntry.short }}</span>
                  <div style="flex: 1; min-width: 0;">
                    <div style="font-size: 14px; font-weight: 600; color: #1A1A1A;">
                      {{ selfEntry.name }}
                      <span style="color: #7A7570; font-weight: 400;">{{ t('calendar.scopeMe') }}</span>
                      <span v-if="isSelfCurrent" style="margin-left: 6px; font-size: 9.5px;
                        color: #D97757; background: #FAEEE5; padding: 1px 5px;
                        border-radius: 3px; font-weight: 700;">{{ t('calendar.scopeCurrent') }}</span>
                    </div>
                    <div style="font-size: 11.5px; color: #7A7570; margin-top: 2px;">
                      {{ selfEntry.department }}</div>
                  </div>
                  <div :style="cntStyle">
                    <div>{{ selfEntry.week_count }}</div>
                    <div style="font-size: 9px; color: #B5AEA3; font-weight: 400;">
                      {{ t('calendar.weekShort') }}</div>
                  </div>
                  <span style="color: #B5AEA3; font-size: 14px;">›</span>
                </div>
              </div>

              <!-- Colleagues (subordinates + others, design-faithful merge) -->
              <div v-if="colleagueList.length">
                <div :style="secStyle" style="display: flex; align-items: baseline; gap: 8px;">
                  <span>{{ t('calendar.scopeColleagues', { n: colleagueList.length }) }}</span>
                  <span style="margin-left: auto; font-size: 10.5px; color: #B5AEA3;
                    text-transform: none; letter-spacing: 0;">
                    {{ t('calendar.scopeWeekTotal', { n: colleagueTotal }) }}</span>
                </div>
                <div v-for="e in colleagueList" :key="e.id"
                  @click="pick(e)" class="active:opacity-70"
                  :style="{ ...rowStyle, background: isCurrent(e) ? '#FAEEE588' : '#FFF' }">
                  <span :style="ava(e)">{{ e.short }}</span>
                  <div style="flex: 1; min-width: 0;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                      <span style="font-size: 14px; font-weight: 600; color: #1A1A1A;">{{ e.name }}</span>
                      <span v-if="isCurrent(e)" style="font-size: 9.5px; color: #D97757;
                        background: #FAEEE5; padding: 1px 5px; border-radius: 3px;
                        font-weight: 700;">{{ t('calendar.scopeCurrent') }}</span>
                    </div>
                    <div style="font-size: 11.5px; color: #7A7570; margin-top: 2px;">{{ e.department }}</div>
                  </div>
                  <div :style="cntStyle">
                    <div>{{ e.week_count }}</div>
                    <div style="font-size: 9px; color: #B5AEA3; font-weight: 400;">
                      {{ t('calendar.weekShort') }}</div>
                  </div>
                  <span style="color: #B5AEA3; font-size: 14px;">›</span>
                </div>
              </div>

              <div v-if="!match(selfEntry) && !colleagueList.length"
                style="padding: 40px 0; text-align: center; color: #B5AEA3; font-size: 13px;">
                {{ t('calendar.scopeNoMatch') }}</div>
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
import { getWorklogAccounts } from '@/api/worklog'

const { t } = useI18n()
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  currentOwnerId: { type: Number, default: null },   // null = viewing self
})
const emit = defineEmits(['update:modelValue', 'pick'])

const open = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})
const q = ref('')
const loading = ref(false)
const selfEntry = ref({ id: null, name: '', short: '?', department: '', week_count: 0,
  is_self: true })
const subs = ref([])
const others = ref([])

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
const cntStyle = { textAlign: 'right', flexShrink: 0, minWidth: '34px',
  fontSize: '15px', fontWeight: 700, color: '#1A1A1A', lineHeight: 1.15 }

const isSelfCurrent = computed(() => props.currentOwnerId == null)
function isCurrent(e) { return props.currentOwnerId != null && e.id === props.currentOwnerId }
function match(e) {
  const s = q.value.trim()
  if (!s) return true
  return ((e.name || '') + (e.department || '')).includes(s)
}
const colleagues = computed(() => [...subs.value, ...others.value])
const colleagueList = computed(() => colleagues.value.filter(match))
const colleagueTotal = computed(() =>
  colleagues.value.reduce((s, e) => s + (e.week_count || 0), 0))

function pick(e) {
  emit('pick', e)
  close()
}
function close() { open.value = false }

async function fetchData() {
  loading.value = true
  try {
    const r = await getWorklogAccounts()
    const d = r.data?.data || {}
    selfEntry.value = d.self || selfEntry.value
    subs.value = d.subordinates || []
    others.value = d.others || []
  } catch (e) { /* noop */ } finally {
    loading.value = false
  }
}
watch(() => props.modelValue, v => { if (v) { q.value = ''; fetchData() } })
</script>

<style scoped>
.csh-enter-active, .csh-leave-active { transition: opacity .2s; }
.csh-enter-from, .csh-leave-to { opacity: 0; }
</style>
