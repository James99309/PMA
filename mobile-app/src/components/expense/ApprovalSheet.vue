<!--
  ApprovalSheet · 同意/驳回/转交 sheet
  严格对齐 design_handoff/expense-approval.jsx::ApprovalSheet (L235-311)
  - 三种 action 决定颜色: approve=green / reject=red / forward=blue
  - drag indicator → eyebrow(action 大写) → 22 serif title → ID 13 ink3
  - forward 时上方"转交给"卡 (含 user-picker)
  - 备注卡(reject 必填红 *, approve 可选 + 一键标签)
  - CTA 取消(flex 1 outline) + 确认(flex 2 action color)
-->
<template>
  <Teleport to="body">
    <transition name="ex-submit-sheet">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50"
        :style="{ background: 'rgba(26,26,26,.42)' }"
        @click.self="close"
      >
        <div
          class="absolute left-0 right-0 bottom-0"
          :style="[{
            background: 'var(--color-ex-bg)',
            borderRadius: '20px 20px 0 0',
            padding: '14px 20px 26px',
            paddingBottom: `calc(26px + env(safe-area-inset-bottom) + ${kbStyle.paddingBottom || '0px'})`,
            boxShadow: 'var(--shadow-ex-sheet)',
            transition: 'padding-bottom 0.25s cubic-bezier(.25,.46,.45,.94)',
          }]"
        >
          <div :style="{ width: '36px', height: '4px', background: 'var(--color-ex-divider)', borderRadius: '2px', margin: '0 auto 14px' }" />
          <!-- eyebrow: 设计稿是 label.toUpperCase()(中文 toUpperCase 还是中文); 不能直接显示英文 -->
          <div
            :style="{ fontSize: '11px', color: cfg.color, letterSpacing: '0.6px', fontWeight: 600 }"
          >{{ cfg.label }}</div>
          <div
            :style="{ fontSize: '22px', fontWeight: 500, fontFamily: 'var(--font-serif)', marginTop: '4px' }"
          >{{ cfg.title }}</div>
          <div
            :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)', marginTop: '4px' }"
          >{{ contextLine }}</div>

          <!-- forward 选人卡 -->
          <div
            v-if="action === 'forward'"
            :style="{
              marginTop: '14px', padding: '12px 14px',
              background: 'var(--color-ex-card)', borderRadius: '10px',
              border: '1px solid var(--color-ex-divider)',
            }"
          >
            <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginBottom: '6px' }">转交给</div>
            <div v-if="selectedUser" class="flex items-center" :style="{ gap: '10px' }">
              <div
                class="flex items-center justify-center"
                :style="{
                  width: '32px', height: '32px', borderRadius: '16px',
                  background: '#9B5DE5', color: '#fff',
                  fontSize: '13px', fontWeight: 600,
                }"
              >{{ selectedUser.name.slice(0, 1) }}</div>
              <div class="flex-1">
                <div :style="{ fontSize: '13px', fontWeight: 600 }">{{ selectedUser.name }}</div>
                <div
                  v-if="selectedUser.role_label"
                  :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)' }"
                >{{ selectedUser.role_label }}</div>
              </div>
              <div
                :style="{ fontSize: '12px', color: 'var(--color-ex-accent)', fontWeight: 600 }"
                @click="onPickUser"
              >更换</div>
            </div>
            <div
              v-else
              class="flex items-center justify-center"
              :style="{
                height: '40px', borderRadius: '8px',
                border: '1px dashed var(--color-ex-divider)',
                color: 'var(--color-ex-ink3)', fontSize: '13px',
              }"
              @click="onPickUser"
            >选择转交目标</div>
          </div>

          <!-- 备注框 -->
          <div
            :style="{
              marginTop: '14px', padding: '12px 14px',
              background: 'var(--color-ex-card)', borderRadius: '10px',
              border: '1px solid var(--color-ex-divider)',
            }"
          >
            <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginBottom: '6px' }">
              备注
              <span v-if="action === 'reject'" :style="{ color: 'var(--color-ex-red)' }">*</span>
            </div>
            <textarea
              v-model="comment"
              rows="3"
              :placeholder="cfg.placeholder"
              :style="{
                width: '100%', background: 'transparent', border: 'none',
                fontSize: '13px', color: 'var(--color-ex-ink)', outline: 'none',
                lineHeight: 1.55, resize: 'none',
              }"
            />
            <!-- 同意快捷标签 -->
            <div
              v-if="action === 'approve'"
              class="flex flex-wrap"
              :style="{ marginTop: '10px', gap: '6px' }"
            >
              <div
                v-for="t in ['票据已核对', '金额合规', '已确认归属']"
                :key="t"
                :style="{
                  fontSize: '11px', color: 'var(--color-ex-ink3)',
                  padding: '4px 10px',
                  background: 'var(--color-ex-divider-soft)',
                  borderRadius: '12px',
                }"
                @click="onApplyChip(t)"
              >{{ t }}</div>
            </div>
          </div>

          <!-- CTA -->
          <div class="flex" :style="{ gap: '10px', marginTop: '18px' }">
            <div
              class="flex-1 flex items-center justify-center"
              :style="{
                height: '48px', borderRadius: '24px',
                background: 'var(--color-ex-card)',
                border: '1.5px solid var(--color-ex-divider)',
                color: 'var(--color-ex-ink2)',
                fontSize: '14px', fontWeight: 600,
              }"
              @click="close"
            >取消</div>
            <!-- 设计稿(L302-306): 确认按钮永远是 cfg.color 背景 + 白字
                 不能改 disabled 时 bg, 只 fade opacity 表达不可点 -->
            <div
              class="flex items-center justify-center"
              :style="{
                flex: 2,
                height: '48px',
                borderRadius: '24px',
                background: cfg.color,
                color: '#fff',
                fontSize: '14px',
                fontWeight: 600,
                opacity: canConfirm ? 1 : 0.4,
                transition: 'opacity 0.15s',
              }"
              @click="canConfirm && submit()"
            >{{ submitting ? '处理中...' : `确认${cfg.label}` }}</div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'

const { kbStyle } = useKeyboardOffset()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  action: { type: String, required: true }, // approve / reject / forward
  contextLine: { type: String, default: '' },
  selectedUser: { type: Object, default: null }, // {id, name, role_label?}
  submitting: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'confirm', 'pick-user'])

const comment = ref('')

watch(() => props.modelValue, (v) => { if (v) comment.value = '' })

const cfg = computed(() => {
  const map = {
    approve: { label: '同意', title: '同意此报销', color: 'var(--color-ex-green)', placeholder: '可选 · 备注会显示在流程中' },
    reject:  { label: '驳回', title: '驳回此报销', color: 'var(--color-ex-red)',   placeholder: '必填 · 请说明驳回原因' },
    forward: { label: '转交', title: '转交其他人', color: 'var(--color-ex-blue)',  placeholder: '可选 · 转交说明' },
  }
  return map[props.action] || map.approve
})

const canConfirm = computed(() => {
  if (props.submitting) return false
  if (props.action === 'reject' && comment.value.trim().length < 5) return false
  if (props.action === 'forward' && !props.selectedUser) return false
  return true
})

function onApplyChip(t) {
  comment.value = comment.value ? `${comment.value}; ${t}` : t
}

function onPickUser() {
  emit('pick-user')
}

function submit() {
  emit('confirm', { comment: comment.value, targetUserId: props.selectedUser?.id })
}

function close() { emit('update:modelValue', false) }
</script>

<style scoped>
.ex-submit-sheet-enter-active, .ex-submit-sheet-leave-active { transition: opacity 0.2s; }
.ex-submit-sheet-enter-from, .ex-submit-sheet-leave-to { opacity: 0; }
</style>
