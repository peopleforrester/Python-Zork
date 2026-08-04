// ABOUTME: A stable per-browser id that scopes this player's saves server-side.
// ABOUTME: Must survive a refresh, or `save` then reload then `load` breaks.

const STORAGE_KEY = 'python-zork.save-key';

/** A random id, from the platform CSPRNG where available. */
function mint(): string {
  const c = globalThis.crypto;
  if (c && typeof c.randomUUID === 'function') return c.randomUUID();
  if (c && typeof c.getRandomValues === 'function') {
    const bytes = new Uint8Array(16);
    c.getRandomValues(bytes);
    return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
  }
  // No CSPRNG at all. The key only separates players from each other, so a
  // weaker source is worse than the alternatives but far better than every
  // player sharing one namespace, which is the bug this exists to fix.
  return `fallback-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

/**
 * This browser's save key, minted once and remembered.
 *
 * Persisted in localStorage rather than held in memory, because the socket id
 * changes on every reload and saves have to outlive that. Falls back to a
 * per-session key when storage is unavailable (private mode, storage disabled),
 * which costs the player their saves across a reload but never collides with
 * another player.
 */
export function saveKey(): string {
  try {
    const store = globalThis.localStorage;
    if (!store) return memoryKey();
    const existing = store.getItem(STORAGE_KEY);
    if (existing) return existing;
    const fresh = mint();
    store.setItem(STORAGE_KEY, fresh);
    return fresh;
  } catch {
    // Private mode and disabled storage throw rather than returning null.
    return memoryKey();
  }
}

let inMemory: string | null = null;

function memoryKey(): string {
  if (inMemory === null) inMemory = mint();
  return inMemory;
}
