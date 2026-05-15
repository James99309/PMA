<script setup>
// 启动动画 —— 严格对齐 splash-login.jsx AnimatedSplash
// 18 格 50ms 间隔 pop-in (~900ms) → 文字 fade up (1.1s 起) → 公司归属 fade in (1.5s 起)
// 共 ~2s 完成动画后，根据登录态跳转 /login 或 /
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import PixelP from '@/components/common/PixelP.vue'

const router = useRouter()
const auth = useAuthStore()

onMounted(() => {
  // 动画总时长约 2s，再多停 200ms 让用户看清最终态
  setTimeout(() => {
    router.replace(auth.isLoggedIn ? '/' : '/login')
  }, 2200)
})
</script>

<template>
  <div class="splash-root">
    <!-- 背景 vignette（径向蓝晕，对齐 jsx line 108-111） -->
    <div class="splash-vignette" />

    <!-- 像素 P 落格动画 -->
    <PixelP :size="196" state="splash" />

    <!-- PMA 字标 + Project Management（jsx line 362-370） -->
    <div class="splash-wordmark">
      <div class="wordmark-pma">PMA</div>
      <div class="wordmark-sub">Project Management</div>
    </div>

    <!-- 公司归属（jsx line 372-378） —— 真 logo 图 -->
    <div class="splash-footer">
      <div class="footer-label">Powered by</div>
      <img src="/images/evertac-logo.png" alt="Evertac" class="footer-logo" />
    </div>
  </div>
</template>

<style scoped>
.splash-root {
  width: 100%;
  height: 100%;
  background: #FFFFFF;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  font-family: var(--font-sans);
  color: var(--color-ink);
}

.splash-vignette {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 70% 50% at 50% 40%, rgba(77, 130, 224, 0.07), transparent 70%);
  pointer-events: none;
}

.splash-wordmark {
  text-align: center;
  margin-top: 40px;
  opacity: 0;
  transform: translateY(8px);
  animation: fadeUp 600ms ease-out 1100ms forwards;
}
.wordmark-pma {
  font-family: var(--font-serif);
  font-size: 30px;
  font-weight: 500;
  letter-spacing: 1px;
  color: var(--color-ink);
  font-variant-numeric: oldstyle-nums;
}
.wordmark-sub {
  font-size: 12px;
  color: var(--color-ink-3);
  margin-top: 6px;
  letter-spacing: 4px;
  text-transform: uppercase;
  font-weight: 500;
}

.splash-footer {
  position: absolute;
  bottom: calc(60px + env(safe-area-inset-bottom));
  left: 0; right: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  opacity: 0;
  animation: fadeIn 500ms ease-out 1500ms forwards;
}
.footer-label {
  font-size: 10px;
  color: var(--color-ink-3);
  opacity: 0.55;
  letter-spacing: 2px;
  text-transform: uppercase;
  font-weight: 500;
}
.footer-logo {
  height: 32px;
  width: auto;
  opacity: 0.85;
}

@keyframes fadeUp { to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { to { opacity: 1; } }
</style>
