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
import { useI18n } from 'vue-i18n'
import { Capacitor } from '@capacitor/core'
import { DocumentScanner } from '@/plugins/documentScanner'
import ImageCrop4Corners from '@/components/common/ImageCrop4Corners.vue'

const { t } = useI18n()

const props = defineProps({
  allowMulti: { type: Boolean, default: false },
  captureTip: { type: String, default: '' },
  previewTip: { type: String, default: '' },
  primaryLabel: { type: String, default: '' },
  multiPrimaryFormat: { type: String, default: '' },
  // 是否在 mount 时立即触发 VisionKit / 相机(默认 true)
  autoStart: { type: Boolean, default: true },
})

const captureTipText = computed(() => props.captureTip || t('scan.captureTip'))
const previewTipText = computed(() => props.previewTip || t('scan.previewTip'))
const primaryLabelText = computed(() => props.primaryLabel || t('scan.primaryLabel'))
const multiPrimaryFormatText = computed(() => props.multiPrimaryFormat || t('scan.multiPrimaryFormat'))

const emit = defineEmits(['done', 'cancel'])

// 状态: capture (调相机/扫描) | crop (兜底手动裁剪) | preview (拍完预览)
const step = ref('capture')
const photoUrl = ref('')
const photoBlob = ref(null)
const previewDataUrl = ref('')
const previewBlob = ref(null)
const cameraInputEl = ref(null)
const galleryInputEl = ref(null)
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
    visionKitDebug.value = t('scan.visionKitWebEnv')
    return false
  }
  try {
    const r = await DocumentScanner.isAvailable()
    if (!r?.available) {
      visionKitDebug.value = t('scan.visionKitUnavailable', { err: JSON.stringify(r) })
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
        // 不再立刻 finalize, 让用户在 capture 屏看到 "从相册" / "重拍" 按钮
        return
      }
      error.value = t('scan.cameraFail', { msg: msg.slice(0, 80) })
    }
  } else {
    cameraInputEl.value?.click()
  }
}

// 从相册/文件 picker 选已有照片 (跳过 VisionKit; 选完直接走 crop → preview 流程)
async function startFromGallery() {
  error.value = ''
  if (Capacitor.isNativePlatform?.()) {
    try {
      const { Camera, CameraResultType, CameraSource } = await import('@capacitor/camera')
      const photo = await Camera.getPhoto({
        quality: 90,
        allowEditing: false,
        resultType: CameraResultType.Uri,
        source: CameraSource.Photos,  // 强制从相册选, 不走相机
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
        return
      }
      error.value = t('scan.galleryFail', { msg: msg.slice(0, 80) })
    }
  } else {
    // web 退化方案: 同 input file 但不带 capture, 让浏览器开"文件选择"
    galleryInputEl.value?.click()
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
    error.value = t('scan.cropFail')
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
  if (!props.allowMulti) return primaryLabelText.value
  const total = accumulatedCount.value + 1  // +1 当前预览页
  if (total <= 1) return primaryLabelText.value
  return multiPrimaryFormatText.value.replace('{n}', total)
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
    <input ref="galleryInputEl" type="file" accept="image/*"
      @change="onWebPhoto" style="display: none;" />

    <!-- step: capture -->
    <div v-if="step === 'capture'"
      class="flex-1 flex flex-col items-center justify-center text-white px-6 text-center">
      <div class="text-[14px] opacity-80">{{ t('scan.openingCamera') }}</div>
      <p class="mt-4 text-[12px] opacity-60" style="line-height: 1.55;">{{ captureTipText }}</p>
      <div v-if="accumulatedCount > 0" class="mt-3 text-[12px]" style="color: var(--color-accent);">
        {{ t('scan.shotsN', { n: accumulatedCount }) }}
      </div>
      <div v-if="error" class="mt-4 text-[13px]" style="color: #FF6B6B;">{{ error }}</div>

      <!-- 主备入口: 用户如果意外关掉了相机弹窗, 还能从这里选相册 / 重拍 -->
      <div class="mt-8 flex flex-col items-center gap-3">
        <button @click="startManualCamera"
          class="px-6 py-2.5 rounded-full text-[14px] font-medium active:opacity-70"
          style="background: rgba(255,255,255,0.18); color: #fff; border: 1px solid rgba(255,255,255,0.3);">
          📷 {{ t('scan.retake') }}
        </button>
        <button @click="startFromGallery"
          class="text-[13px] active:opacity-70"
          style="color: var(--color-accent); padding: 6px 12px;">
          🖼 {{ t('scan.fromGallery') }}
        </button>
        <button @click="finalizeOrCancel"
          class="text-[12px] active:opacity-70 mt-1"
          style="color: rgba(255,255,255,0.5);">
          {{ t('scan.back') }}
        </button>
      </div>
    </div>

    <!-- step: crop (fallback 手动 4 角) -->
    <ImageCrop4Corners v-else-if="step === 'crop' && photoUrl"
      :src="photoUrl" @crop="onCropped" @cancel="onCropCancel" />

    <!-- step: preview -->
    <div v-else-if="step === 'preview' && previewDataUrl" class="flex flex-col h-full">
      <div class="flex items-center justify-between px-4 py-3 shrink-0"
        style="background: rgba(0,0,0,0.85);">
        <button @click="finalizeOrCancel"
          class="text-white text-[14px] active:opacity-70">{{ t('scan.cancel') }}</button>
        <span class="text-white text-[14px] opacity-80">{{ previewTipText }}</span>
        <span class="w-12 text-right">
          <span v-if="allowMulti && accumulatedCount > 0"
            class="text-[12px]" style="color: var(--color-accent);">
            {{ t('scan.accumulatedN', { n: accumulatedCount }) }}
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
          {{ t('scan.previewTipDetail') }}
        </p>

        <!-- 多张模式: 重拍 / 继续拍 / 完成 三按钮 -->
        <template v-if="allowMulti">
          <div class="flex gap-3 mb-2">
            <button @click="retakePreview"
              class="flex-1 py-3 rounded-xl text-[14px] font-medium active:opacity-70"
              style="background: rgba(255,255,255,0.12); color: #fff; border: 1px solid rgba(255,255,255,0.25);">
              {{ t('scan.retake') }}
            </button>
            <button @click="confirmAndContinue"
              class="flex-1 py-3 rounded-xl text-[14px] font-medium active:opacity-70"
              style="background: rgba(255,255,255,0.12); color: #fff; border: 1px solid rgba(255,255,255,0.25);">
              {{ t('scan.useThisContinue') }}
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
            {{ t('scan.retakeAll') }}
          </button>
          <button @click="confirmAndFinish"
            class="rounded-xl text-[15px] font-semibold active:opacity-70"
            style="flex: 1.6; padding: 14px 0; background: var(--color-accent); color: #fff;">
            {{ t('scan.useThisLabel', { label: primaryLabelText }) }}
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
