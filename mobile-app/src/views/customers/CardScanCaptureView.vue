<!--
  CardScanCaptureView · 名片扫描 - 复用 DocumentScanFlow 公用组件
  本视图只负责: 接收 done 事件 → 调 OCR API → 跳到 confirm 页
  与 ReceiptCaptureView 共享同一套 capture/crop/preview UI
-->
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DocumentScanFlow from '@/components/common/DocumentScanFlow.vue'
import OcrProcessingAnimation from '@/components/common/OcrProcessingAnimation.vue'
import { useCardScanStore } from '@/stores/cardScan'
import { scanBusinessCard } from '@/api/customers'

const route = useRoute()
const router = useRouter()
const scanStore = useCardScanStore()

const processing = ref(false)
const error = ref('')

// 名片识别字段揭示动画 (与 OCR 实际返回字段对齐)
const ocrFields = [
  { label: '姓名',     val: '识别中...', confident: true },
  { label: '公司',     val: '识别中...', confident: true },
  { label: '职务',     val: '识别中...', confident: true },
  { label: '电话',     val: '识别中...', confident: true },
  { label: '邮箱',     val: '识别中...', confident: false },
]

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
    <!-- OCR 进行中: 复用通用 OCR 动画 (单卡 + 字段揭示, 替代黑屏 spinner) -->
    <div v-if="processing" class="h-full" style="background: var(--color-ex-bg, #F7F5F2);">
      <OcrProcessingAnimation
        :card-count="1"
        title="正在识别名片"
        subtitle="通常 2-5 秒"
        :fields="ocrFields"
        :error="error"
        @retry="processing = false; error = ''"
      />
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
