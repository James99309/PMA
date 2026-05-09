// 通用召回逻辑 — 任何业务详情页接入审批召回时复用。
// 用法:
//   const { sheetOpen, submitting, open, confirm } = useApprovalRecall({
//     request: () => client.post(`/mobile/projects/${id.value}/recall`),
//     onSuccess: () => load(),
//   })
//
//   <ExFlowSheet @recall="open" />
//   <ExConfirmSheet v-model="sheetOpen" :submitting="submitting" @confirm="confirm" ... />
import { ref } from 'vue'

export function useApprovalRecall({ request, onSuccess, errorPrefix = '召回失败' }) {
  const sheetOpen = ref(false)
  const submitting = ref(false)

  function open() {
    sheetOpen.value = true
  }

  async function confirm() {
    submitting.value = true
    try {
      const r = await request()
      // 兼容两种约定: axios response 含 data.success / mobile api_response 含 success 字段
      const ok = r?.data?.success !== false
      if (ok) {
        sheetOpen.value = false
        await onSuccess?.()
      } else {
        alert(r?.data?.message || errorPrefix)
      }
    } catch (e) {
      alert(`${errorPrefix}: ${e.response?.data?.message || e.message}`)
    } finally {
      submitting.value = false
    }
  }

  return { sheetOpen, submitting, open, confirm }
}
