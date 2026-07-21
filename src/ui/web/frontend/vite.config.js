/// <reference types="vitest" />
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import path from 'path'
import fs from 'fs'
import obfuscatorPlugin from 'rollup-plugin-obfuscator'

// Read package.json for version (used in cache keys for i18n, etc.)
const pkg = JSON.parse(fs.readFileSync('./package.json', 'utf-8'))

const DEFAULT_API_PORT = 9000
const DEFAULT_FRONTEND_PORT = 3000

// 混淆配置 (生產環境用) - 平衡版：安全性 + 檔案大小
const obfuscatorOptions = {
  // 全局選項
  compact: true,
  simplify: true,

  // 控制流混淆 - 降低閾值減少體積
  controlFlowFlattening: true,
  controlFlowFlatteningThreshold: 0.5,  // 從 0.75 降到 0.5

  // 死程式碼注入 - 大幅降低，這是體積增加的主因
  deadCodeInjection: true,
  deadCodeInjectionThreshold: 0.1,  // 從 0.4 降到 0.1

  // 字串陣列加密 - 只用 base64，不用 rc4
  stringArray: true,
  stringArrayEncoding: ['base64'],  // 移除 rc4
  stringArrayThreshold: 0.5,  // 從 0.75 降到 0.5
  stringArrayIndexShift: true,
  stringArrayRotate: true,
  stringArrayShuffle: true,
  stringArrayWrappersCount: 1,  // 從 2 降到 1
  stringArrayWrappersChainedCalls: true,
  stringArrayWrappersType: 'function',

  // 識別符號混淆
  identifierNamesGenerator: 'hexadecimal',
  renameGlobals: false,

  // 數字混淆 - 關閉，減少體積
  numbersToExpressions: false,

  // 除錯保護 - 保留但不要 interval (避免效能問題)
  debugProtection: true,
  debugProtectionInterval: 0,  // 從 2000 改為 0

  // 禁用 console
  disableConsoleOutput: true,

  // 自我防護
  selfDefending: true,

  // Unicode 轉義 - 關閉，減少體積
  unicodeEscapeSequence: false,

  // 分割字串 - 關閉，減少體積
  splitStrings: false,

  // 轉換物件鍵
  transformObjectKeys: true,

  // 保留名稱
  reservedNames: [
    '^__vue',
    '^__VUE',
    '^vue',
    '^Vue',
    '^pinia',
    '^Pinia',
    '^router',
    '^Router'
  ],

  ignoreImports: true
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const isProduction = mode === 'production'
  const sentryEnabled = false

  // Use 127.0.0.1 instead of localhost to ensure IPv4 (backend only listens on IPv4)
  const apiHost = env.VITE_API_HOST || '127.0.0.1'
  const apiPort = env.VITE_API_PORT || DEFAULT_API_PORT
  const apiTarget = env.VITE_API_URL || `http://${apiHost}:${apiPort}`

  // 基本插件
  const plugins = [
    vue(),
    UnoCSS()
  ]

  // Obfuscation is opt-in. The default release build must stay debuggable
  // enough for browser smoke and must not ship self-defending code that can
  // break SPA boot in Chromium/WebView runtimes.
  const enableObfuscation = isProduction && process.env.ENABLE_OBFUSCATION === '1'
  if (enableObfuscation) {
    plugins.push(
      obfuscatorPlugin({
        global: true,
        options: obfuscatorOptions,
        include: ['**/*.js', '**/*.ts', '**/*.vue'],
        exclude: ['node_modules/**']
      })
    )
  }

  return {
    base: '/',
    plugins,
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src')
      }
    },
    server: {
      port: parseInt(env.VITE_FRONTEND_PORT || DEFAULT_FRONTEND_PORT, 10),
      // Allow external hostnames (e.g. local.flyto2.com) to connect
      host: true,
      allowedHosts: ['local.flyto2.com'],
      // Local HTTPS via mkcert (enables https://local.flyto2.com)
      https: fs.existsSync('./local.flyto2.com+2.pem') ? {
        cert: fs.readFileSync('./local.flyto2.com+2.pem'),
        key: fs.readFileSync('./local.flyto2.com+2-key.pem'),
      } : undefined,
      // Relax COOP for Google OAuth popup compatibility
      headers: {
        'Cross-Origin-Opener-Policy': 'same-origin-allow-popups',
      },
      // HMR 穩定性優化
      hmr: {
        overlay: true,
        // 增加超時時間避免斷線
        timeout: 5000,
      },
      // 文件監聽優化
      watch: {
        // 使用 polling 在某些系統上更穩定 (如 Docker, WSL)
        usePolling: false,
        // 排除不需要監聽的目錄
        ignored: [
          '**/node_modules/**',
          '**/.git/**',
          '**/dist/**',
          '**/__pycache__/**',
          '**/*.pyc',
          '**/coverage/**',
        ],
      },
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          ws: true,  // Enable WebSocket for /api/v1/collaboration/ws/*
          // 增加 timeout 避免後端重載時卡住
          timeout: 30000,  // 30 seconds
          proxyTimeout: 30000,
          // 當後端不可用時返回 503 而不是卡住
          configure: (proxy) => {
            proxy.on('error', (err, req, res) => {
              console.warn('[Proxy] API error:', err.message)
              if (res.writeHead && !res.headersSent) {
                res.writeHead(503, { 'Content-Type': 'application/json' })
                res.end(JSON.stringify({ ok: false, error: 'Backend unavailable, please retry' }))
              }
            })
          }
        },
        '/ws': {
          target: apiTarget,
          ws: true,
          timeout: 30000
        }
      }
    },
    build: {
      target: 'esnext',
      minify: 'esbuild',
      // 生產環境移除 console 和 debugger
      esbuild: isProduction ? {
        drop: ['console', 'debugger'],
      } : {},
      // Source maps - enable 'hidden' when Sentry is configured (uploaded to Sentry, not served)
      // 'hidden' generates maps but doesn't add sourceMappingURL comments
      sourcemap: sentryEnabled ? 'hidden' : false,
      // 程式碼分割
      // Monaco editor core is a deliberately lazy-loaded editor dependency.
      // release:bundle-budget enforces a tighter gzip budget and verifies it is
      // not modulepreloaded on the initial HTML response.
      chunkSizeWarningLimit: 2600,
      modulePreload: {
        resolveDependencies: (_url, deps) => {
          // The code editor is only used on builder code params. Avoid pulling
          // the editor core into first-load preloads; dynamic import will fetch
          // it when the component actually mounts.
          return deps.filter((dep) => !dep.includes('vendor-monaco-'))
        }
      },
      rollupOptions: {
        // Suppress "dynamically imported by X but also statically imported" warning
        // This happens with telemetry.js due to circular dependency breaking via dynamic import
        onwarn(warning, warn) {
          if (warning.code === 'PLUGIN_WARNING' &&
              warning.plugin === 'vite:reporter' &&
              warning.message?.includes('dynamically imported by') &&
              warning.message?.includes('also statically imported')) {
            return // suppress
          }
          warn(warning)
        },
        output: {
          // 混淆檔案名
          entryFileNames: 'assets/[hash].js',
          chunkFileNames: (chunkInfo) => {
            if (chunkInfo.name?.startsWith('vendor-monaco')) {
              return 'assets/vendor-monaco-[hash].js'
            }
            return 'assets/[hash].js'
          },
          assetFileNames: 'assets/[hash].[ext]',
          manualChunks: (id) => {
            if (id.includes('/src/i18n/bundled/')) {
              if (id.endsWith('/en.json')) return 'i18n-baseline-en'
              if (id.endsWith('/zh-TW.json')) return 'i18n-baseline-zh-tw'
              if (id.endsWith('/zh-CN.json')) return 'i18n-baseline-zh-cn'
              return 'i18n-baseline'
            }

            if (!id.includes('node_modules')) return

            // Vue Flow must be checked before generic "vue" because package
            // names contain vue and otherwise collapse into the core Vue chunk.
            if (id.includes('@vue-flow')) {
              return 'vendor-flow'
            }
            // Highlight.js
            if (id.includes('highlight.js')) {
              return 'vendor-highlight'
            }
            // Icons must be checked before generic "vue" for lucide-vue-next.
            if (id.includes('lucide') || id.includes('@iconify')) {
              return 'vendor-icons'
            }
            // Vue ecosystem
            if (id.includes('vue') || id.includes('@vue') ||
                id.includes('pinia') || id.includes('vue-router')) {
              return 'vendor-vue'
            }
            // Monaco Editor
            if (id.includes('monaco-editor')) {
              return 'vendor-monaco'
            }
            // i18n
            if (id.includes('vue-i18n') || id.includes('@intlify')) {
              return 'vendor-i18n'
            }
            // Other vendor libs
            if (id.includes('node_modules')) {
              return 'vendor-libs'
            }
          }
        }
      }
    },
    optimizeDeps: {
      esbuildOptions: {
        target: 'esnext'
      }
    },
    // 定義環境變數替換
    define: {
      // App version for cache invalidation (i18n, etc.)
      'import.meta.env.VITE_APP_VERSION': JSON.stringify(pkg.version),
      // Vue production flags
      __VUE_PROD_DEVTOOLS__: false,
      __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false,
      __VUE_OPTIONS_API__: true,
      // Vue i18n flags (all required for production)
      __VUE_I18N_FULL_INSTALL__: true,
      __VUE_I18N_LEGACY_API__: false,
      __VUE_I18N_PROD_DEVTOOLS__: false,
      __INTLIFY_JIT_COMPILATION__: true,
      __INTLIFY_PROD_DEVTOOLS__: false,
      __INTLIFY_DROP_MESSAGE_COMPILER__: false
    },
    // Vitest configuration
    test: {
      globals: true,
      environment: 'happy-dom',
      setupFiles: ['./tests/setupStorage.js'],
      include: [
        'src/**/*.{test,spec}.{js,ts}',
        'src/**/__tests__/*.{test,spec}.{js,ts}',
        'tests/**/*.{test,spec}.{js,ts}'
      ],
      exclude: ['node_modules', 'dist']
    },
  }
})
