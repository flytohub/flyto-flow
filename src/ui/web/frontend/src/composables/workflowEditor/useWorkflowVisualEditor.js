/**
 * Workflow Visual Editor Composable
 * Handles n8n-style visual workflow editing with Vue Flow
 */

import { ref, computed } from 'vue'

// Grid configuration for snap alignment
const GRID_SIZE = 20
const SNAP_THRESHOLD = 10

export function useWorkflowVisualEditor() {
  // Vue Flow elements (nodes + edges)
  const elements = ref([])

  // Selected node for properties panel
  const selectedNode = ref(null)

  // Drag and drop state
  const draggedNode = ref(null)
  const isDragging = ref(false)
  const dragPreviewPosition = ref({ x: 0, y: 0 })
  const isOverDropZone = ref(false)

  // Grid alignment state
  const snapGuides = ref({ x: null, y: null })
  const showGridOverlay = ref(false)

  // VueFlow ref
  const vueFlowRef = ref(null)

  // Counter for generating unique IDs
  let nodeIdCounter = 0

  /**
   * Create custom drag preview image
   */
  function createDragPreview(nodeData) {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const width = 180
    const height = 60

    canvas.width = width
    canvas.height = height

    // Semi-transparent background
    ctx.fillStyle = 'rgba(30, 41, 59, 0.9)'
    ctx.strokeStyle = '#8B5CF6'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.roundRect(0, 0, width, height, 8)
    ctx.fill()
    ctx.stroke()

    // Node name
    ctx.fillStyle = '#ffffff'
    ctx.font = '13px system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(nodeData.name || nodeData.moduleId || 'Node', width / 2, 25)

    // Module ID (smaller)
    ctx.fillStyle = '#94a3b8'
    ctx.font = '10px system-ui, sans-serif'
    ctx.fillText(nodeData.moduleId || '', width / 2, 42)

    return canvas
  }

  /**
   * Start dragging a node from toolbox
   */
  function onDragStart(event, nodeData) {
    draggedNode.value = nodeData
    isDragging.value = true
    showGridOverlay.value = true

    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('application/vueflow', JSON.stringify(nodeData))

    // Create custom drag preview
    try {
      const preview = createDragPreview(nodeData)
      event.dataTransfer.setDragImage(preview, 90, 30)
    } catch (e) {
      // Fallback to default preview if canvas fails
    }

    // Add drag class to body for global styling
    document.body.classList.add('workflow-dragging')
  }

  /**
   * Handle drag over canvas
   */
  function onDragOver(event) {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
    isOverDropZone.value = true

    // Update preview position for ghost effect
    if (vueFlowRef.value) {
      const bounds = event.target.getBoundingClientRect()
      const position = vueFlowRef.value.project({
        x: event.clientX - bounds.left,
        y: event.clientY - bounds.top
      })

      // Calculate snapped position
      const snappedX = Math.round(position.x / GRID_SIZE) * GRID_SIZE
      const snappedY = Math.round(position.y / GRID_SIZE) * GRID_SIZE

      dragPreviewPosition.value = { x: snappedX, y: snappedY }

      // Show snap guides if close to grid line
      snapGuides.value = {
        x: Math.abs(position.x - snappedX) < SNAP_THRESHOLD ? snappedX : null,
        y: Math.abs(position.y - snappedY) < SNAP_THRESHOLD ? snappedY : null
      }
    }
  }

  /**
   * Handle drag leave from canvas
   */
  function onDragLeave(event) {
    // Only trigger if leaving the canvas entirely
    if (!event.currentTarget.contains(event.relatedTarget)) {
      isOverDropZone.value = false
      snapGuides.value = { x: null, y: null }
    }
  }

  /**
   * Handle drag end (cleanup)
   */
  function onDragEnd() {
    isDragging.value = false
    isOverDropZone.value = false
    showGridOverlay.value = false
    snapGuides.value = { x: null, y: null }
    document.body.classList.remove('workflow-dragging')
  }

  /**
   * Drop node onto canvas
   */
  function onDrop(event) {
    event.preventDefault()

    if (!draggedNode.value || !vueFlowRef.value) return

    const flowInstance = vueFlowRef.value
    const bounds = event.target.getBoundingClientRect()

    // Calculate position relative to canvas
    const rawPosition = flowInstance.project({
      x: event.clientX - bounds.left,
      y: event.clientY - bounds.top
    })

    // Snap to grid
    const position = {
      x: Math.round(rawPosition.x / GRID_SIZE) * GRID_SIZE,
      y: Math.round(rawPosition.y / GRID_SIZE) * GRID_SIZE
    }

    // Create new node
    const newNode = {
      id: `node-${++nodeIdCounter}`,
      type: 'custom',
      position,
      data: {
        ...draggedNode.value,
        params: (() => { try { return JSON.parse(JSON.stringify(draggedNode.value.params || {})) } catch { return { ...(draggedNode.value.params || {}) } } })()
      }
    }

    elements.value = [...elements.value, newNode]

    // Cleanup drag state
    draggedNode.value = null
    onDragEnd()
  }

  /**
   * Handle node click
   */
  function onNodeClick(event) {
    selectedNode.value = event.node
  }

  /**
   * Delete selected node
   */
  function deleteNode(nodeId) {
    elements.value = elements.value.filter(el => el.id !== nodeId)
    if (selectedNode.value?.id === nodeId) {
      selectedNode.value = null
    }
  }

  /**
   * Create a workflow node from a module definition
   * Factory function for consistent node structure
   *
   * @param {Object} module - Module definition from catalog (CanonicalModule format)
   * @param {Object} options - Optional overrides for position, id, etc.
   * @returns {Object} The created node (also added to elements)
   */
  function createNodeFromModule(module, options = {}) {
    // Use moduleId as fallback if module property is undefined
    const moduleId = module.module || module.moduleId

    const nodeId = options.id || `node_${Date.now()}`
    const position = options.position || { x: 250, y: 150 }

    const newNode = {
      id: nodeId,
      type: 'custom',
      position,
      data: {
        module: moduleId,
        params: { ...(module.params || module.defaultParams || {}) }
      }
    }

    // Add to elements
    elements.value = [...elements.value, newNode]

    return newNode
  }

  return {
    // State
    elements,
    selectedNode,
    vueFlowRef,
    isDragging,
    isOverDropZone,
    dragPreviewPosition,
    snapGuides,
    showGridOverlay,

    // Methods
    onDragStart,
    onDragOver,
    onDragLeave,
    onDragEnd,
    onDrop,
    onNodeClick,
    deleteNode,
    createNodeFromModule
  }
}
