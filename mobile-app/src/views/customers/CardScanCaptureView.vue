<!--
  CardScanCaptureView · 名片扫描 - 复用 DocumentScanFlow 公用组件
  本视图只负责: 接收 done 事件 → 调 OCR API → 跳到 confirm 页
  与 ReceiptCaptureView 共享同一套 capture/crop/preview UI
-->
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DocumentScanFlow from '@/components/common/DocumentScanFlow.vue'
import { useCardScanStore } from '@/stores/cardScan'
import { scanBusinessCard } from '@/api/customers'

const route = useRoute()
const router = useRouter()
const scanStore = useCardScanStore()

const processing = ref(false)
const error = ref('')

onMounted(() => {
  scanStore.clear()
  if (route.query.attachTo) {
    scanStore.setAttachTo(Number(route.query.attachTo), route.query.attachToName || '')
  }
})

async function onDone(pages) {
  if (!pages || pages.length === 0) {
    router.back()
    return
  }
  // 名片是单张
  const { blob, dataUrl } = pages[0]
  await uploadAndOCR(blob, dataUrl)
}

async function uploadAndOCR(blob, dataUrl) {
  processing.value = true
  error.value = ''
  scanStore.cropDataUrl = dataUrl
  try {
    const res = await scanBusinessCard(blob, `business_card_${Date.now()}.jpg`)
    const data = res.data?.data
    if (!res.data?.success || !data?.fields) {
      error.value = res.data?.message || '识别失败'
      processing.value = false
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
    processing.value = false
  }
}
</script>

<template>
  <div class="h-full">
    <!-- OCR 进行中: 全屏 loading -->
    <div v-if="processing" class="flex flex-col items-center justify-center h-full text-white px-6 text-center"
      style="background: #000;">
      <div class="inline-block animate-spin"
        style="width: 36px; height: 36px; border: 3px solid rgba(255,255,255,0.25); border-top-color: #fff; border-radius: 18px;" />
      <div class="mt-4 text-[14px]">AI 正在识别名片字段…</div>
      <div class="mt-2 text-[12px] opacity-60">通常 2-5 秒</div>
      <div v-if="error" class="mt-4 text-[13px]" style="color: #FF6B6B;">{{ error }}</div>
      <button v-if="error" @click="processing = false; error = ''"
        class="mt-6 px-5 py-2 rounded-full text-[13px]"
        style="background: rgba(255,255,255,0.15); color: #fff;">重拍</button>
    </div>

    <!-- 扫描流(VisionKit / Camera fallback) -->
    <DocumentScanFlow
      v-else
      :allow-multi="false"
      capture-tip="把名片放在桌面平整位置, 设备保持稳定 1-2 秒等聚焦, 系统会自动捕捉, 也可以手动按白色快门"
      preview-tip="看清楚名片再识别"
      primary-label="AI 识别"
      @done="onDone"
      @cancel="$router.back()"
    />
  </div>
</template>
