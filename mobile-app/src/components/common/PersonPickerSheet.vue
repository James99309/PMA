<script setup>
// 选人 sheet — 严格对齐设计稿 edit-project.jsx PickSalesOwner
// 椭圆 chip 自适应换行 + 搜索 + 部门快筛
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue:   { type: Boolean, default: false },
  title:        { type: String,  default: '选择负责人' },
  options:      { type: Array,   default: () => [] },  // [{id,name,department}]
  selected:     { type: [Number, String, null], default: null },
})
const emit = defineEmits(['update:modelValue', 'update:selected'])

const open = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})

const search = ref('')
const activeDept = ref('全部')
const tempSelected = ref(null)

watch(() => props.modelValue, v => {
  if (v) {
    tempSelected.value = props.selected
    search.value = ''
    activeDept.value = '全部'
  }
})

const departments = computed(() => {
  const set = new Set(['全部'])
  props.options.forEach(o => { if (o.department) set.add(o.department) })
  return [...set]
})

const filtered = computed(() => {
  const q = search.value.trim()
  return props.options.filter(o => {
    if (activeDept.value !== '全部' && o.department !== activeDept.value) return false
    if (q) {
      const text = (o.name || '') + (o.department || '')
      if (!text.includes(q)) return false
    }
    return true
  })
})

function pick(o) {
  tempSelected.value = tempSelected.value === o.id ? null : o.id
}

function clear() { tempSelected.value = null }

function confirm() {
  emit('update:selected', tempSelected.value)
  open.value = false
}

function close() { open.value = false }

const selectedCount = computed(() => tempSelected.value != null ? 1 : 0)
</script>

<template>
  <Teleport to="body">
    <transition name="pps">
      <div v-if="open" class="fixed inset-0 z-50 flex flex-col"
        style="background: rgba(20,20,20,0.36);" @click.self="close">
        <div class="mt-auto flex flex-col"
          style="background: var(--color-bg); border-radius: 24px 24px 0 0;
                 box-shadow: 0 -10px 40px rgba(0,0,0,0.18); height: 82vh;">

          <!-- drag handle -->
          <div class="flex justify-center" style="padding-top: 8px;">
            <div style="width: 36px; height: 4px; background: var(--color-divider-strong); border-radius: 2px;" />
          </div>

          <!-- sheet header -->
          <div class="flex items-center justify-between"
            style="padding: 14px 20px 10px;">
            <button @click="close" type="button" class="active:opacity-60"
              style="font-size: 14px; color: var(--color-ink-2); font-weight: 500;">取消</button>
            <span class="font-serif"
              style="font-size: 16px; font-weight: 500;">{{ title }}</span>
            <button @click="clear" type="button" class="active:opacity-60"
              style="font-size: 14px; color: var(--color-accent); font-weight: 500;">清空</button>
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
              <input v-model="search" type="text" placeholder="搜索姓名或部门"
                class="flex-1 bg-transparent outline-none"
                :style="{
                  fontSize: '13px',
                  color: 'var(--color-ink)',
                  fontFamily: search ? 'var(--font-sans)' : 'var(--font-serif)',
                  fontStyle: search ? 'normal' : 'italic',
                }" />
            </div>
          </div>

          <!-- dept filter chips -->
          <div class="flex gap-1.5 overflow-x-auto shrink-0 no-scrollbar"
            style="padding: 6px 16px 10px;">
            <button v-for="d in departments" :key="d" type="button"
              @click="activeDept = d"
              class="shrink-0 active:opacity-70"
              :style="{
                fontSize: '12px', padding: '6px 12px', borderRadius: '999px',
                background: activeDept === d ? 'var(--color-ink)' : 'var(--color-card)',
                color: activeDept === d ? '#fff' : 'var(--color-ink-2)',
                border: activeDept === d ? 'none' : '1px solid var(--color-divider)',
                fontWeight: activeDept === d ? 600 : 400,
                whiteSpace: 'nowrap',
              }">{{ d }}</button>
          </div>

          <!-- chip list -->
          <div class="flex-1 overflow-y-auto flex flex-wrap gap-2"
            style="padding: 8px 16px 16px; align-content: flex-start;">
            <button v-for="o in filtered" :key="o.id" type="button"
              @click="pick(o)" class="active:opacity-80"
              :style="{
                padding: '8px 14px',
                borderRadius: '999px',
                background: tempSelected === o.id ? 'var(--color-ink)' : 'var(--color-card)',
                color: tempSelected === o.id ? '#fff' : 'var(--color-ink-2)',
                border: tempSelected === o.id ? 'none' : '1px solid var(--color-divider)',
                fontSize: '13px',
                fontWeight: tempSelected === o.id ? 600 : 400,
                whiteSpace: 'nowrap',
              }">
              {{ o.name }}<span v-if="o.department"
                :style="{ opacity: tempSelected === o.id ? 0.7 : 0.6, marginLeft: '4px' }"> · {{ o.department }}</span>
            </button>
            <div v-if="!filtered.length" class="w-full text-center"
              style="font-size: 13px; color: var(--color-ink-3); padding: 24px 0;">
              没有匹配的人员
            </div>
          </div>

          <!-- confirm bar -->
          <div class="flex items-center gap-2.5 shrink-0"
            style="padding: 10px 20px; padding-bottom: calc(10px + env(safe-area-inset-bottom));
                   border-top: 1px solid var(--color-divider); background: var(--color-card);">
            <div class="flex-1" style="font-size: 12px; color: var(--color-ink-3);">
              已选 <span style="color: var(--color-accent); font-weight: 600;">{{ selectedCount }}</span> 人
            </div>
            <button @click="confirm" type="button" class="active:opacity-80"
              style="background: var(--color-accent); color: #fff; border: none;
                     padding: 10px 22px; border-radius: 999px; font-size: 14px; font-weight: 600;">
              确定
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.pps-enter-active, .pps-leave-active { transition: opacity .2s; }
.pps-enter-from, .pps-leave-to { opacity: 0; }
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { scrollbar-width: none; }
</style>
