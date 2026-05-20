<script setup>
// 严格对齐 splash-login.jsx Login 组件（line 188-314）
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import PixelP from '@/components/common/PixelP.vue'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'
import { setLocale } from '@/locales'

// SG 区: 上次登录是 SG (region 持久化) → 登录页一律英文 + SG logo。
// 登录成功后 auth.js 会按 winner 区再次校正 (SG 强制 en)。
const isSG = localStorage.getItem('region') === 'sg'
if (isSG) setLocale('en')

// 键盘抬升: login-form{flex:1} 让 flex 列永远自撑满容器, padding/scroll 路线天生
// 无效 (诊断条实证 sh==ch 永不溢出)。改为键盘弹起时直接 translateY 整个 root, 让
// focus 的输入框抬到键盘上方 —— 与是否可滚无关, 必定生效。kb 高取 main.js 设的
// --kb-height (335px 实证可靠), focus 切换(键盘不收)时也重算。
const liftY = ref(0)
const { onKeyboardDidShow, onKeyboardWillHide } = useKeyboardOffset()

function _kbPx() {
  const v = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--kb-height'))
  return Number.isFinite(v) ? v : 0
}
function recomputeLift() {
  const el = document.activeElement
  const tag = (el?.tagName || '').toLowerCase()
  if (tag !== 'input' && tag !== 'textarea') return
  const kb = _kbPx()
  if (!kb) { liftY.value = 0; return }
  const rect = el.getBoundingClientRect()
  // rect.bottom 含当前 transform → 加回 liftY 还原真实位置, 算绝对目标 (幂等,
  // didShow+focusin 多次调用收敛到同一值, 不会叠加过冲)
  const untransformedBottom = rect.bottom + liftY.value
  const target = untransformedBottom - (window.innerHeight - kb) + 24
  liftY.value = target > 0 ? Math.ceil(target) : 0
}
onKeyboardDidShow(() => setTimeout(recomputeLift, 40))
onKeyboardWillHide(() => { liftY.value = 0 })
function _onFocusIn() { setTimeout(recomputeLift, 60) }
onMounted(() => document.addEventListener('focusin', _onFocusIn))
onBeforeUnmount(() => document.removeEventListener('focusin', _onFocusIn))

const router = useRouter()
const auth = useAuthStore()
const { t } = useI18n()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const userFocused = ref(false)
const pwdFocused = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = t('auth.needAccountPwd')
    return
  }
  loading.value = true
  error.value = ''
  try {
    // 智能并行登: 自动同时试 CN + SG, 两边都成功就两份 token 都缓存
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    if (e.code === 'ERR_NETWORK' || e.message === 'Network Error') {
      error.value = t('auth.netErr')
    } else if (e.code === 'ECONNABORTED') {
      error.value = t('auth.timeoutErr')
    } else if (e.response?.status === 401) {
      error.value = t('auth.badCred')
    } else {
      error.value = e.response?.data?.message || `${t('auth.genericErrPrefix')}: ${e.message}`
    }
  } finally {
    loading.value = false
  }
}

// 装饰用散落像素（splash-login.jsx ScatteredPixels line 317-342）
const SCATTERED = [
  { r: 0, c: 0, t: 'b', d: 0.18 }, { r: 0, c: 2, t: 'b', d: 0.10 },
  { r: 1, c: 1, t: 'd', d: 0.14 }, { r: 1, c: 3, t: 'b', d: 0.08 },
  { r: 2, c: 0, t: 'b', d: 0.06 }, { r: 2, c: 4, t: 'd', d: 0.18 },
  { r: 3, c: 2, t: 'b', d: 0.04 },
]
const SCATTER_COLOR = { b: '#4D82E0', d: '#2F66D6' }
const SCATTER_SIZE = 14
const SCATTER_GAP = 6
</script>

<template>
  <div class="login-root safe-top"
    :style="{
      transform: liftY ? `translateY(-${liftY}px)` : 'none',
      transition: 'transform 0.28s cubic-bezier(.25,.46,.45,.94)',
    }">
    <!-- 装饰用散落像素 (上右角) -->
    <div class="scattered-pixels">
      <div v-for="(p, i) in SCATTERED" :key="i"
        :style="{
          position: 'absolute',
          left:  (p.c * (SCATTER_SIZE + SCATTER_GAP)) + 'px',
          top:   (p.r * (SCATTER_SIZE + SCATTER_GAP)) + 'px',
          width:  SCATTER_SIZE + 'px',
          height: SCATTER_SIZE + 'px',
          background: SCATTER_COLOR[p.t],
          borderRadius: '3px',
          opacity: p.d,
        }" />
    </div>

    <!-- Hero: 像素 P + PMA + 副标 -->
    <div class="login-hero">
      <PixelP :size="68" />
      <div class="login-title">PMA</div>
      <div class="login-subtitle">{{ t('auth.subtitle') }}</div>
    </div>

    <!-- 表单 -->
    <div class="login-form">
      <div class="form-section-label">{{ t('auth.sectionLogin') }}</div>

      <!-- 账号 -->
      <div class="form-group">
        <label class="form-label">{{ t('auth.fAccount') }}</label>
        <div class="form-input" :class="{ focused: userFocused }">
          <svg class="form-icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="9" cy="6" r="3" :stroke="userFocused ? '#4D82E0' : '#7A7570'" stroke-width="1.4" />
            <path d="M3 16c0-3.3 2.7-6 6-6s6 2.7 6 6"
              :stroke="userFocused ? '#4D82E0' : '#7A7570'" stroke-width="1.4" stroke-linecap="round" />
          </svg>
          <input v-model="username" type="text" autocomplete="username"
            :placeholder="t('auth.fAccountPh')"
            @focus="userFocused = true" @blur="userFocused = false"
            @keyup.enter="handleLogin"
            class="form-input-text" />
        </div>
      </div>

      <!-- 密码 -->
      <div class="form-group">
        <div class="form-label-row">
          <label class="form-label">{{ t('auth.fPassword') }}</label>
          <span class="form-forgot">{{ t('auth.forgot') }}</span>
        </div>
        <div class="form-input" :class="{ focused: pwdFocused }">
          <svg class="form-icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
            <rect x="4" y="8" width="10" height="7" rx="1.5"
              :stroke="pwdFocused ? '#4D82E0' : '#7A7570'" stroke-width="1.4" />
            <path d="M6 8V6a3 3 0 016 0v2"
              :stroke="pwdFocused ? '#4D82E0' : '#7A7570'" stroke-width="1.4" />
          </svg>
          <input v-model="password" type="password" autocomplete="current-password"
            :placeholder="t('auth.fPasswordPh')"
            @focus="pwdFocused = true" @blur="pwdFocused = false"
            @keyup.enter="handleLogin"
            class="form-input-text" />
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="form-error">{{ error }}</div>

      <!-- 登录按钮 -->
      <button @click="handleLogin" :disabled="loading" class="login-button">
        {{ loading ? t('auth.loggingIn') : t('auth.login') }}
        <span class="login-button-dot" />
      </button>
    </div>

    <!-- 公司归属：用真 logo 图 (设计包 assets/evertac-logo.png) -->
    <div class="login-attribution">
      <div class="attr-label">{{ t('auth.attrBy') }}</div>
      <img :src="isSG ? '/images/evertac-solutions-logo.png' : '/images/evertac-logo.png'"
        :alt="t('auth.attrAlt')" class="attr-logo" />
      <div class="attr-italic">{{ t('auth.attrFooter') }}</div>
    </div>
  </div>
</template>

<style scoped>
.login-root {
  width: 100%;
  height: 100%;
  background: var(--color-bg);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  font-family: var(--font-sans);
  color: var(--color-ink);
}

.scattered-pixels {
  position: absolute;
  top: 90px; right: 24px;
  pointer-events: none;
  width: 80px; height: 80px;
}

.login-hero {
  /* 顶部留白：刘海下 ~80px，整体比设计稿再下移一点 */
  padding: 80px 32px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.login-title {
  font-family: var(--font-serif);
  font-size: 38px;
  font-weight: 500;
  color: var(--color-ink);
  letter-spacing: -0.5px;
  line-height: 1.05;
  margin-top: 22px;
  font-variant-numeric: oldstyle-nums;
}
.login-subtitle {
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 400;
  font-style: italic;
  color: var(--color-ink-3);
  margin-top: 8px;
  line-height: 1.3;
  text-align: center;
}

.login-form {
  padding: 44px 32px 0;
  flex: 1;
}
.form-section-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-ink-3);
  letter-spacing: 1.2px;
  text-transform: uppercase;
  margin-bottom: 14px;
}
.form-group { margin-bottom: 18px; }
.form-label-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}
.form-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-ink-3);
  letter-spacing: 0.6px;
  display: block;
  margin-bottom: 8px;
}
.form-label-row .form-label { margin-bottom: 0; }
.form-forgot {
  font-size: 12px;
  color: #4D82E0;
  font-weight: 500;
}
.form-input {
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid var(--color-divider-strong);
  padding: 8px 0 12px;
  transition: border-color 0.2s;
}
.form-input.focused {
  border-bottom: 1.5px solid #4D82E0;
}
.form-icon { flex-shrink: 0; }
.form-input-text {
  flex: 1;
  font-family: var(--font-serif);
  font-size: 19px;
  font-weight: 500;
  color: var(--color-ink);
  background: transparent;
  border: none;
  outline: none;
  font-variant-numeric: oldstyle-nums;
}
.form-input-text::placeholder {
  color: var(--color-ink-3);
  font-style: italic;
  font-weight: 400;
}

.form-error {
  font-family: var(--font-serif);
  font-size: 13px;
  color: #A04848;
  font-style: italic;
  margin: 8px 0 16px;
  text-align: center;
}

.login-button {
  width: 100%;
  height: 54px;
  border-radius: 14px;
  background: var(--color-ink);
  color: #fff;
  border: none;
  font-size: 15px;
  font-weight: 600;
  font-family: var(--font-sans);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  letter-spacing: 0.5px;
  box-shadow: 0 6px 20px rgba(26, 26, 26, 0.18);
  cursor: pointer;
  margin-top: 10px;
  transition: opacity 0.2s;
}
.login-button:disabled {
  opacity: 0.5;
}
.login-button:active:not(:disabled) {
  opacity: 0.85;
}
.login-button-dot {
  width: 6px;
  height: 6px;
  background: #4D82E0;
  border-radius: 1px;
  display: inline-block;
}

.login-attribution {
  padding: 0 32px 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.attr-label {
  font-size: 10px;
  color: var(--color-ink-3);
  letter-spacing: 2px;
  text-transform: uppercase;
  font-weight: 500;
}
.attr-logo {
  height: 36px;
  width: auto;
  opacity: 0.85;
}
.attr-italic {
  font-size: 10px;
  color: var(--color-ink-4);
  margin-top: 2px;
  font-family: var(--font-serif);
  font-style: italic;
}
</style>
