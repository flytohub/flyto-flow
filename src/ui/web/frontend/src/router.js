import { createRouter, createWebHistory } from 'vue-router'
import { routes as editionRoutes, routeGuard as editionRouteGuard } from '@edition'
import NotFound from './views/NotFound.vue'

const routes = [
  { path: '/', redirect: '/my-templates' },
  { path: '/my-templates', component: () => import('./views/MyTemplates.vue') },
  { path: '/templates/:id', redirect: to => `/templates/builder/${to.params.id}` },
  { path: '/templates/builder', component: () => import('./views/TemplateBuilder.vue') },
  { path: '/templates/builder/:id', component: () => import('./views/TemplateBuilder.vue') },
  { path: '/templates/runner/:id', redirect: to => `/templates/builder/${to.params.id}` },
  { path: '/executions/:id', component: () => import('./views/ExecutionDetail.vue') },
  { path: '/mcp', component: () => import('./views/MCPStudio.vue') },
  { path: '/variables', component: () => import('./views/Variables.vue') },
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
  ...editionRoutes,
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFound, meta: { public: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0, left: 0 })
})

router.beforeEach(async to => {
  if (to.meta.public) return true
  return editionRouteGuard(to)
})

export default router
