// ABOUTME: Playwright e2e config: builds the frontend and serves it via server.py.
// ABOUTME: Chromium-only, single worker (the server holds one in-process Game).

import { defineConfig, devices } from '@playwright/test';

const PORT = 5000;
const BASE_URL = `http://127.0.0.1:${PORT}`;

// Specs live in e2e/ (repo root), not tests/e2e/, so the pre-push hook's
// Python e2e probe (which runs `pytest tests/e2e/`) does not fire against
// TypeScript specs. The Node `test:e2e` script is what gates e2e on main.
export default defineConfig({
  testDir: './e2e',
  // The server keeps a single Game per session; running specs in parallel
  // against one server would let them stomp each other's game state.
  workers: 1,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['list']] : 'list',
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    }
  ],
  // Build the production bundle, then let Flask (server.py) serve it same-origin
  // exactly as Railway does. flask-socketio lives in the uv venv, so run it
  // through uv. Env mirrors the prod single-service setup.
  webServer: {
    command: 'npm run build && uv run python server.py',
    url: BASE_URL,
    timeout: 120_000,
    reuseExistingServer: !process.env.CI,
    env: {
      CQ_HOST: '127.0.0.1',
      CQ_PORT: String(PORT),
      CQ_CORS_ORIGINS: BASE_URL
    }
  }
});
