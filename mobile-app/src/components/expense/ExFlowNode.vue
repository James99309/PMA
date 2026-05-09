<!--
  ExFlowNode · 审批流时间线节点
  严格对齐 design_handoff/expense-list-form.jsx::ExFlowNode (L459-486)
  - 三态: done(绿) / current(warn 双环) / pending(ink4)
  - 点 14x14, 当前节点带 3px warnSoft border + 0 0 0 2px warn shadow
  - 时间线竖线 1px divider, 不在最后一个节点出现
  - 节点标题 13/600, current 时 ink, 否则 ink2
  - 子文本: user · 已通过/处理中/待处理 + 可选 remark(斜体引号)
-->
<template>
  <div class="flex" :style="{ gap: '12px', paddingBottom: last ? '0' : '12px' }">
    <!-- 时间线 dot + line -->
    <!-- current 用多重 box-shadow 双圈(替代 border, 避免改变 box 大小) -->
    <div class="flex flex-col items-center flex-shrink-0" :style="{ paddingTop: '6px' }">
      <div
        :style="{
          width: '14px',
          height: '14px',
          borderRadius: '7px',
          background: dotColor,
          boxShadow: isCurrent
            ? '0 0 0 3px var(--color-ex-warn-soft), 0 0 0 5px var(--color-ex-warn)'
            : 'none',
        }"
      />
      <div
        v-if="!last"
        class="flex-1"
        :style="{
          width: '1px',
          background: 'var(--color-ex-divider)',
          marginTop: isCurrent ? '8px' : '4px',
        }"
      />
    </div>

    <!-- 文本 -->
    <div class="flex-1" :style="{ paddingTop: '1px', paddingBottom: '6px' }">
      <div class="flex justify-between items-baseline">
        <div
          :style="{
            fontSize: '13px',
            fontWeight: 600,
            color: isCurrent ? 'var(--color-ex-ink)' : 'var(--color-ex-ink2)',
          }"
        >{{ node.node }}</div>
        <div
          v-if="node.at"
          :style="{ fontSize: '10px', color: 'var(--color-ex-ink4)' }"
        >{{ node.at }}</div>
      </div>
      <div
        :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginTop: '2px' }"
      >
        {{ node.user }} ·
        <span
          v-if="isCurrent"
          :style="{ color: 'var(--color-ex-warn)', fontWeight: 600 }"
        >处理中</span>
        <span v-else-if="isDone">已通过</span>
        <span v-else>待处理</span>
        <!-- 召回 — 与"处理中"同行同风格,只是文字 -->
        <span
          v-if="isCurrent && node.can_recall"
          role="button"
          class="active:opacity-60"
          :style="{ color: 'var(--color-ex-warn)', fontWeight: 600, marginLeft: '6px' }"
          @click.stop="$emit('recall')"
        >· 召回</span>
      </div>
      <div
        v-if="node.remark"
        :style="{
          fontSize: '11px',
          color: 'var(--color-ex-ink3)',
          marginTop: '4px',
          fontStyle: 'italic',
        }"
      >&ldquo;{{ node.remark }}&rdquo;</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /**
   * @typedef {Object} FlowNode
   * @property {string} node - 节点名(如 "票据审核")
   * @property {string} user - 处理人姓名
   * @property {'done'|'current'|'pending'} state
   * @property {string|null} at - 处理时间(done 节点必填)
   * @property {string=} remark - 备注(可选)
   */
  node: { type: Object, required: true },
  last: { type: Boolean, default: false },
})

defineEmits(['recall'])

const isDone = computed(() => props.node.state === 'done')
const isCurrent = computed(() => props.node.state === 'current')
const dotColor = computed(() => {
  if (isCurrent.value) return 'var(--color-ex-warn)'
  if (isDone.value) return 'var(--color-ex-green)'
  return 'var(--color-ex-ink4)'
})
</script>
