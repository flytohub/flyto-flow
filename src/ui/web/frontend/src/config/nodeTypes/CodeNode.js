/**
 * Code Node - Execute custom JavaScript/Python code
 *
 * This node type allows users to write and execute custom code
 * for data transformation, filtering, and complex logic.
 *
 * 5-Star: Handles defined in backend node_config.py
 */
export default {
  type: 'code',

  // Default parameters with code template
  getDefaultParams: () => ({
    language: 'javascript',
    code: `// Access input from previous step
const items = $input.all();

// Process each item
for (const item of items) {
  item.processed = true;
}

// Return the result
return items;`
  }),

  // Styling - purple accent for code nodes
  styleClass: 'code-node',
  isFlowControl: false,

  // Use dedicated code editor component
  paramsComponent: 'CodeNodeParams',

  // Show add button for chaining
  showAddButton: true,

  // Code node specific flag
  isCode: true
}
