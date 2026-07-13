// ABOUTME: Vitest setup run before each test file across the frontend suite.
// ABOUTME: Registers jest-dom matchers and clears the DOM between test cases.

import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// React Testing Library does not auto-unmount when globals are enabled, so
// each test starts from a clean DOM.
afterEach(() => {
  cleanup();
});

// React Flow (used by GameMap) reaches for browser APIs that jsdom does not
// implement. Without these stubs, rendering the map throws before any of our
// assertions run. They are inert no-ops sufficient for React Flow to mount.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;

class DOMMatrixReadOnlyStub {
  m22 = 1;
  constructor(_transform?: string) {}
}
globalThis.DOMMatrixReadOnly = DOMMatrixReadOnlyStub as unknown as typeof DOMMatrixReadOnly;

if (!window.matchMedia) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn()
  }));
}
