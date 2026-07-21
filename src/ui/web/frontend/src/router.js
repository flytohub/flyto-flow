import { createRouter, createWebHistory } from 'vue-router'
import { authAPI } from './api/auth'
import { useCapabilitiesStore } from './stores/capabilitiesStore'
import { useUserStore } from './stores/userStore'

import Login from './views/Login.vue'
import NotFound from './views/NotFound.vue'

const routes = [
  { path: '/', redirect: '/my-templates' },
  { path: '/login', component: Login, meta: { public: true } },
  { path: '/dashboard', redirect: '/my-templates' },
  { path: '/my-templates', component: () => import('./views/MyTemplates.vue') },
  { path: '/workflows', redirect: '/my-templates' },
  { path: '/templates/:id', component: () => import('./views/TemplateDetail.vue') },
  { path: '/templates/builder', component: () => import('./views/TemplateBuilder.vue') },
  { path: '/templates/builder/:id', component: () => import('./views/TemplateBuilder.vue') },
  { path: '/templates/runner/:id', redirect: to => `/templates/builder/${to.params.id}` },
  { path: '/executions/:id', component: () => import('./views/ExecutionDetail.vue') },
  { path: '/plugins', component: () => import('./views/PluginStore.vue') },
  { path: '/tools', component: () => import('./views/ToolLibrary.vue') },
  { path: '/tools/:id/run', component: () => import('./views/ToolRunner.vue') },
  { path: '/mcp', component: () => import('./views/MCPStatus.vue') },
  { path: '/variables', component: () => import('./views/Variables.vue') },
  { path: '/settings', component: () => import('./views/UserSettings.vue') },
  {
    path: '/observability',
    component: () => import('./views/observability/ObservabilityLayout.vue'),
    children: [
      { path: '', redirect: '/observability/metrics' },
      { path: 'metrics', component: () => import('./views/observability/MetricsDashboard.vue') },
      { path: 'traces', component: () => import('./views/observability/TraceViewer.vue') },
      { path: 'traces/:traceId', component: () => import('./views/observability/TraceViewer.vue') },
      { path: 'alerts', component: () => import('./views/observability/AlertManager.vue') }
    ]
  },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFound, meta: { public: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0, left: 0 })
})

router.beforeEach(async to => {
  if (to.meta.public) return true
  const userStore = useUserStore()
  if (!userStore.authInitialized) {
    try {
      await userStore.waitForAuth()
    } catch {
      return '/login'
    }
  }
  if (!authAPI.isLoggedIn()) return '/login'
  const capabilities = useCapabilitiesStore()
  if (!capabilities.isLoaded) {
    try {
      await capabilities.load()
    } catch {
      return '/login'
    }
  }
  return capabilities.canAccessPage(to.path) ? true : '/my-templates'
})

export default router
