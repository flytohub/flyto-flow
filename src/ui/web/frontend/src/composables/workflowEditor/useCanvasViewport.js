/**
 * Canvas Viewport Composable
 *
 * Handles zoom, fit view, auto layout, and viewport persistence.
 */
import { useVueFlow } from '@vue-flow/core'

export function useCanvasViewport({ nodes }) {
  const { zoomIn, zoomOut, fitView, setCenter, getViewport, setViewport } = useVueFlow()

  function handleZoomIn() {
    zoomIn()
  }

  function handleZoomOut() {
    zoomOut()
  }

  function handleFitView() {
    fitView({ padding: 0.2 })
  }

  function restoreViewport(savedViewport) {
    if (savedViewport && 'x' in savedViewport && 'y' in savedViewport) {
      setTimeout(() => {
        setViewport({
          x: savedViewport.x,
          y: savedViewport.y,
          zoom: savedViewport.zoom || 1
        }, { duration: 0 })
      }, 150)
    }
  }

  function createViewportChangeHandler(emit) {
    let viewportDebounceTimer = null

    function handleViewportChange() {
      if (viewportDebounceTimer) clearTimeout(viewportDebounceTimer)
      viewportDebounceTimer = setTimeout(() => {
        const viewport = getViewport()
        emit('update:viewport', {
          x: Math.round(viewport.x),
          y: Math.round(viewport.y),
          zoom: Math.round(viewport.zoom * 100) / 100
        })
      }, 500)
    }

    function cleanup() {
      if (viewportDebounceTimer) {
        clearTimeout(viewportDebounceTimer)
        viewportDebounceTimer = null
      }
    }

    return { handleViewportChange, cleanup }
  }

  return {
    handleZoomIn,
    handleZoomOut,
    handleFitView,
    restoreViewport,
    setCenter,
    createViewportChangeHandler
  }
}
