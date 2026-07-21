<template>
  <div class="min-h-screen bg-white dark:bg-gray-900">
    <!-- Hero Section -->
    <section class="relative min-h-screen flex items-center overflow-hidden bg-gradient-to-b from-gray-50 to-white dark:(from-gray-800 to-gray-900)">
      <canvas ref="particlesCanvas" class="absolute inset-0 z-0" aria-hidden="true"></canvas>

      <div class="container relative z-10 py-20">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          <div class="space-y-8 text-center lg:text-left px-4">
            <HeroBadge :text="$t('home.aiPlatformBadge')" :icon="Sparkles" />

            <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight">
              <span class="gradient-text">{{ displayText }}</span>
              <span class="cursor text-primary-600">|</span>
            </h1>

            <p class="text-lg sm:text-xl text-gray-600 leading-relaxed max-w-2xl mx-auto lg:mx-0 dark:text-gray-300">
              {{ $t('home.heroSubtitle') }}<br class="hidden sm:inline"/>
              {{ $t('home.heroSubtitle2') }}
            </p>

            <div class="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <button @click="goWorkflows" class="btn-primary btn-lg group">
                <Zap :size="20" />
                {{ $t('home.getStarted') }}
                <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-500"></div>
              </button>
              <button @click="goMarketplace" class="btn-secondary btn-lg">
                <Package :size="20" />
                {{ $t('home.exploreApps') }}
              </button>
            </div>

            <div class="grid grid-cols-3 gap-6 pt-8 border-t border-gray-200 dark:border-gray-700">
              <div v-for="(stat, i) in heroStats" :key="i" class="text-center lg:text-left">
                <div class="text-2xl sm:text-3xl font-bold gradient-text">{{ stat.value }}</div>
                <div class="text-xs sm:text-sm mt-1 text-gray-500 dark:text-gray-400">{{ stat.label }}</div>
              </div>
            </div>
          </div>

          <div class="hidden lg:block px-4">
            <div class="relative w-full aspect-square bg-white border border-gray-200 rounded-2xl shadow-lg overflow-hidden dark:(bg-gray-800 border-gray-700)">
              <div class="network-visualization" ref="networkViz"></div>
            </div>
          </div>
        </div>

        <div class="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce text-gray-400 dark:text-gray-500">
          <ChevronDown :size="24" />
        </div>
      </div>

      <WaveDivider />
    </section>

    <!-- Features Section -->
    <section class="py-16 sm:py-20 lg:py-24 bg-gray-50 dark:bg-gray-800">
      <div class="container px-4">
        <div
          ref="featuresHeader"
          class="text-center mb-12 sm:mb-16 opacity-0 translate-y-8 transition-all duration-800"
        >
          <span class="inline-block px-4 py-2 bg-primary-50 text-primary-600 rounded-full text-sm font-semibold mb-4 dark:(bg-primary-900/30 text-primary-300)">{{ $t('home.featuresTitle') }}</span>
          <h2 class="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4 dark:text-gray-100">{{ $t('home.whyChoose') }}</h2>
          <p class="text-lg sm:text-xl text-gray-600 dark:text-gray-300">{{ $t('home.featuresPower') }}</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          <FeatureCard
            v-for="(feature, index) in features"
            :key="index"
            :ref="el => featureCards[index] = el"
            :title="feature.title"
            :description="feature.description"
            :icon="feature.icon"
            :gradient="feature.gradient"
            class="opacity-0 translate-y-8"
          />
        </div>
      </div>
    </section>

    <!-- Stats Section -->
    <section class="py-16 sm:py-20 lg:py-24 bg-white dark:bg-gray-900">
      <div class="container px-4">
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
          <StatCard
            v-for="(stat, i) in detailedStats"
            :key="i"
            :ref="el => statCards[i] = el"
            :icon="stat.icon"
            :number="stat.number"
            :label="stat.label"
            class="opacity-0 scale-90 transition-all duration-600"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Workflow, Zap, Package, Brain, DollarSign, Shield,
  Sparkles, ChevronDown, Users, TrendingUp, CheckCircle
} from 'lucide-vue-next'
import { useTypingEffect } from '@/composables/useTypingEffect'
import { useParticles } from '@/composables/useParticles'
import { useNetworkViz } from '@/composables/useNetworkViz'
import { useScrollAnimation } from '@/composables/useScrollAnimation'
import { DEFAULTS } from '@/config/defaults'
import WaveDivider from '@/components/home/WaveDivider.vue'
import HeroBadge from '@/components/home/HeroBadge.vue'
import FeatureCard from '@/components/home/FeatureCard.vue'
import StatCard from '@/components/home/StatCard.vue'

const router = useRouter()
const { t } = useI18n()

const particlesCanvas = ref(null)
const networkViz = ref(null)
const featuresHeader = ref(null)
const featureCards = ref([])
const statCards = ref([])

const typingTexts = computed(() => [
  t('home.heroTyping1'),
  t('home.heroTyping2'),
  t('home.heroTyping3')
])

const { displayText, start: startTyping } = useTypingEffect(typingTexts)
const { init: initParticles } = useParticles()
const { init: initNetworkViz } = useNetworkViz()
const { observe, animateIn } = useScrollAnimation()

const heroStats = computed(() => [
  { value: '1,000+', label: t('home.stat1Label') },
  { value: '500+', label: t('home.stat2Label') },
  { value: '200+', label: t('home.stat3Label') }
])

const features = computed(() => [
  {
    title: t('home.feature1Title'),
    description: t('home.feature1Desc'),
    icon: Workflow,
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  },
  {
    title: t('home.feature2Title'),
    description: t('home.feature2Desc'),
    icon: Zap,
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
  },
  {
    title: t('home.feature3Title'),
    description: t('home.feature3Desc'),
    icon: Package,
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
  },
  {
    title: t('home.feature4Title'),
    description: t('home.feature4Desc'),
    icon: Brain,
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
  },
  {
    title: t('home.feature5Title'),
    description: t('home.feature5Desc'),
    icon: DollarSign,
    gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
  },
  {
    title: t('home.feature6Title'),
    description: t('home.feature6Desc'),
    icon: Shield,
    gradient: 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)'
  }
])

const detailedStats = computed(() => [
  { icon: Users, number: DEFAULTS.HOME_STATS.ACTIVE_USERS, label: t('home.statActiveUsers') },
  { icon: Workflow, number: DEFAULTS.HOME_STATS.WORKFLOWS_CREATED, label: t('home.statWorkflows') },
  { icon: TrendingUp, number: DEFAULTS.HOME_STATS.SUCCESS_RATE, label: t('home.statSuccessRate') },
  { icon: CheckCircle, number: DEFAULTS.HOME_STATS.TOTAL_EXECUTIONS, label: t('home.statExecutions') }
])

function goMarketplace() {
  router.push('/marketplace')
}

function goWorkflows() {
  router.push('/workflows')
}

const timers = []

onMounted(() => {
  timers.push(setTimeout(startTyping, DEFAULTS.TIMING.TYPING_DELAY))
  timers.push(setTimeout(() => initParticles(particlesCanvas.value), DEFAULTS.TIMING.ANIMATION_INIT))

  if (window.matchMedia('(min-width: 1024px)').matches) {
    timers.push(setTimeout(() => initNetworkViz(networkViz.value), DEFAULTS.TIMING.ANIMATION_DURATION))
  }

  timers.push(setTimeout(() => {
    observe(featuresHeader.value, animateIn)
    observe(featureCards.value.map(fc => fc?.$el || fc).filter(Boolean), animateIn)
    observe(statCards.value.map(sc => sc?.$el || sc).filter(Boolean), animateIn)
  }, DEFAULTS.TIMING.DEBOUNCE_DELAY))
})

onUnmounted(() => {
  timers.forEach(clearTimeout)
})
</script>

<style scoped>
.network-visualization {
  position: relative;
  width: 100%;
  height: 100%;
}
</style>
