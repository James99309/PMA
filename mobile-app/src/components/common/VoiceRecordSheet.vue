<script setup>
// 语音消息录制底部弹层 — Web MediaRecorder 实现
// 简化交互：点击麦克风开始/停止录音；左滑取消、点发送上传
import { ref, watch, onBeforeUnmount, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // (file: Blob, durationSec: number) => Promise
  send:       { type: Function, required: true },
})
const emit = defineEmits(['update:modelValue'])

const recording = ref(false)
const elapsed = ref(0)         // 秒
const blobUrl = ref('')
const blob = ref(null)
const sending = ref(false)

let mr = null               // MediaRecorder
let stream = null
let chunks = []
let timer = null

watch(() => props.modelValue, v => {
  if (!v) reset()
})

const display = computed(() => {
  const m = String(Math.floor(elapsed.value / 60)).padStart(2, '0')
  const s = String(elapsed.value % 60).padStart(2, '0')
  return `${m}:${s}`
})

async function start() {
  if (recording.value) return
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  } catch (e) {
    alert(t('voice.micFail') + (e?.message || e))
    return
  }
  chunks = []
  // iOS WKWebView 支持 audio/mp4, Android/Chrome 支持 audio/webm
  const mime = MediaRecorder.isTypeSupported('audio/mp4') ? 'audio/mp4'
    : MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm'
    : ''
  mr = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined)
  mr.ondataavailable = e => { if (e.data?.size) chunks.push(e.data) }
  mr.onstop = () => {
    const type = mr.mimeType || 'audio/mp4'
    blob.value = new Blob(chunks, { type })
    blobUrl.value = URL.createObjectURL(blob.value)
    cleanupStream()
  }
  mr.start()
  recording.value = true
  elapsed.value = 0
  timer = setInterval(() => { elapsed.value++ }, 1000)
}

function stop() {
  if (!recording.value) return
  try { mr.stop() } catch {}
  recording.value = false
  clearInterval(timer); timer = null
}

function cleanupStream() {
  stream?.getTracks?.().forEach(t => t.stop())
  stream = null
}

function reset() {
  if (recording.value) {
    try { mr.stop() } catch {}
    recording.value = false
  }
  clearInterval(timer); timer = null
  cleanupStream()
  if (blobUrl.value) { URL.revokeObjectURL(blobUrl.value); blobUrl.value = '' }
  blob.value = null
  elapsed.value = 0
  chunks = []
  sending.value = false
}

async function onSend() {
  if (!blob.value || sending.value) return
  sending.value = true
  try {
    await props.send(blob.value, elapsed.value)
    emit('update:modelValue', false)
  } catch (e) {
    alert(t('voice.sendFail') + (e?.message || e))
  } finally {
    sending.value = false
  }
}

function close() {
  if (sending.value) return
  emit('update:modelValue', false)
}

onBeforeUnmount(reset)

// 简易波形条（非实时频谱，使用伪随机静态数据避免性能开销）
const bars = Array.from({ length: 38 }, (_, i) => {
  const s = Math.sin(i * 0.6) * 0.5 + 0.5
  const r = ((i * 17) % 11) / 11
  return 8 + (s * 0.6 + r * 0.4) * 38
})
</script>

<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="modelValue" class="fixed inset-0 z-50">
        <div class="absolute inset-0 bg-black/40" @click="close" />
        <div class="absolute left-0 right-0 bottom-0 rounded-t-3xl px-5 pt-4"
          :style="{
            background: 'var(--color-bg)',
            paddingBottom: 'calc(20px + env(safe-area-inset-bottom))',
          }">
          <div class="w-10 h-1 rounded-full mx-auto mb-3"
            style="background: var(--color-divider-strong);" />

          <!-- 标题行：录音中红点 + 时长 -->
          <div class="flex items-center justify-between mb-3">
            <span class="inline-flex items-center gap-1.5 text-[12px]"
              style="color: var(--color-ink-3);">
              <span v-if="recording" class="w-[7px] h-[7px] rounded-full vr-pulse-dot" />
              <span v-else class="w-[7px] h-[7px] rounded-full"
                style="background: var(--color-ink-4);" />
              {{ recording ? t('voice.statusRecording') : (blob ? t('voice.statusRecorded') : t('voice.statusReady')) }}
            </span>
            <span class="text-[14px] font-semibold tabular"
              style="color: var(--color-ink);">{{ display }}</span>
          </div>

          <!-- 波形显示区 -->
          <div class="rounded-[18px] flex items-center justify-center gap-[3px] h-[70px] px-4"
            :class="{ 'vr-bars-active': recording, 'vr-bars-rest': !recording && !blob, 'vr-bars-recorded': blob }"
            :style="{
              background: 'var(--color-card)',
              border: '1px solid var(--color-divider)',
            }">
            <span v-for="(h, i) in bars" :key="i" class="vr-bar"
              :style="{ height: h + 'px', '--vr-delay': (i * 60) + 'ms' }" />
          </div>

          <!-- 已录制 → 试听 -->
          <audio v-if="blob && blobUrl" :src="blobUrl" controls
            class="w-full mt-3 rounded-xl" style="height: 38px;" />

          <!-- 操作按钮 -->
          <div class="flex items-center justify-center gap-6 mt-5">
            <button v-if="blob" @click="reset"
              class="text-[13px] active:opacity-60"
              style="color: var(--color-ink-3);">{{ t('voice.rerecord') }}</button>
            <button v-else @click="close"
              class="text-[13px] active:opacity-60"
              style="color: var(--color-ink-3);">{{ t('voice.cancel') }}</button>

            <button @click="recording ? stop() : start()" type="button"
              class="w-[76px] h-[76px] rounded-full inline-flex items-center justify-center active:scale-95 transition-transform"
              :style="{
                background: recording ? '#C44' : 'var(--color-accent)',
                color: '#fff',
                boxShadow: recording
                  ? '0 0 0 8px rgba(196,68,68,0.18)'
                  : '0 0 0 8px var(--color-accent-soft)',
              }">
              <!-- 麦克 / 停止图标 -->
              <svg v-if="!recording" width="28" height="28" viewBox="0 0 24 24" fill="none">
                <rect x="9" y="3" width="6" height="11" rx="3" fill="#fff"/>
                <path d="M5 12a7 7 0 0014 0M12 19v3" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <span v-else class="w-5 h-5 rounded-[3px]" style="background: #fff;" />
            </button>

            <button v-if="blob && !recording" @click="onSend" :disabled="sending"
              class="text-[13px] font-semibold active:opacity-60 disabled:opacity-50"
              style="color: var(--color-accent);">
              {{ sending ? t('voice.sending') : t('voice.send') }}
            </button>
            <span v-else class="text-[13px]" style="color: var(--color-ink-4);">
              {{ recording ? t('voice.tapStop') : t('voice.tapStart') }}
            </span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sheet-enter-active, .sheet-leave-active { transition: opacity .2s ease; }
.sheet-enter-from, .sheet-leave-to       { opacity: 0; }

@keyframes vrPulse { 0%,100%{opacity:.4} 50%{opacity:1} }
.vr-pulse-dot { background: #C44; animation: vrPulse 1.2s infinite; }

.vr-bar {
  width: 3px;
  border-radius: 2px;
  background: var(--color-accent);
  opacity: 0.25;
}
.vr-bars-recorded .vr-bar { opacity: 0.85; }

@keyframes vrFlick {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.35; }
}
.vr-bars-active .vr-bar {
  animation: vrFlick 0.6s ease-in-out infinite;
  animation-delay: var(--vr-delay);
}
</style>
