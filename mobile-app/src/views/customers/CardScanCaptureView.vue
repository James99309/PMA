<script setup>
// 名片扫描 · 优先 VisionKit (iOS) 自动边缘检测 + 透视校正,
// 老 build / web 没插件 → fallback 到 @capacitor/camera + 4 角手动裁剪
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import ImageCrop4Corners from '@/components/common/ImageCrop4Corners.vue'
import { useCardScanStore } from '@/stores/cardScan'
import { scanBusinessCard } from '@/api/customers'
import { Capacitor } from '@capacitor/core'
import { DocumentScanner } from '@/plugins/documentScanner'

const router = useRouter()
const scanStore = useCardScanStore()

// 状态: capture (调相机/扫描) | crop (兜底手动裁剪) | processing (上传+OCR)
const step = ref('capture')
const photoUrl = ref('')      // fallback 路径: 拍到的原图 blob URL
const photoBlob = ref(null)
const cameraInputEl = ref(null)
const error = ref('')

// 把 dataUrl ('data:image/jpeg;base64,...') 转 Blob, 用于 multipart 上传
function dataUrlToBlob(dataUrl) {
  const [meta, b64] = dataUrl.split(',')
  const mime = (meta.match(/data:([^;]+)/) || [, 'image/jpeg'])[1]
  const bin = atob(b64)
  const buf = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i)
  return new Blob([buf], { type: mime })
}

async function tryVisionKit() {
  if (!Capacitor.isNativePlatform?.()) return false
  try {
    const r = await DocumentScanner.isAvailable()
    if (!r?.available) return false
    const scan = await DocumentScanner.scan({ quality: 0.88, maxLong: 1600 })
    const page = scan?.pages?.[0]
    if (!page?.dataUrl) {
      error.value = '未识别到名片'
      return true   // 已"占用"流程, 不再 fallback
    }
    // VisionKit 已经裁剪 + 透视校正 → 直接进 OCR
    await uploadAndOCR(dataUrlToBlob(page.dataUrl), page.dataUrl)
    return true
  } catch (e) {
    const msg = e?.message || String(e || '')
    if (msg.includes('cancelled')) {
      // 用户取消 → 退出
      router.back()
      return true
    }
    if (msg.includes('not supported')) return false  // fallback
    // 其他错误 → 也 fallback 试旧流程
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

// 4 角裁剪完毕 → 上传+OCR
async function onCropped({ blob, dataUrl }) {
  if (!blob) {
    error.value = '裁剪失败'
    return
  }
  await uploadAndOCR(blob, dataUrl)
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
      <div v-if="error" class="mt-4 text-[13px]" style="color: #FF6B6B;">{{ error }}</div>
      <button v-if="error" @click="router.back()"
        class="mt-6 px-5 py-2 rounded-full text-[13px]"
        style="background: rgba(255,255,255,0.15); color: #fff;">返回</button>
    </div>

    <!-- step: crop (fallback 手动裁剪) -->
    <ImageCrop4Corners v-else-if="step === 'crop' && photoUrl"
      :src="photoUrl" @crop="onCropped" @cancel="onCropCancel" />

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
