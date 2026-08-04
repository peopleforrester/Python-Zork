// ABOUTME: The save key must be stable across reloads and unique per browser.
// ABOUTME: Stability is what keeps save-then-refresh-then-load working.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

/**
 * A working localStorage. This environment's jsdom does not provide one at all
 * (`window.localStorage` is undefined, not merely throwing), so the persistence
 * behaviour has to be tested against a stand-in. That absence is also why
 * saveKey guards its storage access: the no-storage path is the one that runs
 * here, and a real browser takes the other.
 */
function fakeStorage() {
  const map = new Map<string, string>();
  return {
    getItem: (k: string) => (map.has(k) ? map.get(k)! : null),
    setItem: (k: string, v: string) => void map.set(k, v),
    removeItem: (k: string) => void map.delete(k),
    clear: () => map.clear(),
    get length() { return map.size; },
    key: (i: number) => Array.from(map.keys())[i] ?? null
  };
}

async function freshModule() {
  vi.resetModules();
  return import('./saveKey');
}

describe('saveKey with working storage', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', fakeStorage());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns a non-empty key', async () => {
    expect((await freshModule()).saveKey().length).toBeGreaterThan(8);
  });

  it('returns the same key on every call', async () => {
    const { saveKey } = await freshModule();
    expect(saveKey()).toBe(saveKey());
  });

  it('persists the key, so a reload finds the same saves', async () => {
    const key = (await freshModule()).saveKey();
    expect(globalThis.localStorage.getItem('python-zork.save-key')).toBe(key);
  });

  it('reuses a key already in storage rather than minting a new one', async () => {
    globalThis.localStorage.setItem('python-zork.save-key', 'previously-stored');
    expect((await freshModule()).saveKey()).toBe('previously-stored');
  });

  it('survives a reload, which is the whole point', async () => {
    // Same storage, fresh module: exactly what a browser refresh does.
    const before = (await freshModule()).saveKey();
    const after = (await freshModule()).saveKey();
    expect(after).toBe(before);
  });

  it('mints a different key for a browser with empty storage', async () => {
    const a = (await freshModule()).saveKey();
    vi.stubGlobal('localStorage', fakeStorage());
    const b = (await freshModule()).saveKey();
    expect(b).not.toBe(a);
  });
});

describe('saveKey without usable storage', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('still returns a stable key when storage throws', async () => {
    vi.stubGlobal('localStorage', {
      getItem() { throw new Error('denied'); },
      setItem() { throw new Error('denied'); }
    });
    const { saveKey } = await freshModule();
    const key = saveKey();
    expect(key.length).toBeGreaterThan(8);
    expect(saveKey()).toBe(key);
  });

  it('still returns a stable key when storage is absent entirely', async () => {
    // This environment's default. Costs saves across a reload, but never
    // collides with another player, which is the property that matters.
    vi.stubGlobal('localStorage', undefined);
    const { saveKey } = await freshModule();
    const key = saveKey();
    expect(key.length).toBeGreaterThan(8);
    expect(saveKey()).toBe(key);
  });
});
