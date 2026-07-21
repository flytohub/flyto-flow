export const LEGAL_PAGE_METADATA = Object.freeze({
  terms: {
    lastUpdated: '2025-12-05',
    contactEmail: 'conduct@flyto2.com'
  },
  privacy: {
    lastUpdated: '2025-12-05',
    contactEmail: 'privacy@flyto2.com'
  }
})

export function getLegalPageMetadata(page) {
  return LEGAL_PAGE_METADATA[page]
}
