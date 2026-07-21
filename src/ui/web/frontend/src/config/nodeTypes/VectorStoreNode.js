/**
 * Vector Store Node - Vector database operations for RAG
 *
 * Enables document storage, similarity search, and deletion.
 * Integrates with Qdrant vector database via flyto-pro.
 *
 * 5-Star: Handles defined in backend node_config.py
 */
export default {
  type: 'vector-store',

  // Default parameters
  getDefaultParams: () => ({
    // Operation mode: insert | search | delete
    operation: 'search',

    // Target collection
    collection: 'flyto_knowledge',

    // Insert mode params
    content: '',
    documentId: '',
    metadata: {},

    // Search mode params
    query: '',
    topK: 5,
    scoreThreshold: 0.7,
    filters: {},

    // Delete mode params
    deleteIds: [],
    deleteFilter: {}
  }),

  // Styling
  styleClass: 'vector-store-node',
  isFlowControl: false,

  // AI-specific flags
  isAI: true,
  isVectorStore: true,

  // Use dedicated params editor
  paramsComponent: 'VectorStoreParams',

  // Show add button for chaining
  showAddButton: true
}
