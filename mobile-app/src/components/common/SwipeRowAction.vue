<!--
  SwipeRowAction · 通用左滑显示操作按钮(类 iOS Mail 删除)
  - 滑动 > 阈值显示按钮; 释放时 snap to 0 或 -actionWidth
  - 任何外部 tap (如另一行 swipe / 滚动) 自动收回
  - actions: [{label, color: 'red'/'ink', handler: () => void}]
  - disabled: 禁用滑动(如非草稿不允许删除)
-->
<template>
  <div class="swipe-wrap" :style="{ touchAction: 'pan-y' }">
    <!-- 操作按钮区(在内容下方, 滑出后显露) -->
    <div class="swipe-actions" :style="{ width: `${actionWidth}px` }">
      <button v-for="(a, i) in actions" :key="i"
        @click.stop="onAction(a)"
        :style="{
          width: `${actionWidth / actions.length}px`,
          background: actionColor(a),
          color: '#fff',
          fontSize: '14px', fontWeight: 600,
          border: 'none',
        }">{{ a.label }}</button>
    </div>
    <!-- 内容(可滑动) -->
    <div class="swipe-inner"
      :style="{
        transform: `translateX(${offset}px)`,
        transition: transitioning ? 'transform 0.2s ease-out' : 'none',
      }"
      @touchstart.passive="onTouchStart"
      @touchmove.passive="onTouchMove"
      @touchend="onTouchEnd"
      @touchcancel="onTouchEnd"
      @click.capture="onInnerClick">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  actions: { type: Array, default: () => [] },     // [{label, color: 'red'|'ink', handler}]
  disabled: { type: Boolean, default: false },
  actionWidth: { type: Number, default: 80 },       // 单个 action 默认 80
  threshold: { type: Number, default: 30 },          // 拖动多少 px 才认为是滑动手势
})
const emit = defineEmits(['open', 'close'])

const offset = ref(0)
const transitioning = ref(false)
let startX = 0
let startY = 0
let startOffset = 0
let isHorizontal = null  // null/true/false — 第一次 move 时锁定方向

const opened = computed(() => offset.value < -props.threshold)

function actionColor(a) {
  if (a.color === 'red') return 'var(--color-ex-red, #B5453A)'
  if (a.color === 'ink') return 'var(--color-ink, #1A1A1A)'
  return a.color || 'var(--color-ex-red, #B5453A)'
}

function onTouchStart(e) {
  if (props.disabled) return
  const t = e.touches[0]
  startX = t.clientX
  startY = t.clientY
  startOffset = offset.value
  isHorizontal = null
  transitioning.value = false
}

function onTouchMove(e) {
  if (props.disabled || isHorizontal === false) return
  const t = e.touches[0]
  const dx = t.clientX - startX
  const dy = t.clientY - startY
  // 第一次 move: 判断方向(横向才接管)
  if (isHorizontal === null) {
    if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return  // 还不够判定
    isHorizontal = Math.abs(dx) > Math.abs(dy)
    if (!isHorizontal) return
  }
  // 横向滑动: 只允许向左拉(dx<0); 向右拉超过 0 时夹回 0
  let next = startOffset + dx
  if (next > 0) next = 0
  // 弹性: 拉超 -actionWidth 后缩减增量
  const max = -props.actionWidth
  if (next < max) {
    const over = max - next
    next = max - over * 0.3
  }
  offset.value = next
}

function onTouchEnd() {
  if (props.disabled || isHorizontal !== true) {
    isHorizontal = null
    return
  }
  isHorizontal = null
  transitioning.value = true
  // 滑过半数 → snap 到 fully open; 否则收回
  if (offset.value < -props.actionWidth / 2) {
    offset.value = -props.actionWidth
    emit('open')
    // 通知所有同级 SwipeRowAction 收回(单一打开)
    document.dispatchEvent(new CustomEvent('swipe-row-opened', { detail: { source: instanceId } }))
  } else {
    offset.value = 0
    emit('close')
  }
}

function onAction(a) {
  if (typeof a.handler === 'function') a.handler()
  // 操作完成自动收回
  close()
}

function close() {
  if (offset.value === 0) return
  transitioning.value = true
  offset.value = 0
  emit('close')
}

// 点行内任意位置 → 如果当前是打开状态, 第一次点收回(吃掉点击, 不触发行内 router.push)
function onInnerClick(e) {
  if (offset.value !== 0) {
    e.stopPropagation()
    e.preventDefault()
    close()
  }
}

// 单一打开: 任何其它 SwipeRowAction 打开时, 自己收回
const instanceId = Math.random().toString(36).slice(2)
function onOtherOpened(e) {
  if (e.detail?.source !== instanceId) close()
}
// 滚动列表也收回
function onScroll() { close() }

onMounted(() => {
  document.addEventListener('swipe-row-opened', onOtherOpened)
})
onBeforeUnmount(() => {
  document.removeEventListener('swipe-row-opened', onOtherOpened)
})

defineExpose({ close })
</script>

<style scoped>
.swipe-wrap {
  position: relative;
  overflow: hidden;
}
.swipe-actions {
  position: absolute;
  top: 0; right: 0; bottom: 0;
  display: flex;
}
.swipe-inner {
  position: relative;
  z-index: 1;
  background: inherit;
  will-change: transform;
}
</style>
