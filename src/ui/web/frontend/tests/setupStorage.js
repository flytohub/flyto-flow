class MemoryStorage {
  constructor() {
    this.store = new Map()
  }

  get length() {
    return this.store.size
  }

  key(index) {
    return Array.from(this.store.keys())[index] ?? null
  }

  getItem(key) {
    const normalizedKey = String(key)
    return this.store.has(normalizedKey) ? this.store.get(normalizedKey) : null
  }

  setItem(key, value) {
    this.store.set(String(key), String(value))
  }

  removeItem(key) {
    this.store.delete(String(key))
  }

  clear() {
    this.store.clear()
  }
}

function defineGlobal(name, value) {
  Object.defineProperty(globalThis, name, {
    value,
    writable: true,
    configurable: true,
  })
  if (globalThis.window) {
    Object.defineProperty(globalThis.window, name, {
      value,
      writable: true,
      configurable: true,
    })
  }
}

defineGlobal('Storage', MemoryStorage)
defineGlobal('localStorage', new MemoryStorage())
defineGlobal('sessionStorage', new MemoryStorage())
