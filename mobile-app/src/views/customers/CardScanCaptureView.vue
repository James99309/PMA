<script setup>
// 名片扫描 · 优先 VisionKit (iOS) 自动边缘检测 + 透视校正,
// 老 build / web 没插件 → fallback 到 @capacitor/camera + 4 角手动裁剪
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ImageCrop4Corners from '@/components/common/ImageCrop4Corners.vue'
import { useCardScanStore } from '@/stores/cardScan'
import { scanBusinessCard } from '@/api/customers'
import { Capacitor } from '@capacitor/core'
import { DocumentScanner } from '@/plugins/documentScanner'

const route = useRoute()
const router = useRouter()
const scanStore = useCardScanStore()

// 状态: capture (调相机/扫描) | preview (拍完预览, 让用户决定用这张还是重拍)
//       | crop (兜底手动裁剪) | processing (上传+OCR)
const step = ref('capture')
const photoUrl = ref('')      // fallback 路径: 拍到的原图 blob URL
const photoBlob = ref(null)
const cameraInputEl = ref(null)
const error = ref('')

// preview 步用: VisionKit 裁好的高清 dataUrl + 对应 blob (用于上传)
const previewDataUrl = ref('')
const previewBlob = ref(null)

// 把 dataUrl ('data:image/jpeg;base64,...') 转 Blob, 用于 multipart 上传
function dataUrlToBlob(dataUrl) {
  const [meta, b64] = dataUrl.split(',')
  const mime = (meta.match(/data:([^;]+)/) || [, 'image/jpeg'])[1]
  const bin = atob(b64)
  const buf = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i)
  return new Blob([buf], { type: mime })
}

// 调试: VisionKit 不工作时把原因暴露到 UI, 用户可截图反馈
const visionKitDebug = ref('')

async function tryVisionKit() {
  if (!Capacitor.isNativePlatform?.()) {
    visionKitDebug.value = 'web 环境无 VisionKit'
    return false
  }
  try {
    const r = await DocumentScanner.isAvailable()
    if (!r?.available) {
      visionKitDebug.value = `VisionKit 不可用 (返回 ${JSON.stringify(r)})`
      return false
    }
    // 不传 quality/maxLong, 用插件默认 (0.98 + 不缩放), 名片小字需要原图清晰度
    const scan = await DocumentScanner.scan({})
    const page = scan?.pages?.[0]
    if (!page?.dataUrl) {
      error.value = '未识别到名片'
      return true   // 已"占用"流程, 不再 fallback
    }
    // VisionKit 已经裁剪 + 透视校正 → 进预览页, 让用户决定 OCR 还是重拍
    previewDataUrl.value = page.dataUrl
    previewBlob.value = dataUrlToBlob(page.dataUrl)
    step.value = 'preview'
    return true
  } catch (e) {
    const msg = e?.message || String(e || '')
    if (msg.includes('cancelled')) {
      // 用户取消 → 退出
      router.back()
      return true
    }
    visionKitDebug.value = `VisionKit error: ${msg.slice(0, 120)}`
    if (msg.includes('not supported') || msg.includes('not implemented')
        || msg.includes('UNIMPLEMENTED')) {
      return false   // fallback to manual
    }
    console.warn('VisionKit scan failed, falling back:', msg)
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
        router.back()
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

// 4 角裁剪完毕 → 进预览页 (跟 VisionKit 路径一致)
async function onCropped({ blob, dataUrl }) {
  if (!blob) {
    error.value = '裁剪失败'
    return
  }
  previewDataUrl.value = dataUrl
  previewBlob.value = blob
  step.value = 'preview'
}

// 预览页: 用这张 → 进 OCR
async function confirmPreview() {
  if (!previewBlob.value || !previewDataUrl.value) return
  await uploadAndOCR(previewBlob.value, previewDataUrl.value)
}

// 预览页: 重新拍 → 回到 capture 步, 重新调 VisionKit / 相机
async function retakePreview() {
  previewBlob.value = null
  previewDataUrl.value = ''
  step.value = 'capture'
  // 优先 VisionKit, fallback 手动相机
  const used = await tryVisionKit()
  if (!used) await startManualCamera()
}

async function uploadAndOCR(blob, dataUrl) {
  step.value = 'processing'
  scanStore.cropDataUrl = dataUrl
  try {
    const res = await scanBusinessCard(blob, `business_card_${Date.now()}.jpg`)
    const data = res.data?.data
    if (!res.data?.success || !data?.fields) {
      error.value = res.data?.message || '识别失败'
      step.value = 'crop'
      return
    }
    scanStore.setOcr({
      cropDataUrl: dataUrl,
      fileUrl: data.file_url || '',
      fields: data.fields,
      ocrJson: data.ocr_json || '',
    })
    router.replace('/customers/scan/confirm')
  } catch (e) {
    error.value = `请求失败: ${e?.message || e}`
    step.value = 'crop'
  }
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

onMounted(async () => {
  scanStore.clear()
  // 客户详情页过来扫名片时, attachTo 标记目标客户 ID
  if (route.query.attachTo) {
    scanStore.setAttachTo(Number(route.query.attachTo), route.query.attachToName || '')
  }
  // 优先 VisionKit; 不可用则回退手动相机
  const usedVisionKit = await tryVisionKit()
  if (!usedVisionKit) await startManualCamera()
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

    <!-- step: capture (扫描或相机调用中) -->
    <div v-if="step === 'capture'" class="flex-1 flex flex-col items-center justify-center text-white px-6 text-center">
      <div class="text-[14px] opacity-80">正在打开相机…</div>
      <p class="mt-4 text-[12px] opacity-60" style="line-height: 1.55;">
        💡 把名片放在桌面平整位置, 设备保持稳定 1-2 秒等聚焦,<br>
        系统会自动捕捉, 也可以手动按白色快门
      </p>
      <div v-if="error" class="mt-4 text-[13px]" style="color: #FF6B6B;">{{ error }}</div>
      <button v-if="error" @click="router.back()"
        class="mt-6 px-5 py-2 rounded-full text-[13px]"
        style="background: rgba(255,255,255,0.15); color: #fff;">返回</button>
    </div>

    <!-- step: crop (fallback 手动裁剪) -->
    <ImageCrop4Corners v-else-if="step === 'crop' && photoUrl"
      :src="photoUrl" @crop="onCropped" @cancel="onCropCancel" />

    <!-- step: preview (拍好后让用户确认 / 重拍, 之后才进 OCR) -->
    <div v-else-if="step === 'preview' && previewDataUrl" class="flex flex-col h-full">
      <div class="flex items-center justify-between px-4 py-3 shrink-0"
        style="background: rgba(0,0,0,0.85);">
        <button @click="router.back()" class="text-white text-[14px] active:opacity-70">取消</button>
        <span class="text-white text-[14px] opacity-80">看清楚名片再识别</span>
        <span class="w-12"></span>
      </div>
      <div class="flex-1 flex items-center justify-center overflow-auto" style="background: #111;">
        <img :src="previewDataUrl" class="block"
          style="max-width: 100%; max-height: 100%; object-fit: contain;" />
      </div>
      <div class="px-4 pt-3 shrink-0"
        style="background: rgba(0,0,0,0.85); padding-bottom: calc(env(safe-area-inset-bottom) + 16px);">
        <p class="text-center mb-3" style="font-size: 12px; color: rgba(255,255,255,0.65);">
          字够清晰吗? 模糊就重拍, 否则识别准确率会下降
        </p>
        <div class="flex gap-3">
          <button @click="retakePreview"
            class="flex-1 py-3.5 rounded-xl text-[15px] font-medium active:opacity-70"
            style="background: rgba(255,255,255,0.12); color: #fff; border: 1px solid rgba(255,255,255,0.25);">
            重新拍
          </button>
          <button @click="confirmPreview"
            class="rounded-xl text-[15px] font-semibold active:opacity-70"
            style="flex: 1.6; padding: 14px 0; background: var(--color-accent); color: #fff;">
            用这张 · AI 识别
          </button>
        </div>
      </div>
    </div>

    <!-- 调试条: VisionKit 不工作时显示原因, 帮助诊断 (临时) -->
    <div v-if="visionKitDebug" class="absolute left-2 right-2 px-3 py-1.5 rounded text-[11px]"
      style="bottom: env(safe-area-inset-bottom); background: rgba(255,180,0,0.9); color: #000; max-width: 100%;">
      🛠 {{ visionKitDebug }}
    </div>

    <!-- step: processing (上传 + Claude OCR) -->
    <div v-else-if="step === 'processing'"
      class="flex-1 flex flex-col items-center justify-center text-white px-6 text-center">
      <div class="inline-block animate-spin"
        style="width: 36px; height: 36px; border: 3px solid rgba(255,255,255,0.25); border-top-color: #fff; border-radius: 18px;"></div>
      <div class="mt-4 text-[14px]">AI 正在识别名片字段…</div>
      <div class="mt-2 text-[12px] opacity-60">通常 2-5 秒</div>
    </div>
  </div>
</template>
