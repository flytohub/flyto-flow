/**
 * Builder Metadata Store
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All metadata logic split into metadata/* directory.
 *
 * Split modules:
 * - metadata/state.js: State refs and getters
 * - metadata/templateActions.js: Template operations
 * - metadata/sectionActions.js: Section and component operations
 * - metadata/metadataStoreCore.js: Main store
 */

// Re-export all from split modules
export {
  useBuilderMetadataStore,
  createMetadataState,
  createMetadataGetters,
  createTemplateActions,
  createSectionActions,
  createComponentActions,
  createSaveActions
} from './metadata/index'
