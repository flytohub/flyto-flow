/**
 * Builder Metadata Store Module
 *
 * S-Grade: Re-export all metadata store functionality.
 *
 * Split modules:
 * - state.js: State refs and getters
 * - templateActions.js: Template operations
 * - sectionActions.js: Section and component operations
 * - metadataStoreCore.js: Main store
 */

// Main store
export { useBuilderMetadataStore } from './metadataStoreCore'

// State factory (for testing/composition)
export { createMetadataState, createMetadataGetters } from './state'

// Action factories (for testing/composition)
export { createTemplateActions } from './templateActions'
export { createSectionActions, createComponentActions, createSaveActions } from './sectionActions'
