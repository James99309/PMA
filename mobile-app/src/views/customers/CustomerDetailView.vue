<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCustomer, addCustomerNote, addContact } from '@/api/customers'

const route = useRoute()
const router = useRouter()
const company = ref(null)
const loading = ref(true)

// 跟进
const showNoteBox = ref(false)
const noteText = ref('')
const addingNote = ref(false)

// 新增联系人
const showContactForm = ref(false)
const newContact = ref({ name: '', position: '', phone: '', email: '', department: '' })
const addingContact = ref(false)

async function load() {
  try {
    const res = await getCustomer(route.params.id)
    company.value = res.data.data
  } finally {
    loading.value = false
  }
}

async function submitNote() {
  if (!noteText.value.trim()) return
  addingNote.value = true
  try {
    await addCustomerNote(route.params.id, noteText.value.trim())
    noteText.value = ''
    showNoteBox.value = false
    await load()
  } finally {
    addingNote.value = false
  }
}

async function submitContact() {
  if (!newContact.value.name.trim()) return
  addingContact.value = true
  try {
    await addContact(route.params.id, newContact.value)
    newContact.value = { name: '', title: '', phone: '', email: '', department: '' }
    showContactForm.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.message || '添加失败')
  } finally {
    addingContact.value = false
  }
}

function callPhone(phone) { if (phone) window.open(`tel:${phone}`) }
function sendEmail(email) { if (email) window.open(`mailto:${email}`) }

onMounted(load)
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- 顶部栏 -->
    <div class="bg-white border-b border-gray-100 px-4 py-3 flex items-center gap-2">
      <button @click="router.back()" class="text-blue-500 p-1 -ml-1 shrink-0">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-gray-900 flex-1 truncate text-sm">客户详情</h1>
      <button @click="showNoteBox = !showNoteBox"
        class="text-blue-500 text-xs px-2 py-1 border border-blue-200 rounded-lg shrink-0">
        + 跟进
      </button>
    </div>

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <div v-else-if="company" class="flex-1 overflow-y-auto">

      <!-- 基本信息 -->
      <div class="bg-white px-4 py-5">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-lg font-bold shrink-0">
            {{ company.name?.[0] }}
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-base font-bold text-gray-900 leading-tight">{{ company.name }}</h2>
            <p class="text-xs text-gray-400 mt-0.5">
              {{ [company.industry, company.city, company.region].filter(Boolean).join(' · ') || '暂无行业信息' }}
            </p>
          </div>
        </div>
        <div v-if="company.address" class="flex items-start gap-1.5 text-sm text-gray-500">
          <svg class="w-4 h-4 shrink-0 mt-0.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a2 2 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          </svg>
          {{ company.address }}
        </div>
      </div>

      <!-- 联系人 -->
      <div class="h-2 bg-gray-50" />
      <div class="bg-white">
        <div class="px-4 pt-3 pb-1 flex items-center justify-between">
          <p class="text-xs text-gray-400">联系人 ({{ company.contacts?.length || 0 }})</p>
          <button @click="showContactForm = !showContactForm"
            class="text-blue-500 text-xs flex items-center gap-1">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            新增联系人
          </button>
        </div>

        <!-- 新增联系人表单 -->
        <div v-if="showContactForm" class="px-4 pb-4 space-y-2 border-b border-gray-100">
          <input v-model="newContact.name" type="text" placeholder="姓名 *"
            class="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-blue-400" />
          <input v-model="newContact.position" type="text" placeholder="职位"
            class="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-blue-400" />
          <input v-model="newContact.department" type="text" placeholder="部门"
            class="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-blue-400" />
          <input v-model="newContact.phone" type="tel" placeholder="电话"
            class="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-blue-400" />
          <input v-model="newContact.email" type="email" placeholder="邮箱"
            class="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-blue-400" />
          <div class="flex gap-2 pt-1">
            <button @click="showContactForm = false"
              class="flex-1 border border-gray-200 text-gray-600 rounded-xl py-2 text-sm">取消</button>
            <button @click="submitContact" :disabled="addingContact || !newContact.name.trim()"
              class="flex-1 bg-blue-600 text-white rounded-xl py-2 text-sm disabled:opacity-60">
              {{ addingContact ? '添加中...' : '确认添加' }}
            </button>
          </div>
        </div>

        <!-- 联系人列表 -->
        <ul v-if="company.contacts?.length" class="divide-y divide-gray-50">
          <li v-for="ct in company.contacts" :key="ct.id" class="px-4 py-3.5 flex items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <p class="font-medium text-gray-900 text-sm">{{ ct.name }}</p>
              <p class="text-xs text-gray-400 mt-0.5">
                {{ [ct.position, ct.department].filter(Boolean).join(' · ') || '暂无职位信息' }}
              </p>
              <p v-if="ct.phone" class="text-xs text-gray-500 mt-0.5">{{ ct.phone }}</p>
            </div>
            <div class="flex gap-2 shrink-0">
              <button v-if="ct.phone" @click="callPhone(ct.phone)"
                class="w-9 h-9 bg-green-100 rounded-full flex items-center justify-center text-green-600 active:bg-green-200">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
              </button>
              <button v-if="ct.email" @click="sendEmail(ct.email)"
                class="w-9 h-9 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 active:bg-blue-200">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
          </li>
        </ul>
        <p v-else class="px-4 py-4 text-sm text-gray-400 text-center">暂无联系人</p>
      </div>

      <!-- 跟进记录 -->
      <div class="h-2 bg-gray-50" />
      <div class="bg-white px-4 py-3">
        <p class="text-xs text-gray-400 mb-3">跟进记录 ({{ company.actions?.length || 0 }})</p>
        <ul v-if="company.actions?.length" class="space-y-3">
          <li v-for="a in company.actions" :key="a.id" class="flex gap-2">
            <div class="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 shrink-0" />
            <div class="flex-1 min-w-0">
              <p class="text-xs text-gray-400 mb-0.5">{{ a.date }} · {{ a.owner_name }}</p>
              <p class="text-sm text-gray-800 break-words leading-relaxed">{{ a.communication }}</p>
            </div>
          </li>
        </ul>
        <p v-else class="text-sm text-gray-400 text-center py-2">暂无跟进记录</p>
      </div>

      <!-- 跟进输入框 -->
      <div v-if="showNoteBox">
        <div class="h-2 bg-gray-50" />
        <div class="bg-white px-4 py-4">
          <p class="text-xs text-gray-400 mb-2">添加跟进记录</p>
          <textarea v-model="noteText" rows="3" placeholder="输入跟进内容..."
            class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-400 resize-none" />
          <div class="flex gap-2 mt-2">
            <button @click="showNoteBox = false"
              class="flex-1 border border-gray-200 text-gray-600 rounded-xl py-2 text-sm">取消</button>
            <button @click="submitNote" :disabled="addingNote"
              class="flex-1 bg-blue-600 text-white rounded-xl py-2 text-sm disabled:opacity-60">
              {{ addingNote ? '提交中...' : '提交' }}
            </button>
          </div>
        </div>
      </div>

      <div class="h-8" />
    </div>
  </div>
</template>
