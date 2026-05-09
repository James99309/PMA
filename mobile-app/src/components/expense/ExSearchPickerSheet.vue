<!--
  ExSearchPickerSheet · 通用搜索选择 sheet
  用于 ExpenseEditView 的"关联客户/关联项目"挑选, 走后端 search API
-->
<template>
  <Teleport to="body">
    <transition name="sheet">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex flex-col"
        :style="{ background: 'rgba(0,0,0,0.32)' }"
        @click.self="close"
      >
        <div
          class="mt-auto flex flex-col"
          :style="[{
            background: 'var(--color-ex-bg)',
            borderRadius: '20px 20px 0 0',
            maxHeight: '80vh',
            minHeight: '50vh',
          }, kbStyle]"
        >
          <!-- drag indicator -->
          <div
            :style="{
              width: '36px',
              height: '4px',
              background: 'var(--color-ex-divider)',
              borderRadius: '2px',
              margin: '10px auto 6px',
            }"
          />
          <div class="px-5 pt-2 pb-3 flex items-center justify-between shrink-0">
            <div :style="{ fontSize: '15px', fontWeight: 600, color: 'var(--color-ex-ink)' }">{{ title }}</div>
            <div
              :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)' }"
              @click="close"
            >取消</div>
          </div>

          <!-- search input -->
          <div :style="{ padding: '0 16px 12px' }">
            <input
              v-model="q"
              :placeholder="placeholder"
              class="w-full"
              :style="{
                background: 'var(--color-ex-card)',
                border: '1px solid var(--color-ex-divider)',
                borderRadius: '8px',
                padding: '10px 14px',
                fontSize: '14px',
                color: 'var(--color-ex-ink)',
              }"
              @input="onSearch"
            />
          </div>

          <!-- list -->
          <div class="flex-1 overflow-auto">
            <div v-if="loading" :style="{ padding: '20px', textAlign: 'center', color: 'var(--color-ex-ink3)', fontSize: '13px' }">
              搜索中...
            </div>
            <div v-else-if="items.length === 0 && q" :style="{ padding: '20px', textAlign: 'center', color: 'var(--color-ex-ink3)', fontSize: '13px' }">
              没有找到相关结果
            </div>
            <div v-else>
              <div
                v-for="it in items"
                :key="it.id"
                :style="{
                  background: 'var(--color-ex-card)',
                  padding: '14px 20px',
                  borderBottom: '1px solid var(--color-ex-divider-soft)',
                }"
                @click="pick(it)"
              >
                <div :style="{ fontSize: '14px', fontWeight: 600, color: 'var(--color-ex-ink)' }">
                  {{ it.label || it.name || it.title }}
                </div>
                <div
                  v-if="it.sub"
                  :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)', marginTop: '3px' }"
                >{{ it.sub }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'

const { kbStyle } = useKeyboardOffset()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title:      { type: String,  default: '搜索' },
  placeholder:{ type: String,  default: '输入关键词搜索' },
  searchFn:   { type: Function, required: true }, // (q) => Promise<{items: [{id, label, sub?}]}>
})
const emit = defineEmits(['update:modelValue', 'pick'])

const q = ref('')
const items = ref([])
const loading = ref(false)
let debounce = null

watch(() => props.modelValue, (v) => {
  if (v) {
    q.value = ''
    items.value = []
    onSearch()
  }
})

async function onSearch() {
  clearTimeout(debounce)
  debounce = setTimeout(async () => {
    loading.value = true
    try {
      const r = await props.searchFn(q.value)
      items.value = r || []
    } finally {
      loading.value = false
    }
  }, 250)
}

function pick(it) {
  emit('pick', it)
  close()
}
function close() { emit('update:modelValue', false) }
</script>

<style scoped>
.sheet-enter-active, .sheet-leave-active { transition: opacity 0.2s; }
.sheet-enter-from, .sheet-leave-to { opacity: 0; }
</style>
