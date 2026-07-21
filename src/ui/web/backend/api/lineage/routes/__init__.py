"""
Lineage Routes Package

Lineage API routes organized by functionality:
- Graph: Full lineage graph
- Step: Step-specific lineage, dependencies, impact
- Variable: Variable tracing
- Swimlane: Swimlane view visualization
- Focus: Click-to-focus node view
- Item: Item-level lineage tracking

API Routes:
    GET  /executions/{id}/graph - Get full lineage graph
    GET  /executions/{id}/steps/{step_id} - Get step lineage
    GET  /executions/{id}/steps/{step_id}/dependencies - Get step dependencies
    GET  /executions/{id}/steps/{step_id}/impact - Get step impact
    GET  /executions/{id}/variables/{name} - Trace variable
    GET  /executions/{id}/swimlane - Get swimlane view
    GET  /executions/{id}/focus/{node_id} - Get focused node view
    GET  /executions/{id}/item-lineage - Get item-level lineage
    GET  /executions/{id}/steps/{step_id}/item-origins - Get item origins
    GET  /executions/{id}/trace/{path} - Trace variable path
"""

from fastapi import APIRouter

from api.lineage.routes.graph import router as graph_router
from api.lineage.routes.step import router as step_router
from api.lineage.routes.variable import router as variable_router
from api.lineage.routes.swimlane import router as swimlane_router
from api.lineage.routes.focus import router as focus_router
from api.lineage.routes.item import router as item_router

# DEPRECATED: Not used by frontend. Retained for potential future use.
# Main router that combines all sub-routers
router = APIRouter()
router.include_router(graph_router)
router.include_router(step_router)
router.include_router(variable_router)
router.include_router(swimlane_router)
router.include_router(focus_router)
router.include_router(item_router)

__all__ = ["router"]
