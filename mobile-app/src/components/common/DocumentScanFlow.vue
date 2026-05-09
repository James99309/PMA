<!--
  DocumentScanFlow · 通用文档扫描流(名片 / 发票等共用)
  封装: VisionKit DocumentScanner 优先 → fallback Camera + ImageCrop4Corners
  生命周期: capture (调相机) → crop (兜底手动 4 角) → preview (拍后预览)
  发出事件:
    - done(pages: [{blob, dataUrl}])  用户最终确认的所有页 (1 或多张)
    - cancel()                         用户取消(无任何页)

  Props:
    - allowMulti: 是否允许累积多张(发票场景)
    - captureTip: capture 步说明文字
    - previewTip: preview 步说明文字
    - primaryLabel: 单张时主 CTA 文字
    - multiPrimaryFormat: 多张时主 CTA 模板(用 {n} 占位待拍数)

  内部状态: 累积已确认的 pages, allowMulti=false 时 1 张就 emit done; true 时由用户决定
-->
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { Capacitor } from '@capacitor/core'
import { DocumentScanner } from '@/plugins/documentScanner'
import ImageCrop4Corners from '@/components/common/ImageCrop4Corners.vue'

const props = defineProps({
  allowMulti: { type: Boolean, default: false },
  captureTip: { type: String, default: '把文档放在桌面平整位置, 设备保持稳定, 系统会自动捕捉' },
  previewTip: { type: String, default: '字够清晰吗? 模糊就重拍' },
  primaryLabel: { type: String, default: 'AI 识别' },
  multiPrimaryFormat: { type: String, default: '用这张 · 共 {n} 张 · 开始识别' },
  // 是否在 mount 时立即触发 VisionKit / 相机(默认 true)
  autoStart: { type: Boolean, default: true },
})

const emit = defineEmits(['done', 'cancel'])

// 状态: capture (调相机/扫描) | crop (兜底手动裁剪) | preview (拍完预览)
const step = ref('capture')
const photoUrl = ref('')
const photoBlob = ref(null)
const previewDataUrl = ref('')
const previewBlob = ref(null)
const cameraInputEl = ref(null)
const error = ref('')
const visionKitDebug = ref('')

// allowMulti=true 时累积已确认的页(每页 {blob, dataUrl})
const accumulated = ref([])
const accumulatedCount = computed(() => accumulated.value.length)

// data:URL → Blob (用于 multipart 上传)
function dataUrlToBlob(dataUrl) {
  const [meta, b64] = dataUrl.split(',')
  const mime = (meta.match(/data:([^;]+)/) || [, 'image/jpeg'])[1]
  const bin = atob(b64)
  const buf = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i)
  return new Blob([buf], { type: mime })
}

async function tryVisionKit() {
  if (!Capacitor.isNativePlatform?.()) {
    visionKitDebug.value = 'web 环境无 VisionKit'
    return false
  }
  try {
    const r = await DocumentScanner.isAvailable()
    if (!r?.available) {
      visionKitDebug.value = `VisionKit 不可用 (${JSON.stringify(r)})`
      return false
    }
    // 不限制页数 + 不压缩, 保留原图清晰度
    const scan = await DocumentScanner.scan({})
    const rawPages = scan?.pages || []
    if (rawPages.length === 0) {
      // 用户取消 / 未识别
      finalizeOrCancel()
      return true
    }
    // 全部入累积
    for (const p of rawPages) {
      if (!p?.dataUrl) continue
      accumulated.value.push({
        dataUrl: p.dataUrl,
        blob: dataUrlToBlob(p.dataUrl),
      })
    }
    // VisionKit 已让用户连拍多张, 直接 emit done (allowMulti 也无需再让用户决定)
    emit('done', accumulated.value)
    return true
  } catch (e) {
    const msg = e?.message || String(e || '')
    if (msg.includes('cancelled') || msg.includes('canceled')) {
      finalizeOrCancel()
      return true
    }
    visionKitDebug.value = `VisionKit error: ${msg.slice(0, 120)}`
    if (msg.includes('not supported') || msg.includes('not implemented')
        || msg.includes('UNIMPLEMENTED')) {
      return false
    }
    console.warn('VisionKit failed, falling back:', msg)
    return false
  }
}

async function startManualCamera() {
  error.value = ''
  if (Capacitor.isNativePlatform?.()) {
    try {
      const { Camera, CameraResultType, CameraSource } = await import('@capacitor/camera')
      const photo = await Camera.getPhoto({
        quality: 90,
        allowEditing: false,
        resultType: CameraResultType.Uri,
        source: CameraSource.Camera,
        saveToGallery: false,
      })
      const res = await fetch(photo.webPath)
      const blob = await res.blob()
      photoBlob.value = blob
      photoUrl.value = URL.createObjectURL(blob)
      step.value = 'crop'
    } catch (e) {
      const msg = e?.message || String(e || '')
      if (msg.includes('cancelled') || msg.includes('canceled') || msg.includes('User cancelled')) {
        finalizeOrCancel()
        return
      }
      error.value = `相机调用失败: ${msg.slice(0, 80)}`
    }
  } else {
    cameraInputEl.value?.click()
  }
}

function onWebPhoto(e) {
  const f = e.target.files?.[0]
  if (!f) return
  photoBlob.value = f
  photoUrl.value = URL.createObjectURL(f)
  step.value = 'crop'
  e.target.value = ''
}

async function onCropped({ blob, dataUrl }) {
  if (!blob) {
    error.value = '裁剪失败'
    return
  }
  previewDataUrl.value = dataUrl
  previewBlob.value = blob
  step.value = 'preview'
}

function onCropCancel() {
  if (photoUrl.value && photoUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(photoUrl.value)
  }
  photoUrl.value = ''
  photoBlob.value = null
  step.value = 'capture'
  startManualCamera()
}

// 用这张 + 完成
function confirmAndFinish() {
  if (!previewBlob.value || !previewDataUrl.value) return
  accumulated.value.push({
    dataUrl: previewDataUrl.value,
    blob: previewBlob.value,
  })
  previewDataUrl.value = ''
  previewBlob.value = null
  emit('done', accumulated.value)
}

// 用这张 + 继续(多张模式)
async function confirmAndContinue() {
  if (!previewBlob.value || !previewDataUrl.value) return
  accumulated.value.push({
    dataUrl: previewDataUrl.value,
    blob: previewBlob.value,
  })
  previewDataUrl.value = ''
  previewBlob.value = null
  step.value = 'capture'
  await startManualCamera()
}

// 重拍当前页
async function retakePreview() {
  previewDataUrl.value = ''
  previewBlob.value = null
  step.value = 'capture'
  await startManualCamera()
}

// 用户从相机直接退出 → 已拍的累积页提交; 否则取消
function finalizeOrCancel() {
  if (accumulated.value.length > 0) {
    emit('done', accumulated.value)
  } else {
    emit('cancel')
  }
}

const finishLabel = computed(() => {
  if (!props.allowMulti) return props.primaryLabel
  const total = accumulatedCount.value + 1  // +1 当前预览页
  if (total <= 1) return props.primaryLabel
  return props.multiPrimaryFormat.replace('{n}', total)
})

// 公开方法 — 父组件可以手动触发
defineExpose({
  start: async () => {
    const used = await tryVisionKit()
    if (!used) await startManualCamera()
  },
})

onMounted(async () => {
  if (props.autoStart) {
    const used = await tryVisionKit()
    if (!used) await startManualCamera()
  }
})

onBeforeUnmount(() => {
  if (photoUrl.value && photoUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(photoUrl.value)
  }
})
</script>

<template>
  <div class="flex flex-col h-full" style="background: #000;">
    <input ref="cameraInputEl" type="file" accept="image/*" capture="environment"
      @change="onWebPhoto" style="display: none;" />

    <!-- step: capture -->
    <div v-if="step === 'capture'"
      class="flex-1 flex flex-col items-center justify-center text-white px-6 text-center">
      <div class="text-[14px] opacity-80">正在打开相机…</div>
      <p class="mt-4 text-[12px] opacity-60" style="line-height: 1.55;">{{ captureTip }}</p>
      <div v-if="accumulatedCount > 0" class="mt-3 text-[12px]" style="color: var(--color-accent);">
        已拍 {{ accumulatedCount }} 张
      </div>
      <div v-if="error" class="mt-4 text-[13px]" style="color: #FF6B6B;">{{ error }}</div>
      <button v-if="error" @click="finalizeOrCancel"
        class="mt-6 px-5 py-2 rounded-full text-[13px]"
        style="background: rgba(255,255,255,0.15); color: #fff;">返回</button>
    </div>

    <!-- step: crop (fallback 手动 4 角) -->
    <ImageCrop4Corners v-else-if="step === 'crop' && photoUrl"
      :src="photoUrl" @crop="onCropped" @cancel="onCropCancel" />

    <!-- step: preview -->
    <div v-else-if="step === 'preview' && previewDataUrl" class="flex flex-col h-full">
      <div class="flex items-center justify-between px-4 py-3 shrink-0"
        style="background: rgba(0,0,0,0.85);">
        <button @click="finalizeOrCancel"
          class="text-white text-[14px] active:opacity-70">取消</button>
        <span class="text-white text-[14px] opacity-80">{{ previewTip }}</span>
        <span class="w-12 text-right">
          <span v-if="allowMulti && accumulatedCount > 0"
            class="text-[12px]" style="color: var(--color-accent);">
            已 {{ accumulatedCount }}
          </span>
        </span>
      </div>
      <div class="flex-1 flex items-center justify-center overflow-auto" style="background: #111;">
        <img :src="previewDataUrl" class="block"
          style="max-width: 100%; max-height: 100%; object-fit: contain;" />
      </div>
      <div class="px-4 pt-3 shrink-0"
        style="background: rgba(0,0,0,0.85); padding-bottom: calc(env(safe-area-inset-bottom) + 16px);">
        <p class="text-center mb-3" style="font-size: 12px; color: rgba(255,255,255,0.65);">
          看清楚字段, 模糊就重拍, 否则识别准确率会下降
        </p>

        <!-- 多张模式: 重拍 / 继续拍 / 完成 三按钮 -->
        <template v-if="allowMulti">
          <div class="flex gap-3 mb-2">
            <button @click="retakePreview"
              class="flex-1 py-3 rounded-xl text-[14px] font-medium active:opacity-70"
              style="background: rgba(255,255,255,0.12); color: #fff; border: 1px solid rgba(255,255,255,0.25);">
              重拍
            </button>
            <button @click="confirmAndContinue"
              class="flex-1 py-3 rounded-xl text-[14px] font-medium active:opacity-70"
              style="background: rgba(255,255,255,0.12); color: #fff; border: 1px solid rgba(255,255,255,0.25);">
              用这张 · 继续拍
            </button>
          </div>
          <button @click="confirmAndFinish"
            class="w-full rounded-xl text-[15px] font-semibold active:opacity-70"
            style="padding: 13px 0; background: var(--color-accent); color: #fff;">
            {{ finishLabel }}
          </button>
        </template>

        <!-- 单张模式: 重拍 / 用这张 两按钮 -->
        <div v-else class="flex gap-3">
          <button @click="retakePreview"
            class="flex-1 py-3.5 rounded-xl text-[15px] font-medium active:opacity-70"
            style="background: rgba(255,255,255,0.12); color: #fff; border: 1px solid rgba(255,255,255,0.25);">
            重新拍
          </button>
          <button @click="confirmAndFinish"
            class="rounded-xl text-[15px] font-semibold active:opacity-70"
            style="flex: 1.6; padding: 14px 0; background: var(--color-accent); color: #fff;">
            用这张 · {{ primaryLabel }}
          </button>
        </div>
      </div>
    </div>

    <!-- 调试条 -->
    <div v-if="visionKitDebug" class="absolute left-2 right-2 px-3 py-1.5 rounded text-[11px]"
      style="bottom: env(safe-area-inset-bottom); background: rgba(255,180,0,0.9); color: #000; max-width: 100%;">
      🛠 {{ visionKitDebug }}
    </div>
  </div>
</template>
