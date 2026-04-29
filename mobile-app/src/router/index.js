import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login', component: () => import('@/views/auth/LoginView.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/views/AppShell.vue'),
    children: [
      { path: '', redirect: '/projects' },
      { path: 'projects', component: () => import('@/views/projects/ProjectListView.vue') },
      { path: 'projects/:id', component: () => import('@/views/projects/ProjectDetailView.vue') },
      { path: 'approval', component: () => import('@/views/approval/ApprovalView.vue') },
      { path: 'customers', component: () => import('@/views/customers/CustomerListView.vue') },
      { path: 'customers/:id', component: () => import('@/views/customers/CustomerDetailView.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) return '/login'
})

export default router
