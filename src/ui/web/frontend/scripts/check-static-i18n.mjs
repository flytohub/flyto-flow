import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const bundleRoot = path.join(frontendRoot, 'src', 'i18n', 'bundled')
const flagsRoot = path.join(frontendRoot, 'public', 'flags')
const manifest = JSON.parse(fs.readFileSync(path.join(bundleRoot, 'manifest.json'), 'utf8'))

const requiredKeys = [
  'myTemplates.title',
  'myTemplates.subtitle',
  'myTemplates.importYaml',
  'myTemplates.newTemplate',
  'myTemplates.stats.total',
  'myTemplates.emptyState',
  'templateToolbar.searchPlaceholder',
  'templateToolbar.sortOptions.updated',
  'templateFolders.folders',
  'templateFolders.allTemplates',
  'footer.description',
  'footer.copyright',
  'footer.disclaimer',
]

const forbiddenHostedGroups = [
  'auth',
  'collaboration',
  'dashboard',
  'marketplace',
  'plugins',
  'rpa',
  'settings',
  'subscriptions',
]

function getPath(value, dottedPath) {
  return dottedPath.split('.').reduce((current, key) => current?.[key], value)
}

const errors = []
const localeEntries = Object.entries(manifest.locales || {})
if (!localeEntries.length) errors.push('manifest.json contains no locales')

for (const [locale, metadata] of localeEntries) {
  const localePath = path.join(bundleRoot, `${locale}.json`)
  if (!fs.existsSync(localePath)) {
    errors.push(`${locale}: bundled locale file is missing`)
    continue
  }

  const payload = JSON.parse(fs.readFileSync(localePath, 'utf8'))
  if (payload.locale !== locale) errors.push(`${locale}: locale metadata mismatch`)
  for (const group of forbiddenHostedGroups) {
    if (Object.hasOwn(payload.translations || {}, group)) {
      errors.push(`${locale}: hosted translation group must not be bundled: ${group}`)
    }
  }
  for (const key of requiredKeys) {
    const translated = getPath(payload.translations, key)
    if (typeof translated !== 'string' || !translated.trim()) {
      errors.push(`${locale}: missing translation ${key}`)
    }
  }

  const region = String(metadata.region || payload.region || '').toLowerCase()
  if (!region || !fs.existsSync(path.join(flagsRoot, `${region}.svg`))) {
    errors.push(`${locale}: static flag ${region || '(unknown)'}.svg is missing`)
  }
}

if (errors.length) {
  console.error(errors.join('\n'))
  process.exit(1)
}

console.log(`Static i18n bundle verified: ${localeEntries.length} locales with local flags`)
