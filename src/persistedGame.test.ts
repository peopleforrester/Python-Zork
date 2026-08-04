// ABOUTME: A refresh must resume the game, and the player must be able to clear it.
// ABOUTME: Storage is absent in this jsdom, so every path is exercised both ways.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

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

async function fresh() {
  vi.resetModules();
  return import('./persistedGame');
}

describe('with working storage', () => {
  beforeEach(() => vi.stubGlobal('localStorage', fakeStorage()));
  afterEach(() => vi.unstubAllGlobals());

  it('has nothing to resume before anything is played', async () => {
    const m = await fresh();
    expect(m.hasSavedGame()).toBe(false);
    expect(m.recall()).toBeNull();
  });

  it('remembers a game and recalls it intact', async () => {
    const m = await fresh();
    const blob = { version: '1.3', turns: 7, player: { health: 12 } };
    m.remember(blob);
    expect(m.recall()).toEqual(blob);
  });

  it('survives a reload, which is the whole point', async () => {
    (await fresh()).remember({ turns: 3 });
    // Same storage, fresh module: exactly what a browser refresh does.
    expect((await fresh()).recall()).toEqual({ turns: 3 });
  });

  it('reports that a game is available to resume', async () => {
    const m = await fresh();
    m.remember({ turns: 1 });
    expect(m.hasSavedGame()).toBe(true);
  });

  it('overwrites the previous state rather than accumulating', async () => {
    const m = await fresh();
    m.remember({ turns: 1 });
    m.remember({ turns: 2 });
    expect(m.recall()).toEqual({ turns: 2 });
  });

  it('forgets on request, so the player can start clean', async () => {
    const m = await fresh();
    m.remember({ turns: 5 });
    m.forget();
    expect(m.recall()).toBeNull();
    expect(m.hasSavedGame()).toBe(false);
  });

  it('ignores corrupt stored data instead of offering a broken resume', async () => {
    globalThis.localStorage.setItem('python-zork.game-state', '{not json');
    expect((await fresh()).recall()).toBeNull();
  });

  it('ignores stored data that is not an object', async () => {
    for (const junk of ['"a string"', '42', '[1,2]', 'null']) {
      globalThis.localStorage.setItem('python-zork.game-state', junk);
      expect((await fresh()).recall()).toBeNull();
    }
  });
});

describe('without usable storage', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('degrades quietly when storage is absent', async () => {
    vi.stubGlobal('localStorage', undefined);
    const m = await fresh();
    expect(() => m.remember({ turns: 1 })).not.toThrow();
    expect(m.recall()).toBeNull();
    expect(m.hasSavedGame()).toBe(false);
    expect(() => m.forget()).not.toThrow();
  });

  it('degrades quietly when storage throws, as in private mode', async () => {
    vi.stubGlobal('localStorage', {
      getItem() { throw new Error('denied'); },
      setItem() { throw new Error('denied'); },
      removeItem() { throw new Error('denied'); }
    });
    const m = await fresh();
    expect(() => m.remember({ turns: 1 })).not.toThrow();
    expect(m.recall()).toBeNull();
    expect(() => m.forget()).not.toThrow();
  });

  it('does not break when the quota is exceeded mid-game', async () => {
    vi.stubGlobal('localStorage', {
      getItem: () => null,
      setItem() { throw new Error('QuotaExceededError'); },
      removeItem() {}
    });
    const m = await fresh();
    expect(() => m.remember({ turns: 1 })).not.toThrow();
  });
});
