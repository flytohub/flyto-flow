/**
 * HTTP Node - HTTP Request node configuration
 *
 * Used for making HTTP requests (GET, POST, PUT, DELETE, etc.)
 * with support for headers, query params, body, and authentication.
 *
 * 5-Star: Handles defined in backend node_config.py
 */
import { DEFAULTS } from '@/config/defaults'

export default {
  type: 'http',

  // Default parameters
  getDefaultParams: () => ({
    method: 'GET',
    url: '',
    headers: {},
    query: {},
    body: null,
    contentType: 'application/json',
    auth: null,
    timeout: DEFAULTS.TIMEOUTS.HTTP_NODE,
    followRedirects: true,
    verifySsl: true
  }),

  // Styling
  styleClass: 'http-node',
  isFlowControl: false,

  // Use dedicated HTTP params editor
  paramsComponent: 'HttpNodeParams',

  // Show add button for chaining
  showAddButton: true,

  // HTTP node specific flag
  isHttp: true
}
