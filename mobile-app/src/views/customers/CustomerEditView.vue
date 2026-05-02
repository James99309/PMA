<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCustomer, updateCustomer, archiveCustomer } from '@/api/customers'
import EditField from '@/components/common/EditField.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const saving = ref(false)
const archiving = ref(false)
const focusedKey = ref('company_name')  // 默认聚焦公司名

const form = ref({
  company_name: '',
  company_type: '',
  industry: '',
  address: '',
  status: '',
  source: '',
})

const totalCount = ref(0)  // 名下项目数

async function load() {
  try {
    const res = await getCustomer(route.params.id)
    const c = res.data.data
    form.value = {
      company_name: c.name || '',
      company_type: c.company_type || '',
      industry:     c.industry || '',
      address:      c.address || '',
      status:       c.status || '活跃',
      source:       c.source || '',
    }
    totalCount.value = c.total_count || 0
  } finally {
    loading.value = false
  }
}

const subtitle = computed(() => totalCount.value > 0
  ? `修改客户档案，改动会同步到名下 ${totalCount.value} 个项目。`
  : '修改客户档案。')

async function save() {
  saving.value = true
  try {
    await updateCustomer(route.params.id, form.value)
    router.back()
  } catch (e) {
    alert(e.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function archive() {
  if (!confirm(`确认归档客户「${form.value.company_name}」？归档后不再出现在列表中。`)) return
  archiving.value = true
  try {
    await archiveCustomer(route.params.id)
    router.replace('/customers')
  } catch (e) {
    alert(e.response?.data?.message || '归档失败')
  } finally {
    archiving.value = false
  }
}

function transferOwner() {
  alert('转交功能开发中')
}

function deleteCustomer() {
  alert(totalCount.value > 0
    ? `客户名下还有 ${totalCount.value} 个项目，无法直接删除。请先归档。`
    : '硬删除功能开发中，请先归档客户。')
}

onMounted(load)
</script>

<template>
  <div class="flex flex-col h-full overflow-y-auto" style="background: var(--color-bg);">

    <!-- Header — 取消 / 编辑客户 / 保存 -->
    <div class="flex items-center justify-between px-5 py-3 shrink-0">
      <button @click="router.back()" class="text-[15px] active:opacity-60"
        style="color: var(--color-accent);">取消</button>
      <span class="font-serif text-[16px] font-medium">编辑客户</span>
      <button @click="save" :disabled="saving || !form.company_name.trim()"
        class="text-[15px] font-bold active:opacity-60 disabled:opacity-40"
        style="color: var(--color-accent);">
        {{ saving ? '保存中…' : '保存' }}
      </button>
    </div>

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 rounded-full animate-spin"
        style="border-color: var(--color-accent); border-top-color: transparent;" />
    </div>

    <template v-else>
      <!-- 副标题（衬线斜体）-->
      <div class="px-7 pt-3 font-serif italic"
        style="font-size: 13px; color: var(--color-ink-3);">
        {{ subtitle }}
      </div>

      <!-- 基本信息 -->
      <div class="px-7 pt-5 pb-1 text-[11px] font-semibold uppercase"
        style="color: var(--color-ink-3); letter-spacing: 1px;">基本信息</div>
      <div class="mx-5 rounded-2xl py-1"
        style="background: var(--color-card); border: 1px solid var(--color-divider);">
        <EditField label="公司名称" v-model="form.company_name"
          :focused="focusedKey === 'company_name'" @click="focusedKey = 'company_name'" />
        <EditField label="企业类型" v-model="form.company_type"
          :focused="focusedKey === 'company_type'" @click="focusedKey = 'company_type'" />
        <EditField label="行业" v-model="form.industry" arrow
          :focused="focusedKey === 'industry'" @click="focusedKey = 'industry'" />
        <EditField label="地址" v-model="form.address"
          :focused="focusedKey === 'address'" @click="focusedKey = 'address'" />
      </div>

      <!-- 分级 / 状态 -->
      <div class="px-7 pt-5 pb-1 text-[11px] font-semibold uppercase"
        style="color: var(--color-ink-3); letter-spacing: 1px;">分级</div>
      <div class="mx-5 rounded-2xl py-1"
        style="background: var(--color-card); border: 1px solid var(--color-divider);">
        <EditField label="状态" v-model="form.status" arrow
          :focused="focusedKey === 'status'" @click="focusedKey = 'status'" />
        <EditField label="来源" v-model="form.source"
          :focused="focusedKey === 'source'" @click="focusedKey = 'source'" />
      </div>

      <!-- 危险区 -->
      <div class="px-7 pt-6 pb-1 text-[11px] font-semibold uppercase"
        style="color: var(--color-ink-3); letter-spacing: 1px;">其他</div>
      <div class="mx-5 mb-6 flex flex-col gap-2">
        <button @click="transferOwner"
          class="px-4 py-3.5 rounded-xl text-left text-[14px] flex justify-between items-center active:opacity-70"
          style="background: var(--color-card); border: 1px solid var(--color-divider); color: var(--color-ink-2);">
          转交给其他同事
          <svg width="7" height="11" viewBox="0 0 7 11">
            <path d="M1 1l4 4.5L1 10" stroke="var(--color-ink-3)" stroke-width="1.4" fill="none" stroke-linecap="round" />
          </svg>
        </button>
        <button @click="archive" :disabled="archiving"
          class="px-4 py-3.5 rounded-xl text-left text-[14px] active:opacity-70 disabled:opacity-40"
          style="background: var(--color-card); border: 1px solid var(--color-divider); color: #A8533A;">
          {{ archiving ? '归档中…' : '归档客户' }}
        </button>
        <button @click="deleteCustomer"
          class="px-4 py-3.5 rounded-xl text-center text-[14px] font-medium active:opacity-70 mt-2"
          style="background: transparent; border: none; color: #B83C3C;">
          删除客户<template v-if="totalCount > 0">（及全部 {{ totalCount }} 个项目）</template>
        </button>
      </div>

      <div class="h-16" />
    </template>
  </div>
</template>
