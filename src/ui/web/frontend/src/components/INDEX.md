# Component Index

Total: 294 Vue components across 30+ categories.

---

## Top-Level (root components)

Used directly in workflow canvas views.

- `AddNodeMenu.vue` — Node creation menu overlay
- `EmptyCanvasState.vue` — Empty workflow placeholder
- `LanguageSwitcher.vue` — i18n language toggle
- `ModuleCard.vue` — Module display card
- `ModuleSelector.vue` — Module picker dropdown
- `ValueSourceSelector.vue` — Input source type selector
- `WorkflowCanvas.vue` — Main canvas container
- `WorkflowNode.vue` — Single node on canvas

---

## Categories

### addNodeMenu/
Node creation menu sub-components (header, search, categories, stats).
7 components. Internal to AddNodeMenu.

### admin/
Admin dashboard: sidebar, telemetry views, user management, SEO tools.
20 components (10 in `seo/` sub-folder).

### ai/
AI chat interface: floating button, chat window, message rendering.
4 components.

### alerts/
Alert management: active alerts, history, rule editing.
5 components.

### audit/
Audit log viewer: filters, table, detail panel, chain verification.
6 components.

### collaboration/
Real-time collaboration: chat, cursors, panel, invites, node locking.
6 components.

### common/ (shared/reusable)
**37 components.** The largest reusable library:
- Form inputs: `AppInput`, `AppSelect`, `AppTextarea`, `NumberInput`, `ColorPicker`
- Modals: `BaseModal`, `Modal`, `ConfirmDialog`, `GlobalConfirmDialog`
- Display: `StatusBadge`, `SkeletonCard`, `EmptyState`, `LoadingButton`
- Editors: `MonacoEditor`, `IconPicker`, `ImageCropperModal`, `LabelPicker`
- Layout: `PageTabs`, `PageTransition`, `DisclosureSection`, `FilterChips`
- Specialized: `PreviewRenderer`, `RegionSelector`, `UsageChart`, `WaveHero`

### creator/
Creator dashboard: regional sales chart.
1 component.

### dashboard/
Main dashboard sections: recent activity, sales overview, usage.
3 components.

### debug/
Developer debug tools: toolbar, evidence, execution history, lineage, replay, versions.
13 components.

### execution/
Workflow execution UI: browser panel, breakpoints, checkpoints, timeline, interact dialog.
11 components.

### form/
Form utilities: file upload, image upload.
2 components.

### home/
Landing/home page: feature cards, hero badge, stats, wave divider.
4 components.

### layout/
App shell: navbar, footer.
2 components.

### lineage/
Execution lineage visualization: decision nodes, loops, steps, storyline.
4 components.

### login/
Authentication UI: forms, branding, animated background, password modal.
10 components.

### marketplace/
Marketplace browsing: action button, template card, list item.
3 components.

### messaging/
Messaging integrations: integration form.
1 component.

### metrics/
Metrics display: stat card.
1 component.

### notifications/
Notification center.
1 component.

### plugins/
Plugin management: plugin card.
1 component.

### reviews/
Review system: review card, review form.
2 components.

### settings/
User settings: AI config, linked accounts, API keys, licenses.
4 components.

### templateBuilder/
**The largest category (~75 components).** Template/workflow builder:
- Top-level: header, tab bar, canvas, skeleton, dialogs, overlays
- Node params: AI agent, code, flow control, form input, HTTP, LLM chain, vector store
- Canvas sub-system (`canvas/`): panels, toolbox, component previews (20+ preview types)
- Params fields (`params/fields/`): checkbox, number, select, text, textarea
- Preview renderers (`preview/renderers/`): 13 form element renderers
- Properties (`properties/`): conditional, header, validation sections
- Shared (`shared/`): array editor, auth config, expression tools, key-value editor, variable selector (5 sub-components)

### templates/
Template management: CRUD, folders, publishing, collaboration, pull requests, issues.
35 components across sub-folders:
- Root: cards, filters, grid, toolbar, modals, invite keys, folders
- `collaboration/`: commit timeline, contributor list
- `detail/`: header, hero, sidebar
- `publish/`: invite keys, marketplace toggle, pricing, protection, visibility
- `pullRequests/`: PR cards, diff views, activity timeline, status badges (8 components)
- `templateIssues/`: issue card, detail, form, list

### toolLibrary/
Tool library browsing: card, row.
2 components.

### toolRunner/
Tool execution runner: flow, logs, navbar, resolved, results panels.
5 components.

### tools/
Simple tool views: flow steps, output, process button, header.
4 components.

### traces/
Distributed tracing: span detail, waterfall, status badge/dot.
4 components.

### triggers/
Trigger configuration: config panel, indicator, webhook test panel.
3 components.

### valueSource/
Value source editors: expression, linked, literal.
3 components.

### variables/
Variable management: credential manager, variable editor, variable list.
3 components.

### wallet/
Credits/wallet: execute confirm dialog, top-up modal.
2 components.

### workflow/
Workflow settings: error workflow selector.
1 component.

### workflowCanvas/
Canvas controls and node types: controls, context menu, search, modals, badges.
21 components:
- Root: controls, case selector, checkpoint, context menu, execution bar, node actions, search, notes, save-as-template
- `edges/`: GlowEdge
- `nodes/`: AIAgentNode, AISubNode, BranchNode, ContainerNode, DefaultNode, LoopNode, StickyNote, SwitchNode, TriggerNode, ExecutionDetailDialog, NodeCardIcon, NodeExecutionBadges

---

## Reusable vs Page-Specific

**Shared/reusable** (safe to use anywhere):
- `common/*` — generic UI primitives
- `layout/*` — app shell
- `form/*` — form utilities
- `valueSource/*` — value source editors
- `variables/*` — variable management

**Page-specific** (tightly coupled to their feature):
- `admin/*`, `templateBuilder/*`, `execution/*`, `debug/*`
- `marketplace/*`, `templates/*`, `collaboration/*`
- `workflowCanvas/*`, `toolRunner/*`
