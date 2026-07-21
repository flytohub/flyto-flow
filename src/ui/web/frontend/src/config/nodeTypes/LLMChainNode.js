/**
 * LLM Chain Node - AI Language Model chain configuration
 *
 * Enables prompt template → LLM → response workflows.
 * Supports multiple providers: OpenAI, Anthropic (Claude).
 *
 * 5-Star: Handles defined in backend node_config.py
 */
export default {
  type: 'llm-chain',

  // Default parameters
  getDefaultParams: () => ({
    // Provider selection: openai, anthropic
    provider: 'openai',

    // Model ID - varies by provider
    model: 'gpt-4o',

    // Optional system prompt for context setting
    systemPrompt: '',

    // User prompt with {{variable}} interpolation support
    userPrompt: '',

    // Generation parameters
    temperature: 0.7,
    maxTokens: 1000,

    // Streaming (future enhancement)
    stream: false
  }),

  // Styling
  styleClass: 'llm-chain-node',
  isFlowControl: false,

  // AI-specific flags
  isAI: true,
  isLLMChain: true,

  // Use dedicated params editor
  paramsComponent: 'LLMChainParams',

  // Show add button for chaining
  showAddButton: true
}
