<!--
  WorkItemTypePickerSheet - grouped work-type picker (C3).
  Groups come from backend meta.type_groups (localized label + color, single
  source). Tap a type → emit('pick', value) + close. UI text via t().
-->
<template>
  <Teleport to="body">
    <transition name="tps">
      <div v-if="open" class="fixed inset-0 z-50 flex flex-col"
        style="background: rgba(20,20,20,0.36);" @click.self="close">
        <div class="mt-auto flex flex-col"
          style="background: var(--color-bg, #F7F5F2); border-radius: 24px 24px 0 0;
                 box-shadow: 0 -10px 40px rgba(0,0,0,0.18); max-height: 82vh;">
          <div class="flex justify-center" style="padding-top: 8px;">
            <div style="width: 36px; height: 4px; background: #D8D2C6; border-radius: 2px;" />
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center;
            padding: 12px 20px;">
            <span @click="close" class="active:opacity-60"
              style="font-size: 13px; color: #7A7570;">{{ t('common.cancel') }}</span>
            <span style="font-family: var(--font-serif); font-size: 18px; font-weight: 600;
              color: #1A1A1A;">{{ t('calendar.pickType') }}</span>
            <span style="width: 28px;" />
          </div>

          <div class="overflow-y-auto" style="padding: 0 16px calc(20px + env(safe-area-inset-bottom));">
            <div v-for="g in groups" :key="g.key">
              <div style="font-size: 11px; color: #7A7570; letter-spacing: 0.6px;
                font-weight: 600; text-transform: uppercase; padding: 14px 4px 8px;">
                {{ g.label }} · {{ g.options.length }}
              </div>
              <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;">
                <div v-for="o in g.options" :key="o.value"
                  @click="pick(o.value)" class="active:opacity-70"
                  :style="{ padding: '11px 12px', borderRadius: '10px',
                    display: 'flex', alignItems: 'center', gap: '8px',
                    background: o.value === selected ? (o.color + '22') : '#FFF',
                    border: o.value === selected
                      ? `1.5px solid ${o.color}` : '1px solid #EBE6DD' }">
                  <span :style="{ width: '8px', height: '8px', borderRadius: '4px',
                    background: o.color, flexShrink: 0 }" />
                  <span :style="{ fontSize: '13px',
                    fontWeight: o.value === selected ? 600 : 500,
                    color: o.value === selected ? o.color : '#1A1A1A' }">{{ o.label }}</span>
                  <span v-if="o.value === selected"
                    :style="{ marginLeft: 'auto', color: o.color, fontSize: '12px',
                      fontWeight: 700 }">✓</span>
                </div>
              </div>
            </div>
            <div v-if="!groups.length" style="padding: 40px 0; text-align: center;
              color: #B5AEA3; font-size: 13px;">···</div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  groups: { type: Array, default: () => [] },   // backend meta.type_groups
  selected: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'pick'])

const open = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})
function pick(v) { emit('pick', v); close() }
function close() { open.value = false }
</script>

<style scoped>
.tps-enter-active, .tps-leave-active { transition: opacity .2s; }
.tps-enter-from, .tps-leave-to { opacity: 0; }
</style>
