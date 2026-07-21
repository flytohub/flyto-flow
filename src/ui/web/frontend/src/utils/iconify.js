/**
 * Iconify CDN Utility
 *
 * Generate icon URLs from Iconify CDN (200,000+ icons, including brand logos)
 * No bundle size impact - icons loaded from CDN with browser caching
 *
 * Icon sets:
 * - simple-icons: Brand logos (OpenAI, Anthropic, Google, etc.)
 * - lucide: General purpose icons
 * - mdi: Material Design Icons
 * - carbon: IBM Carbon icons
 *
 * @see https://iconify.design/
 */

const ICONIFY_CDN = 'https://api.iconify.design'

// Popular brand icons from Simple Icons
export const BRAND_ICONS = [
  { id: 'simple-icons:openai', name: 'OpenAI', color: '#412991' },
  { id: 'simple-icons:anthropic', name: 'Anthropic (Claude)', color: '#191919' },
  { id: 'simple-icons:google', name: 'Google', color: '#4285F4' },
  { id: 'simple-icons:microsoft', name: 'Microsoft', color: '#5E5E5E' },
  { id: 'simple-icons:amazon', name: 'Amazon', color: '#FF9900' },
  { id: 'simple-icons:github', name: 'GitHub', color: '#181717' },
  { id: 'simple-icons:gitlab', name: 'GitLab', color: '#FC6D26' },
  { id: 'simple-icons:slack', name: 'Slack', color: '#4A154B' },
  { id: 'simple-icons:discord', name: 'Discord', color: '#5865F2' },
  { id: 'simple-icons:telegram', name: 'Telegram', color: '#26A5E4' },
  { id: 'simple-icons:whatsapp', name: 'WhatsApp', color: '#25D366' },
  { id: 'simple-icons:notion', name: 'Notion', color: '#000000' },
  { id: 'simple-icons:airtable', name: 'Airtable', color: '#18BFFF' },
  { id: 'simple-icons:figma', name: 'Figma', color: '#F24E1E' },
  { id: 'simple-icons:stripe', name: 'Stripe', color: '#008CDD' },
  { id: 'simple-icons:shopify', name: 'Shopify', color: '#7AB55C' },
  { id: 'simple-icons:wordpress', name: 'WordPress', color: '#21759B' },
  { id: 'simple-icons:firebase', name: 'Firebase', color: '#FFCA28' },
  { id: 'simple-icons:supabase', name: 'Supabase', color: '#3FCF8E' },
  { id: 'simple-icons:mongodb', name: 'MongoDB', color: '#47A248' },
  { id: 'simple-icons:postgresql', name: 'PostgreSQL', color: '#4169E1' },
  { id: 'simple-icons:redis', name: 'Redis', color: '#DC382D' },
  { id: 'simple-icons:docker', name: 'Docker', color: '#2496ED' },
  { id: 'simple-icons:kubernetes', name: 'Kubernetes', color: '#326CE5' },
  { id: 'simple-icons:vercel', name: 'Vercel', color: '#000000' },
  { id: 'simple-icons:netlify', name: 'Netlify', color: '#00C7B7' },
  { id: 'simple-icons:cloudflare', name: 'Cloudflare', color: '#F38020' },
  { id: 'simple-icons:twilio', name: 'Twilio', color: '#F22F46' },
  { id: 'simple-icons:sendgrid', name: 'SendGrid', color: '#1A82E2' },
  { id: 'simple-icons:mailchimp', name: 'Mailchimp', color: '#FFE01B' },
  { id: 'simple-icons:hubspot', name: 'HubSpot', color: '#FF7A59' },
  { id: 'simple-icons:salesforce', name: 'Salesforce', color: '#00A1E0' },
  { id: 'simple-icons:zapier', name: 'Zapier', color: '#FF4A00' },
  { id: 'simple-icons:ifttt', name: 'IFTTT', color: '#000000' },
  { id: 'simple-icons:n8n', name: 'n8n', color: '#EA4B71' },
  { id: 'simple-icons:python', name: 'Python', color: '#3776AB' },
  { id: 'simple-icons:javascript', name: 'JavaScript', color: '#F7DF1E' },
  { id: 'simple-icons:typescript', name: 'TypeScript', color: '#3178C6' },
  { id: 'simple-icons:react', name: 'React', color: '#61DAFB' },
  { id: 'simple-icons:vuedotjs', name: 'Vue.js', color: '#4FC08D' },
  { id: 'simple-icons:nodedotjs', name: 'Node.js', color: '#339933' },
  { id: 'simple-icons:rust', name: 'Rust', color: '#000000' },
  { id: 'simple-icons:go', name: 'Go', color: '#00ADD8' },
  { id: 'simple-icons:amazonaws', name: 'AWS', color: '#232F3E' },
  { id: 'simple-icons:googlecloud', name: 'Google Cloud', color: '#4285F4' },
  { id: 'simple-icons:microsoftazure', name: 'Azure', color: '#0078D4' },
  { id: 'simple-icons:huggingface', name: 'Hugging Face', color: '#FFD21E' },
  { id: 'simple-icons:ollama', name: 'Ollama', color: '#000000' },
  { id: 'simple-icons:meta', name: 'Meta', color: '#0081FB' },
  { id: 'simple-icons:x', name: 'X (Twitter)', color: '#000000' },
  { id: 'simple-icons:linkedin', name: 'LinkedIn', color: '#0A66C2' },
  { id: 'simple-icons:youtube', name: 'YouTube', color: '#FF0000' },
  { id: 'simple-icons:spotify', name: 'Spotify', color: '#1DB954' },
  { id: 'simple-icons:dropbox', name: 'Dropbox', color: '#0061FF' },
  { id: 'simple-icons:googledrive', name: 'Google Drive', color: '#4285F4' },
  { id: 'simple-icons:onedrive', name: 'OneDrive', color: '#0078D4' },
  { id: 'simple-icons:jira', name: 'Jira', color: '#0052CC' },
  { id: 'simple-icons:trello', name: 'Trello', color: '#0052CC' },
  { id: 'simple-icons:asana', name: 'Asana', color: '#F06A6A' },
  { id: 'simple-icons:linear', name: 'Linear', color: '#5E6AD2' },
]

// Category icons for workflow modules
export const CATEGORY_ICONS = [
  { id: 'lucide:bot', name: 'AI Bot', color: '#8B5CF6' },
  { id: 'lucide:brain', name: 'AI Brain', color: '#EC4899' },
  { id: 'lucide:sparkles', name: 'AI Sparkles', color: '#F59E0B' },
  { id: 'lucide:message-square', name: 'Chat', color: '#10B981' },
  { id: 'lucide:mail', name: 'Email', color: '#3B82F6' },
  { id: 'lucide:database', name: 'Database', color: '#6366F1' },
  { id: 'lucide:globe', name: 'Web', color: '#06B6D4' },
  { id: 'lucide:file-text', name: 'Document', color: '#F97316' },
  { id: 'lucide:image', name: 'Image', color: '#14B8A6' },
  { id: 'lucide:video', name: 'Video', color: '#EF4444' },
  { id: 'lucide:code', name: 'Code', color: '#84CC16' },
  { id: 'lucide:terminal', name: 'Terminal', color: '#22C55E' },
  { id: 'lucide:webhook', name: 'Webhook', color: '#A855F7' },
  { id: 'lucide:zap', name: 'Automation', color: '#FBBF24' },
  { id: 'lucide:settings', name: 'Settings', color: '#64748B' },
  { id: 'lucide:folder', name: 'Folder', color: '#0EA5E9' },
  { id: 'lucide:cloud', name: 'Cloud', color: '#38BDF8' },
  { id: 'lucide:lock', name: 'Security', color: '#DC2626' },
  { id: 'lucide:users', name: 'Users', color: '#7C3AED' },
  { id: 'lucide:calendar', name: 'Calendar', color: '#F43F5E' },
]

/**
 * Generate Iconify CDN URL for an icon
 *
 * @param {string} iconId - Icon ID (e.g., 'simple-icons:openai', 'lucide:bot')
 * @param {Object} options - Options
 * @param {string} options.color - Icon color (hex without #)
 * @param {number} options.size - Icon size in pixels
 * @returns {string} CDN URL
 *
 * @example
 * getIconUrl('simple-icons:openai', { color: '10a37f', size: 24 })
 * // => 'https://api.iconify.design/simple-icons/openai.svg?color=%2310a37f&width=24&height=24'
 */
export function getIconUrl(iconId, options = {}) {
  if (!iconId) return null

  const { color, size = 24 } = options

  // Parse icon ID (format: "prefix:name" or just "name")
  let prefix, name
  if (iconId.includes(':')) {
    [prefix, name] = iconId.split(':')
  } else {
    // Default to lucide for backwards compatibility
    prefix = 'lucide'
    name = iconId
  }

  // Build URL
  let url = `${ICONIFY_CDN}/${prefix}/${name}.svg`

  // Add query params
  const params = new URLSearchParams()
  if (color) {
    // Ensure color has # prefix for URL encoding
    const colorValue = color.startsWith('#') ? color : `#${color}`
    params.set('color', colorValue)
  }
  if (size) {
    params.set('width', size.toString())
    params.set('height', size.toString())
  }

  const queryString = params.toString()
  if (queryString) {
    url += `?${queryString}`
  }

  return url
}

/**
 * Search icons by name
 *
 * @param {string} query - Search query
 * @param {Object} options - Options
 * @param {boolean} options.includeBrands - Include brand icons
 * @param {boolean} options.includeCategories - Include category icons
 * @param {number} options.limit - Max results
 * @returns {Array} Matching icons
 */
export function searchIcons(query, options = {}) {
  const {
    includeBrands = true,
    includeCategories = true,
    limit = 50
  } = options

  if (!query) {
    // Return popular icons when no query
    const results = []
    if (includeBrands) results.push(...BRAND_ICONS.slice(0, 20))
    if (includeCategories) results.push(...CATEGORY_ICONS.slice(0, 10))
    return results.slice(0, limit)
  }

  const lowerQuery = query.toLowerCase()
  const results = []

  if (includeBrands) {
    const matchingBrands = BRAND_ICONS.filter(icon =>
      icon.name.toLowerCase().includes(lowerQuery) ||
      icon.id.toLowerCase().includes(lowerQuery)
    )
    results.push(...matchingBrands)
  }

  if (includeCategories) {
    const matchingCategories = CATEGORY_ICONS.filter(icon =>
      icon.name.toLowerCase().includes(lowerQuery) ||
      icon.id.toLowerCase().includes(lowerQuery)
    )
    results.push(...matchingCategories)
  }

  return results.slice(0, limit)
}

export default {
  BRAND_ICONS,
  CATEGORY_ICONS,
  getIconUrl,
  searchIcons
}
