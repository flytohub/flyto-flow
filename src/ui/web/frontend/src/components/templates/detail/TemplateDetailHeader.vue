<template>
  <header class="sticky top-0 z-20 backdrop-blur-xl bg-gray-900/70 border-b border-white/10">
    <div class="max-w-7xl mx-auto px-4 py-4">
      <div class="flex items-center justify-between">
        <!-- Left: Back & Breadcrumb -->
        <div class="flex items-center gap-4">
          <button
            @click="$emit('back')"
            aria-label="Back"
            class="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-xl transition-all"
          >
            <ArrowLeft :size="20" />
          </button>
          <nav class="hidden md:flex items-center gap-2 text-sm text-gray-400">
            <router-link to="/marketplace" class="hover:text-purple-400 transition-colors">
              {{ $t('nav.marketplace') }}
            </router-link>
            <ChevronRight :size="14" />
            <span v-if="categoryName" class="hover:text-purple-400">{{ categoryName }}</span>
            <ChevronRight v-if="categoryName" :size="14" />
            <span class="text-white font-medium">{{ templateName }}</span>
          </nav>
        </div>

        <!-- Right: Actions -->
        <div class="flex items-center gap-3">
          <button
            @click="$emit('share')"
            aria-label="Share"
            class="p-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 hover:text-white rounded-xl transition-all"
            :title="$t('common.share')"
          >
            <Share2 :size="18" />
          </button>

          <!-- Export YAML (owner only) -->
          <button
            v-if="isOwnTemplate"
            @click="$emit('export-yaml')"
            aria-label="Export YAML"
            class="p-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 hover:text-white rounded-xl transition-all"
            title="Export YAML"
          >
            <FileDown :size="18" />
          </button>

          <!-- Own template: Edit button -->
          <button
            v-if="isOwnTemplate"
            @click="$emit('edit')"
            class="group relative px-5 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-medium rounded-xl transition-all hover:shadow-lg hover:shadow-blue-500/30 flex items-center gap-2 overflow-hidden"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-blue-400 to-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <span class="relative flex items-center gap-2">
              <Pencil :size="18" />
              {{ $t('common.edit') }}
            </span>
          </button>

          <!-- Installed template: Run button -->
          <button
            v-else-if="isInstalled"
            @click="$emit('run')"
            class="group relative px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-medium rounded-xl transition-all hover:shadow-lg hover:shadow-emerald-500/30 flex items-center gap-2 overflow-hidden"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-emerald-400 to-teal-400 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <span class="relative flex items-center gap-2">
              <Play :size="18" />
              {{ $t('templateDetail.run') }}
            </span>
          </button>

          <!-- Not installed: Install/Buy button -->
          <button
            v-else
            @click="$emit('install')"
            :disabled="installing || purchasing"
            class="group relative px-5 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium rounded-xl transition-all hover:shadow-lg hover:shadow-purple-500/30 flex items-center gap-2 disabled:opacity-50 overflow-hidden"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-purple-400 to-pink-400 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <span class="relative flex items-center gap-2">
              <Loader2 v-if="installing || purchasing" :size="18" class="animate-spin" />
              <ShoppingCart v-else-if="requiresPurchase" :size="18" />
              <Download v-else :size="18" />
              <template v-if="installing">{{ $t('templateDetail.installing') }}</template>
              <template v-else-if="purchasing">{{ $t('payment.processing') }}</template>
              <template v-else-if="requiresPurchase">{{ $t('payment.buyNow') }} - {{ formattedPrice }}</template>
              <template v-else>{{ $t('templateDetail.install') }}</template>
            </span>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import {
  ArrowLeft,
  ChevronRight,
  Share2,
  Pencil,
  Play,
  Download,
  ShoppingCart,
  Loader2,
  FileDown
} from 'lucide-vue-next'

defineProps({
  templateName: { type: String, default: '' },
  categoryName: { type: String, default: '' },
  isOwnTemplate: { type: Boolean, default: false },
  isInstalled: { type: Boolean, default: false },
  requiresPurchase: { type: Boolean, default: false },
  formattedPrice: { type: String, default: '' },
  installing: { type: Boolean, default: false },
  purchasing: { type: Boolean, default: false }
})

defineEmits(['back', 'share', 'edit', 'run', 'install', 'export-yaml'])
</script>
