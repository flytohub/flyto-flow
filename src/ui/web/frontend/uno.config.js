import { defineConfig, presetUno, transformerDirectives, transformerVariantGroup } from 'unocss'

export default defineConfig({
  // Ensure all Vue files are scanned for utility classes
  content: {
    filesystem: [
      './src/**/*.{vue,js,ts,jsx,tsx,html}'
    ]
  },
  // Use UnoCSS built-in preflight (reset) - ensures correct CSS ordering
  preflights: [
    {
      getCSS: () => `
        *, *::before, *::after {
          box-sizing: border-box;
          border-width: 0;
          border-style: solid;
        }
        html {
          line-height: 1.5;
          -webkit-text-size-adjust: 100%;
          tab-size: 4;
        }
        body {
          margin: 0;
          line-height: inherit;
        }
        input, button, textarea, select {
          font: inherit;
          color: inherit;
        }
        button {
          background-color: transparent;
          background-image: none;
        }
        img, video {
          max-width: 100%;
          height: auto;
        }
      `,
      layer: 'preflights'
    }
  ],
  presets: [
    presetUno({
      dark: 'class' // Enable class-based dark mode
    })
  ],
  transformers: [
    transformerDirectives(),
    transformerVariantGroup()
  ],
  theme: {
    colors: {
      primary: {
        50: '#f0f4ff',
        100: '#e0eaff',
        200: '#c7d7fe',
        300: '#a5b8fc',
        400: '#818cf8',
        500: '#6366f1',
        600: '#4f46e5',
        700: '#4338ca',
        800: '#3730a3',
        900: '#312e81'
      },
      purple: {
        50: '#faf5ff',
        100: '#f3e8ff',
        200: '#e9d5ff',
        300: '#d8b4fe',
        400: '#c084fc',
        500: '#a855f7',
        600: '#9333ea',
        700: '#7e22ce',
        800: '#6b21a8',
        900: '#581c87'
      }
    }
  },
  shortcuts: {
    // Buttons
    'btn': 'inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer border-none outline-none',
    'btn-primary': 'btn relative bg-gradient-to-r from-primary-600 to-purple-600 text-white hover:shadow-lg overflow-hidden',
    'btn-secondary': 'btn bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-primary-300',
    'btn-lg': 'px-6 py-3 text-base',

    // Cards
    'card': 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-1',

    // Inputs
    'input': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg text-base transition-all duration-200 focus:outline-none focus:border-primary-500 focus:ring-3 focus:ring-primary-100 dark:focus:ring-primary-900',

    // Layout
    'container': 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8',

    // Text
    'gradient-text': 'bg-gradient-to-r from-primary-500 via-purple-500 to-pink-500 bg-clip-text text-transparent',

    // Cursor
    'cursor': 'inline-block animate-pulse'
  },
  safelist: [
    // Animation/transition
    'duration-600',
    'duration-800',
    'translate-y-0',
    'translate-y-8',
    'scale-90',
    'scale-100',
    'opacity-0',
    'opacity-100',
    // Layout essentials
    'flex',
    'flex-col',
    'flex-row',
    'flex-1',
    'items-center',
    'justify-center',
    'justify-between',
    'gap-1',
    'gap-2',
    'gap-3',
    'gap-4',
    // Common widths
    'w-full',
    'w-auto',
    'min-h-screen',
    // Text
    'text-sm',
    'text-base',
    'text-lg',
    'font-medium',
    'font-semibold',
    // Spacing
    'px-2',
    'px-3',
    'px-4',
    'py-2',
    'py-3',
    // Colors - IMPORTANT: These must be in safelist for Tauri builds
    'text-gray-100',
    'text-gray-900',
    'text-white',
    'bg-white',
    'bg-gray-800',
    'bg-gray-900',
    'dark:bg-gray-900',
    'dark:bg-gray-800',
    'dark:text-gray-100',
    // Borders
    'rounded-lg',
    'rounded-xl',
    'border',
    'border-gray-200',
    // Transitions
    'transition-all',
    'transition-colors',
    'duration-200'
  ]
})
