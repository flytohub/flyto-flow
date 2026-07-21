/**
 * Payload Encryption (Application-Layer)
 *
 * RSA + AES-256-GCM hybrid encryption on top of TLS.
 * Uses Web Crypto API (SubtleCrypto) — no external dependencies.
 *
 * All HTTP methods are supported:
 * - POST/PUT/PATCH: AES key embedded in encrypted body envelope
 * - GET/DELETE: AES key sent via X-Enc-Key header (RSA-encrypted)
 *
 * All responses are encrypted with the per-request AES key.
 */

let _serverPublicKey = null
let _encryptionEnabled = null
let _initPromise = null

/**
 * Fetch and cache the server's encryption config + public key.
 * Retries on failure (e.g., server temporarily down at app init).
 */
async function _ensurePublicKey() {
  if (_encryptionEnabled === true && _serverPublicKey) return
  if (_initPromise) return _initPromise

  _initPromise = (async () => {
    try {
      const resp = await fetch('/api/encryption/public-key')
      const data = await resp.json()

      _encryptionEnabled = data.enabled === true

      if (_encryptionEnabled && data.publicKey) {
        const pem = data.publicKey
          .replace(/-----BEGIN PUBLIC KEY-----/, '')
          .replace(/-----END PUBLIC KEY-----/, '')
          .replace(/\s/g, '')

        const binaryDer = Uint8Array.from(atob(pem), c => c.charCodeAt(0))

        _serverPublicKey = await crypto.subtle.importKey(
          'spki',
          binaryDer.buffer,
          { name: 'RSA-OAEP', hash: 'SHA-256' },
          false,
          ['encrypt']
        )
      }
    } catch (e) {
      _encryptionEnabled = false
      // Allow retry on next call
      _initPromise = null
      return
    }
    _initPromise = null
  })()

  return _initPromise
}

/**
 * Check if payload encryption is enabled
 */
export async function isEncryptionEnabled() {
  await _ensurePublicKey()
  return _encryptionEnabled === true && _serverPublicKey !== null
}

/**
 * Generate a per-request AES key + RSA-encrypted key header.
 * Used for ALL request types (GET, POST, etc.) so responses can always be encrypted.
 *
 * @returns {{ aesKey: CryptoKey, encKeyHeader: string, ivHeader: string } | null}
 */
export async function generateRequestKey() {
  await _ensurePublicKey()
  if (!_encryptionEnabled || !_serverPublicKey) return null

  const aesKey = await crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  )

  const rawAesKey = await crypto.subtle.exportKey('raw', aesKey)
  const encryptedAesKey = await crypto.subtle.encrypt(
    { name: 'RSA-OAEP' },
    _serverPublicKey,
    rawAesKey
  )

  return {
    aesKey,
    encKeyHeader: _arrayBufferToBase64(encryptedAesKey),
  }
}

/**
 * Encrypt request body → envelope (for POST/PUT/PATCH)
 *
 * @param {Object|string} payload - Request body
 * @param {CryptoKey} aesKey - AES key from generateRequestKey()
 * @returns {Object} Encrypted envelope { _e, k, iv, d }
 */
export async function encryptPayload(payload, aesKey) {
  const plaintext = typeof payload === 'string' ? payload : JSON.stringify(payload)
  const encoded = new TextEncoder().encode(plaintext)

  const iv = crypto.getRandomValues(new Uint8Array(12))

  const ciphertext = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    aesKey,
    encoded
  )

  const rawAesKey = await crypto.subtle.exportKey('raw', aesKey)
  const encryptedAesKey = await crypto.subtle.encrypt(
    { name: 'RSA-OAEP' },
    _serverPublicKey,
    rawAesKey
  )

  return {
    _e: true,
    k: _arrayBufferToBase64(encryptedAesKey),
    iv: _arrayBufferToBase64(iv),
    d: _arrayBufferToBase64(ciphertext),
  }
}

/**
 * Decrypt response envelope
 *
 * @param {Object} envelope - { _e: true, iv: ..., d: ... }
 * @param {CryptoKey} aesKey - AES key from the request
 * @returns {Object} Decrypted response data
 */
export async function decryptResponse(envelope, aesKey) {
  const iv = _base64ToArrayBuffer(envelope.iv)
  const ciphertext = _base64ToArrayBuffer(envelope.d)

  const plaintext = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv },
    aesKey,
    ciphertext
  )

  const decoded = new TextDecoder().decode(plaintext)
  return JSON.parse(decoded)
}

// --- Helpers ---

function _arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

function _base64ToArrayBuffer(base64) {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes.buffer
}
