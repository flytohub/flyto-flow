<template>
  <div class="flex-1 flex flex-col justify-center p-8 md:p-12 bg-gradient-to-br from-primary-500/10 to-purple-500/10 border-b md:border-b-0 md:border-r border-white/10">
    <div class="max-w-none text-center flex flex-col items-center md:max-w-[320px] md:text-left md:items-start">
      <LogoAnimated src="/logo.png" :alt="$t('alt.flytoLogo')" />
      <h1 class="text-[2.5rem] font-extrabold mb-2 flex justify-center md:justify-start">
        <span
          v-for="(letter, idx) in 'Flyto2'"
          :key="idx"
          class="title-letter"
          :style="{ animationDelay: `${idx * 0.1}s` }"
        >{{ letter }}</span>
      </h1>
      <p class="text-white/75 text-base leading-relaxed mb-8">{{ subtitle }}</p>

      <div class="hidden md:flex md:flex-col gap-4">
        <div
          v-for="(feature, idx) in features"
          :key="feature.key"
          class="feature-item flex items-center gap-3 text-white/90 text-[0.9rem]"
          :style="{ animationDelay: `${0.5 + idx * 0.15}s` }"
        >
          <div class="feature-icon w-9 h-9 bg-white/10 rounded-[10px] flex items-center justify-center text-purple-500 transition-all duration-300">
            <component :is="feature.icon" :size="18" />
          </div>
          <span>{{ feature.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LogoAnimated from './LogoAnimated.vue'

defineProps({
  subtitle: {
    type: String,
    default: ''
  },
  features: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.title-letter {
  background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.7) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: letterBounce 0.6s ease-out both;
  display: inline-block;
}

@keyframes letterBounce {
  0% { opacity: 0; transform: translateY(-30px) scale(0.5); }
  60% { transform: translateY(5px) scale(1.1); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

.feature-item {
  animation: slideInLeft 0.5s ease-out both;
  opacity: 0;
}

@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-30px); }
  to { opacity: 1; transform: translateX(0); }
}

.feature-item:hover .feature-icon {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.3), rgba(99, 102, 241, 0.3));
  transform: scale(1.1) rotate(5deg);
  box-shadow: 0 0 20px rgba(168, 85, 247, 0.4);
}
</style>
