/**
 * AI Agent Node - n8n-style multi-port architecture
 *
 * Multiple input ports:
 * - input: main control flow (from trigger or previous node)
 * - model: connect ai.model for LLM configuration
 * - memory: connect ai.memory for conversation history
 * - tools: connect tool modules (multiple allowed)
 *
 * Output ports:
 * - output: main output
 * - error: error output
 *
 * 5-Star: Handles defined in backend node_config.py
 */

export default {
  type: 'ai-agent',

  getDefaultParams: () => ({
    // Model settings (fallback if no ai.model connected)
    provider: 'openai',
    model: 'gpt-4o',
    temperature: 0.3,

    // Agent settings
    task: '',
    tools: [],
    toolsAllowed: ['browser.*', 'file.*'],
    maxIterations: 10,

    // Optional
    systemPrompt: '',
    context: {}
  }),

  styleClass: 'ai-agent-node',
  isFlowControl: false,
  isAI: true,
  isAgent: true,
  hasMultipleInputs: true,  // Flag for multi-port rendering
  paramsComponent: 'AIAgentParams',
  showAddButton: true
}
