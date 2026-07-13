// ABOUTME: End-to-end play-through of the microquiz game against a served build.
// ABOUTME: Codifies the manual browser checks: start, solve each answer kind, map.

import { expect, Page, test } from '@playwright/test';

/**
 * Drive the xterm terminal the way a player does: focus it, type a line, and
 * press Enter. The server buffers keystrokes and flushes on Enter, so this
 * mirrors real input rather than emitting synthetic socket events.
 */
async function sendCommand(page: Page, command: string): Promise<void> {
  await page.locator('.xterm').click();
  await page.keyboard.type(command);
  await page.keyboard.press('Enter');
}

/** The rendered terminal buffer, for text assertions. */
function terminal(page: Page) {
  return page.locator('.xterm-rows');
}

/** Start a fresh game and wait for the world to be ready. */
async function startGame(page: Page): Promise<void> {
  await page.goto('/');
  const startButton = page.getByRole('button', { name: 'Start Game' });
  await expect(startButton).toBeEnabled();
  await startButton.click();
  // The button flips to "Game Running" once the server confirms game_started.
  await expect(page.getByRole('button', { name: 'Game Running' })).toBeVisible();
  // Anchor on a fresh room render at the bottom of the buffer rather than the
  // long welcome banner, which xterm virtualizes out of the visible rows.
  await sendCommand(page, 'look');
  await expect(terminal(page)).toContainText('CPU Package');
}

/**
 * Navigate a sequence of single-direction moves, asserting the destination
 * banner appears before moving on so each step is synchronized.
 */
async function walk(page: Page, steps: Array<[string, string]>): Promise<void> {
  for (const [direction, expectedRoom] of steps) {
    await sendCommand(page, direction);
    await expect(terminal(page)).toContainText(expectedRoom);
  }
}

test.describe('microquiz play-through', () => {
  test('solves a puzzle of each answer kind', async ({ page }) => {
    await startGame(page);

    // SEQUENCE (cache): CPU Package -> Core 1 -> Core 1 L1 Cache.
    await walk(page, [
      ['n', 'Core 1'],
      ['s', 'Core 1 L1 Cache']
    ]);
    await sendCommand(page, 'solve');
    await expect(terminal(page)).toContainText('predict hit/miss');
    await sendCommand(page, 'answer M M M M H M H');
    await expect(terminal(page)).toContainText('Correct!');

    // NUMBER (pipeline): back to Core 1, up to the Control Unit (difficulty-1,
    // ungated), which asks for a cycle count.
    await walk(page, [
      ['n', 'Core 1'],
      ['n', 'Control Unit']
    ]);
    await sendCommand(page, 'solve');
    await expect(terminal(page)).toContainText('cycles');
    await sendCommand(page, 'answer 7');
    await expect(terminal(page)).toContainText('Correct!');

    // CHOICE (signature): route down to the BIOS and name the infection.
    await walk(page, [
      ['s', 'Core 1'],
      ['se', 'L2 Cache'],
      ['s', 'L3 Cache'],
      ['n', 'CPU Package'],
      ['d', 'Platform Controller Hub'],
      ['w', 'BIOS']
    ]);
    await sendCommand(page, 'solve');
    await expect(terminal(page)).toContainText('Signature scan');
    await sendCommand(page, 'answer boot_sector_virus');
    await expect(terminal(page)).toContainText('Correct!');
  });

  test('updates the map badge when a puzzle is solved', async ({ page }) => {
    await startGame(page);
    await page.getByRole('button', { name: 'Show Map' }).click();

    const mapTitle = page.locator('.map-title');
    await expect(mapTitle).toContainText('0/28 puzzles');

    await walk(page, [
      ['n', 'Core 1'],
      ['s', 'Core 1 L1 Cache']
    ]);
    await sendCommand(page, 'solve');
    await sendCommand(page, 'answer M M M M H M H');
    await expect(terminal(page)).toContainText('Correct!');

    // The header total ticks up. Core 1 L1 Cache has two puzzles, so solving
    // one flips that node to the partial (started) class, not solved.
    await expect(mapTitle).toContainText('1/28 puzzles');
    await expect(page.locator('.node.puzzles-partial')).toHaveCount(1);
    await expect(page.locator('.node.puzzles-solved')).toHaveCount(0);
  });

  test('rejects a wrong answer without marking the puzzle solved', async ({ page }) => {
    await startGame(page);
    await walk(page, [
      ['n', 'Core 1'],
      ['s', 'Core 1 L1 Cache']
    ]);
    await sendCommand(page, 'solve');
    await expect(terminal(page)).toContainText('predict hit/miss');
    // Flip the last token: 7 of 7 -> one wrong.
    await sendCommand(page, 'answer M M M M H M M');
    await expect(terminal(page)).toContainText('Not quite');
    await expect(terminal(page)).not.toContainText('Correct!');
  });
});
