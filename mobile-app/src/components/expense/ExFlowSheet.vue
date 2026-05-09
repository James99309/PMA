<!--
  ExFlowSheet · 审批流程时间线 sheet
  顶部状态 chip 点击 → 弹出此 sheet 显示完整流程节点
  替代之前在每个详情页底部塞一大块"审批进度"的做法
-->
<template>
  <Teleport to="body">
    <transition name="ex-flow-sheet">
      <div v-if="modelValue"
        class="fixed inset-0 z-50"
        :style="{ background: 'rgba(0,0,0,0.32)' }"
        @click.self="close">
        <div class="absolute left-0 right-0 bottom-0"
          :style="{
            background: 'var(--color-ex-bg)',
            borderRadius: '20px 20px 0 0',
            paddingBottom: 'calc(20px + env(safe-area-inset-bottom))',
            maxHeight: '80vh',
            display: 'flex', flexDirection: 'column',
          }">
          <div :style="{ width: '36px', height: '4px', background: 'var(--color-ex-divider)', borderRadius: '2px', margin: '10px auto 6px' }" />
          <div class="px-5 pt-2 pb-3 flex items-center justify-between shrink-0">
            <div :style="{ fontSize: '15px', fontWeight: 600, color: 'var(--color-ex-ink)' }">
              审批流程
              <span v-if="currentStepName"
                :style="{ fontSize: '11px', color: 'var(--color-ex-warn)', fontWeight: 500, marginLeft: '6px' }">
                · 当前在「{{ currentStepName }}」
              </span>
            </div>
            <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)' }" @click="close">关闭</div>
          </div>

          <div class="overflow-auto" :style="{ background: 'var(--color-ex-card)', padding: '12px 20px 20px' }">
            <div v-if="!nodes || nodes.length === 0"
              :style="{ padding: '40px 20px', textAlign: 'center', color: 'var(--color-ex-ink3)', fontSize: '13px' }">
              暂无审批流程
            </div>
            <ExFlowNode v-for="(n, i) in nodes" :key="i" :node="n" :last="i === nodes.length - 1" />
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import ExFlowNode from './ExFlowNode.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  nodes: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const currentStepName = computed(() => props.nodes?.find(n => n.state === 'current')?.node || '')

function close() { emit('update:modelValue', false) }
</script>

<style scoped>
.ex-flow-sheet-enter-active, .ex-flow-sheet-leave-active { transition: opacity 0.2s; }
.ex-flow-sheet-enter-from, .ex-flow-sheet-leave-to { opacity: 0; }
</style>
