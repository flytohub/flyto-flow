<template>
  <div :class="['chat-message', role]">
    <div class="message-avatar">
      <component :is="role === 'user' ? User : Bot" :size="16" />
    </div>
    <div class="message-wrapper">
      <div class="message-content" ref="contentRef">
        <!-- Rendered markdown content -->
        <div v-html="renderedContent" class="markdown-body"></div>

        <!-- Workflow Suggestions -->
        <div v-if="suggestions && suggestions.length > 0" class="suggestions-list">
          <div
            v-for="(suggestion, idx) in suggestions"
            :key="idx"
            class="suggestion-card"
          >
            <div class="suggestion-header">
              <span class="suggestion-name">{{ suggestion.name || 'Workflow' }}</span>
              <span class="suggestion-confidence">{{ Math.round((suggestion.confidence || 0) * 100) }}%</span>
            </div>
            <p class="suggestion-desc">{{ suggestion.description }}</p>
            <button
              v-if="suggestion.yaml_content"
              @click="$emit('apply-suggestion', suggestion)"
              class="apply-btn"
              aria-label="Apply suggestion"
            >
              {{ $t('common.apply') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Message Actions -->
      <div class="message-actions" v-if="role === 'bot'">
        <button @click="copyMessage" class="action-btn" :title="$t('common.copy')">
          <component :is="copied ? Check : Copy" :size="14" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { Bot, User, Copy, Check } from 'lucide-vue-next'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

// Lazy-loaded highlight.js with language subset
let _hljs = null
async function getHljs() {
  if (_hljs) return _hljs
  const [
    { default: hljs },
    { default: javascript },
    { default: python },
    { default: yaml },
    { default: json },
    { default: xml },
    { default: css },
    { default: bash },
  ] = await Promise.all([
    import('highlight.js/lib/core'),
    import('highlight.js/lib/languages/javascript'),
    import('highlight.js/lib/languages/python'),
    import('highlight.js/lib/languages/yaml'),
    import('highlight.js/lib/languages/json'),
    import('highlight.js/lib/languages/xml'),
    import('highlight.js/lib/languages/css'),
    import('highlight.js/lib/languages/bash'),
  ])
  hljs.registerLanguage('javascript', javascript)
  hljs.registerLanguage('js', javascript)
  hljs.registerLanguage('python', python)
  hljs.registerLanguage('yaml', yaml)
  hljs.registerLanguage('yml', yaml)
  hljs.registerLanguage('json', json)
  hljs.registerLanguage('xml', xml)
  hljs.registerLanguage('html', xml)
  hljs.registerLanguage('css', css)
  hljs.registerLanguage('bash', bash)
  hljs.registerLanguage('shell', bash)
  _hljs = hljs
  return hljs
}

const props = defineProps({
  role: {
    type: String,
    required: true // 'user' | 'bot'
  },
  content: {
    type: String,
    default: ''
  },
  suggestions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['apply-suggestion'])

const { t } = useI18n()
const contentRef = ref(null)
const copied = ref(false)
const hljsReady = ref(false)

// Pre-load highlight.js on mount so it's ready for rendering
getHljs().then(() => { hljsReady.value = true })

// Configure marked
marked.setOptions({
  breaks: true,
  gfm: true
})

// Custom renderer for code blocks with copy button
// marked v17+: renderer.code receives { text, lang, escaped } object
const renderer = {
  code({ text, lang }) {
    const language = lang || ''
    const code = text || ''
    const langClass = language ? `language-${language}` : ''
    // Use pre-loaded hljs synchronously (already loaded on mount)
    const highlighted = _hljs && language && _hljs.getLanguage(language)
      ? _hljs.highlight(code, { language }).value
      : _hljs ? _hljs.highlightAuto(code).value
      : code
    const copyText = t('common.copy')
    const copiedText = t('common.copied')
    const copyCodeTitle = t('common.copyCode')

    // SECURITY: Removed onclick attribute - using event delegation instead
    return `
      <div class="code-block" data-lang="${language}">
        <div class="code-header">
          <span class="code-lang">${language || 'code'}</span>
          <div class="code-header-actions">
            <button class="code-copy-btn" title="${copyCodeTitle}" data-copy-text="${copyText}" data-copied-text="${copiedText}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>${copyText}</span>
            </button>
          </div>
        </div>
        <pre><code class="hljs ${langClass}">${highlighted}</code></pre>
      </div>
    `
  }
}

marked.use({ renderer })

const renderedContent = computed(() => {
  if (!props.content) return ''
  const html = marked(props.content)
  // SECURITY: Sanitize HTML to prevent XSS attacks
  // NOTE: onclick intentionally NOT allowed - use event delegation instead
  return DOMPurify.sanitize(html, {
    ADD_ATTR: ['data-copy-text', 'data-copied-text'],
    ADD_TAGS: ['button']
  })
})

async function copyMessage() {
  try {
    // Get plain text content
    const plainText = props.content
    await navigator.clipboard.writeText(plainText)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
  }
}

// SECURITY: Use event delegation instead of onclick attributes (XSS prevention)
onMounted(() => {
  if (contentRef.value) {
    contentRef.value.addEventListener('click', async (event) => {
      // Handle copy button click
      const button = event.target.closest('.code-copy-btn')
      if (!button) return

      const codeBlock = button.closest('.code-block')
      if (!codeBlock) return

      const code = codeBlock.querySelector('code')?.textContent || ''
      try {
        await navigator.clipboard.writeText(code)
        const span = button.querySelector('span')
        const copyText = button.getAttribute('data-copy-text') || 'Copy'
        const copiedText = button.getAttribute('data-copied-text') || 'Copied!'
        span.textContent = copiedText
        button.classList.add('copied')
        setTimeout(() => {
          span.textContent = copyText
          button.classList.remove('copied')
        }, 2000)
      } catch (err) {
        // Clipboard API may fail in some contexts
      }
    })
  }
})
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  max-width: 95%;
}

.chat-message.user {
  flex-direction: row-reverse;
  align-self: flex-end;
}

.chat-message.bot {
  align-self: flex-start;
}

.message-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-message.bot .message-avatar {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(6, 182, 212, 0.15) 100%);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #34d399;
}

.chat-message.user .message-avatar {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.15) 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #a78bfa;
}

.message-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  flex: 1;
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
}

.chat-message.bot .message-content {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
  border: 1px solid rgba(71, 85, 105, 0.4);
  color: #e2e8f0;
  border-top-left-radius: 4px;
}

.chat-message.user .message-content {
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  color: white;
  border-top-right-radius: 4px;
}

/* Message Actions */
.message-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.chat-message:hover .message-actions {
  opacity: 1;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: rgba(71, 85, 105, 0.3);
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
}

/* Markdown Styles */
.markdown-body :deep(p) {
  margin: 0 0 12px 0;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.markdown-body :deep(li) {
  margin: 4px 0;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin: 16px 0 8px 0;
  font-weight: 600;
  color: #f1f5f9;
}

.markdown-body :deep(h1) { font-size: 1.5em; }
.markdown-body :deep(h2) { font-size: 1.3em; }
.markdown-body :deep(h3) { font-size: 1.1em; }

.markdown-body :deep(strong) {
  font-weight: 600;
  color: #f1f5f9;
}

.markdown-body :deep(code:not(.hljs)) {
  padding: 2px 6px;
  background: rgba(139, 92, 246, 0.15);
  border-radius: 4px;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 0.9em;
  color: #a78bfa;
}

.markdown-body :deep(a) {
  color: #60a5fa;
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(blockquote) {
  margin: 12px 0;
  padding: 8px 16px;
  border-left: 3px solid #8B5CF6;
  background: rgba(139, 92, 246, 0.1);
  color: #cbd5e1;
}

/* Code Block */
.markdown-body :deep(.code-block) {
  margin: 12px 0;
  border-radius: 10px;
  overflow: hidden;
  background: #0d1117;
  border: 1px solid #30363d;
}

.markdown-body :deep(.code-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
}

.markdown-body :deep(.code-header-actions) {
  display: flex;
  align-items: center;
  gap: 6px;
}

.markdown-body :deep(.code-lang) {
  font-size: 12px;
  font-weight: 500;
  color: #8b949e;
  text-transform: lowercase;
}

.markdown-body :deep(.code-copy-btn) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: transparent;
  border: 1px solid #30363d;
  border-radius: 6px;
  color: #8b949e;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.markdown-body :deep(.code-copy-btn:hover) {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.4);
  color: #a78bfa;
}

.markdown-body :deep(.code-copy-btn.copied) {
  color: #34d399;
  border-color: rgba(16, 185, 129, 0.4);
}

.markdown-body :deep(pre) {
  margin: 0;
  padding: 16px;
  overflow-x: auto;
}

.markdown-body :deep(pre code) {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 13px;
  line-height: 1.5;
  background: transparent;
  padding: 0;
}

/* Suggestions */
.suggestions-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-card {
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 10px;
  padding: 12px;
  transition: all 0.2s ease;
}

.suggestion-card:hover {
  background: rgba(16, 185, 129, 0.12);
  border-color: rgba(16, 185, 129, 0.4);
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.suggestion-name {
  font-size: 13px;
  font-weight: 600;
  color: #10B981;
}

.suggestion-confidence {
  font-size: 11px;
  color: #94a3b8;
  background: rgba(148, 163, 184, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.suggestion-desc {
  font-size: 12px;
  color: #94a3b8;
  margin: 0 0 10px 0;
  line-height: 1.4;
}

.apply-btn {
  width: 100%;
  padding: 8px 12px;
  background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%);
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.apply-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}
</style>
