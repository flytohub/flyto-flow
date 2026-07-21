<template>
  <div class="flex flex-wrap items-center gap-1.5">
    <!-- Existing reaction pills -->
    <button
      v-for="(users, type) in visibleReactions"
      :key="type"
      type="button"
      class="emoji-pill inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium transition-all duration-200 cursor-pointer select-none"
      :class="[
        isReactedBy(type)
          ? 'bg-purple-500/20 border border-purple-500/30 text-purple-400'
          : 'bg-gray-800/30 border border-white/5 text-gray-400 hover:border-white/10'
      ]"
      @click="handleToggle(type)"
    >
      <span
        :ref="(el) => { if (el) pillEmojiRefs[type] = el }"
        class="emoji-icon inline-block leading-none"
      >{{ EMOJI_MAP[type] }}</span>
      <span>{{ users.length }}</span>
    </button>

    <!-- Add reaction button -->
    <div class="relative" ref="popoverAnchor">
      <button
        type="button"
        class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-800/30 border border-white/5 text-gray-500 hover:(border-white/10 text-gray-400) transition-all duration-200 cursor-pointer text-xs leading-none"
        aria-label="Add reaction"
        @mouseenter="showPopover = true"
        @mouseleave="onLeaveAddButton"
      >
        +
      </button>

      <!-- Emoji picker popover -->
      <Transition name="popover">
        <div
          v-if="showPopover"
          class="absolute bottom-full left-0 mb-1.5 flex items-center gap-0.5 rounded-lg bg-gray-900 border border-white/10 px-1.5 py-1 shadow-lg shadow-black/40 z-50"
          @mouseenter="showPopover = true"
          @mouseleave="showPopover = false"
        >
          <button
            v-for="(emoji, type) in EMOJI_MAP"
            :key="type"
            type="button"
            class="emoji-option w-7 h-7 flex items-center justify-center rounded-md text-base cursor-pointer transition-all duration-150 hover:(bg-white/10 scale-110)"
            :class="{ 'bg-purple-500/20': isReactedBy(type) }"
            @click="handleToggle(type)"
          >
            {{ emoji }}
          </button>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, reactive, nextTick } from 'vue'

const EMOJI_MAP = {
  thumbs_up: '\uD83D\uDC4D',
  heart: '\u2764\uFE0F',
  tada: '\uD83C\uDF89',
  confused: '\uD83D\uDE15',
  eyes: '\uD83D\uDC40',
  rocket: '\uD83D\uDE80'
}

const props = defineProps({
  /**
   * Reactions object: { thumbs_up: ["uid1", "uid2"], heart: ["uid3"] }
   */
  reactions: {
    type: Object,
    default: () => ({})
  },
  /**
   * Current user's UID for highlighting their reactions
   */
  currentUserId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['toggle'])

const showPopover = ref(false)
const pillEmojiRefs = reactive({})

/** Only show reactions that have at least one user */
const visibleReactions = computed(() => {
  const result = {}
  for (const [type, users] of Object.entries(props.reactions)) {
    if (Array.isArray(users) && users.length > 0 && EMOJI_MAP[type]) {
      result[type] = users
    }
  }
  return result
})

function isReactedBy(type) {
  const users = props.reactions[type]
  return Array.isArray(users) && users.includes(props.currentUserId)
}

function handleToggle(type) {
  emit('toggle', type)

  // Trigger bounce animation on the pill emoji
  const el = pillEmojiRefs[type]
  if (el) {
    el.classList.remove('emoji-bounce')
    void el.offsetWidth
    el.classList.add('emoji-bounce')
  } else {
    // If toggling from popover and pill doesn't exist yet, animate after next render
    nextTick(() => {
      const newEl = pillEmojiRefs[type]
      if (newEl) {
        newEl.classList.add('emoji-bounce')
      }
    })
  }

  showPopover.value = false
}

function onLeaveAddButton(e) {
  // Keep popover open if mouse moves to the popover itself
  const related = e.relatedTarget
  if (related && related.closest?.('.absolute')) return
  showPopover.value = false
}
</script>

<style scoped>
/* Bounce animation on click */
@keyframes emoji-bounce {
  0% { transform: scale(1); }
  30% { transform: scale(1.2); }
  60% { transform: scale(0.95); }
  100% { transform: scale(1); }
}

.emoji-bounce {
  animation: emoji-bounce 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Popover transition */
.popover-enter-active {
  transition: all 0.15s ease-out;
}

.popover-leave-active {
  transition: all 0.1s ease-in;
}

.popover-enter-from,
.popover-leave-to {
  opacity: 0;
  transform: translateY(4px) scale(0.95);
}

.popover-enter-to,
.popover-leave-from {
  opacity: 1;
  transform: translateY(0) scale(1);
}
</style>
