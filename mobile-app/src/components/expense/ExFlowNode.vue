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
    <div class="flex flex-col items-center flex-shrink-0">
      <div
        :style="{
          width: '14px',
          height: '14px',
          borderRadius: '7px',
          background: dotColor,
          border: isCurrent ? '3px solid var(--color-ex-warn-soft)' : 'none',
          boxShadow: isCurrent ? '0 0 0 2px var(--color-ex-warn)' : 'none',
          marginTop: '4px',
        }"
      />
      <div
        v-if="!last"
        class="flex-1"
        :style="{
          width: '1px',
          background: 'var(--color-ex-divider)',
          marginTop: '2px',
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

const isDone = computed(() => props.node.state === 'done')
const isCurrent = computed(() => props.node.state === 'current')
const dotColor = computed(() => {
  if (isCurrent.value) return 'var(--color-ex-warn)'
  if (isDone.value) return 'var(--color-ex-green)'
  return 'var(--color-ex-ink4)'
})
</script>
