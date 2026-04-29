<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.message || '登录失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center px-6 safe-top safe-bottom">
    <div class="mb-10 text-center">
      <div class="text-3xl font-bold text-blue-600">PMA</div>
      <div class="text-gray-500 mt-1 text-sm">产品管理系统</div>
    </div>

    <div class="bg-white rounded-2xl shadow-sm p-6 space-y-4">
      <div>
        <label class="text-sm text-gray-600 block mb-1">用户名 / 邮箱</label>
        <input
          v-model="username"
          type="text"
          autocomplete="username"
          placeholder="请输入用户名"
          @keyup.enter="handleLogin"
          class="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition"
        />
      </div>

      <div>
        <label class="text-sm text-gray-600 block mb-1">密码</label>
        <input
          v-model="password"
          type="password"
          autocomplete="current-password"
          placeholder="请输入密码"
          @keyup.enter="handleLogin"
          class="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition"
        />
      </div>

      <p v-if="error" class="text-red-500 text-sm text-center">{{ error }}</p>

      <button
        @click="handleLogin"
        :disabled="loading"
        class="w-full bg-blue-600 text-white rounded-xl py-3 font-medium text-sm disabled:opacity-60 active:bg-blue-700 transition"
      >
        {{ loading ? '登录中...' : '登录' }}
      </button>
    </div>
  </div>
</template>
