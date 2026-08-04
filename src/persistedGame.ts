// ABOUTME: Keeps the player's game in this browser so a refresh resumes it.
// ABOUTME: Browser-side because the server container has no volume to write to.

const STORAGE_KEY = 'python-zork.game-state';

/** Serialized save from the server. Opaque here; only the server reads it. */
export type GameBlob = Record<string, unknown>;

function storage(): Storage | null {
  try {
    return globalThis.localStorage ?? null;
  } catch {
    // Private mode and disabled storage throw on access rather than returning null.
    return null;
  }
}

/**
 * Remember the current game.
 *
 * Called on every state change, so it must stay cheap and must never throw:
 * storage can be full or disabled, and losing the ability to resume is not a
 * reason to break the game being played.
 */
export function remember(blob: GameBlob): void {
  const store = storage();
  if (!store) return;
  try {
    store.setItem(STORAGE_KEY, JSON.stringify(blob));
  } catch {
    // Quota exceeded, or storage disabled mid-session. Nothing to do.
  }
}

/** The remembered game, or null if there is none or it is unreadable. */
export function recall(): GameBlob | null {
  const store = storage();
  if (!store) return null;
  try {
    const raw = store.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    // A non-object would be rejected by the server anyway; drop it here so the
    // player is not asked to resume something that cannot load.
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
      ? (parsed as GameBlob)
      : null;
  } catch {
    return null;
  }
}

/** True when there is a game to resume. Drives the button label. */
export function hasSavedGame(): boolean {
  return recall() !== null;
}

/** Discard the remembered game, for the player who wants a clean start. */
export function forget(): void {
  const store = storage();
  if (!store) return;
  try {
    store.removeItem(STORAGE_KEY);
  } catch {
    // Nothing to do; the next remember() will overwrite it anyway.
  }
}
