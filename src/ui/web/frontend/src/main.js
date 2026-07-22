import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import i18n, { initI18n } from './i18n'
import App from './App.vue'
import 'virtual:uno.css'
import '@unocss/reset/tailwind.css'
import './style.css'

import { initClient } from './api/client'
import { initPlugins } from './plugins/init'
import { installEdition } from '@edition'

window.addEventListener('vite:preloadError', () => {
  const reloadKey = 'flyto-chunk-reload'
  if (!sessionStorage.getItem(reloadKey)) {
    sessionStorage.setItem(reloadKey, '1')
    window.location.reload()
  }
})

function tagPlatform() {
  const ua = navigator.userAgentData?.platform || navigator.userAgent || ''
  const cls = /win/i.test(ua) ? 'is-windows' : /mac/i.test(ua) ? 'is-mac' : /linux/i.test(ua) ? 'is-linux' : 'is-other'
  document.documentElement.classList.add(cls)
}

async function bootstrap() {
  tagPlatform()
  await initClient()
  await initI18n()
  await initPlugins()

  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.use(router)
  app.use(i18n)
  await installEdition({ app, pinia, router })
  app.mount('#app')
}

bootstrap()
