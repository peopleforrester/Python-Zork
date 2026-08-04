// ABOUTME: Unit tests for App.tsx's socket wiring and keystroke forwarding.
// ABOUTME: xterm and socket.io are mocked; this covers App's own logic, not theirs.

import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

/**
 * Handlers registered on the mock socket, keyed by event, so a test can fire
 * `connect` or `terminal_output` the way the server would.
 */
const handlers = new Map<string, (payload?: unknown) => void>();
const emit = vi.fn();
const disconnect = vi.fn();
const removeAllListeners = vi.fn();

const socket = {
  on: vi.fn((event: string, cb: (payload?: unknown) => void) => {
    handlers.set(event, cb);
  }),
  off: vi.fn((event: string) => handlers.delete(event)),
  emit,
  disconnect,
  removeAllListeners
};

vi.mock('socket.io-client', () => ({
  io: () => socket,
  Socket: class {}
}));

/**
 * xterm is mocked rather than mounted. jsdom has no layout, so a real Terminal
 * cannot fit or render, and none of what is worth testing here belongs to
 * xterm anyway: the subject is which bytes App forwards and when.
 */
const written: string[] = [];
let onData: ((data: string) => void) | null = null;
const clear = vi.fn();
const dispose = vi.fn();

vi.mock('xterm', () => ({
  Terminal: class {
    rows = 24;
    write = (text: string) => written.push(text);
    clear = clear;
    dispose = dispose;
    open = vi.fn();
    loadAddon = vi.fn();
    onData = (cb: (data: string) => void) => {
      onData = cb;
    };
  }
}));

vi.mock('xterm-addon-fit', () => ({
  FitAddon: class {
    fit = vi.fn();
    activate = vi.fn();
    dispose = vi.fn();
  }
}));

vi.mock('xterm-addon-web-links', () => ({
  WebLinksAddon: class {
    activate = vi.fn();
    dispose = vi.fn();
  }
}));

vi.mock('xterm/css/xterm.css', () => ({}));

// Imported after the mocks so App picks them up.
const { default: App } = await import('./App');

/** Deliver a chunk to the terminal's data handler the way xterm would. */
function type(data: string) {
  act(() => {
    onData?.(data);
  });
}

/** Fire a socket event the way the server would. */
function server(event: string, payload?: unknown) {
  act(() => {
    handlers.get(event)?.(payload);
  });
}

/** Connect and start a game, which is the precondition for input to flow. */
function startedGame() {
  render(<App />);
  server('connect');
  server('game_started');
}

const inputs = () =>
  emit.mock.calls.filter(([event]) => event === 'terminal_input').map(([, arg]) => arg.input);

describe('App', () => {
  beforeEach(() => {
    handlers.clear();
    written.length = 0;
    onData = null;
    vi.clearAllMocks();
  });

  afterEach(() => {
    handlers.clear();
  });

  describe('connection state', () => {
    it('disables Start Game until the socket connects', () => {
      render(<App />);
      expect(screen.getByRole('button', { name: /start game/i })).toBeDisabled();
    });

    it('enables Start Game once connected', () => {
      render(<App />);
      server('connect');
      expect(screen.getByRole('button', { name: /start game/i })).toBeEnabled();
    });

    it('shows the game as running after game_started', () => {
      startedGame();
      expect(screen.getByRole('button', { name: /game running/i })).toBeInTheDocument();
    });

    it('stops reporting a running game when the socket drops', () => {
      startedGame();
      server('disconnect');
      expect(screen.getByRole('button', { name: /start game/i })).toBeInTheDocument();
    });

    it('stops reporting a running game once it ends', () => {
      startedGame();
      server('game_ended', { victory: true });
      expect(screen.getByRole('button', { name: /start game/i })).toBeInTheDocument();
    });
  });

  describe('starting a game', () => {
    it('emits start_game when the button is clicked', async () => {
      render(<App />);
      server('connect');
      await userEvent.click(screen.getByRole('button', { name: /start game/i }));
      // Carries the browser's save key, which scopes saves server-side.
      expect(emit).toHaveBeenCalledWith(
        'start_game', expect.objectContaining({ save_key: expect.any(String) })
      );
    });

    it('reports the viewport height first, so the first long output pages', async () => {
      render(<App />);
      server('connect');
      await userEvent.click(screen.getByRole('button', { name: /start game/i }));
      expect(emit).toHaveBeenCalledWith('terminal_size', { rows: 24 });
    });

    it('clears the terminal so the previous game does not bleed through', async () => {
      render(<App />);
      server('connect');
      await userEvent.click(screen.getByRole('button', { name: /start game/i }));
      expect(clear).toHaveBeenCalled();
    });
  });

  describe('forwarding keystrokes', () => {
    it('sends typed characters to the server', () => {
      startedGame();
      type('l');
      expect(inputs()).toContain('l');
    });

    it('sends nothing before a game is running', () => {
      render(<App />);
      server('connect');
      type('l');
      expect(inputs()).toEqual([]);
    });

    it('does not forward Tab, which asks for completions instead', () => {
      startedGame();
      type('\t');
      expect(inputs()).toEqual([]);
    });

    it('asks the server to complete what has been typed', () => {
      startedGame();
      for (const ch of 'sol') type(ch);
      type('\t');
      expect(emit).toHaveBeenCalledWith('complete', { line: 'sol' });
    });

    it('completes against an empty line after Ctrl-C, which the server also clears', () => {
      // The mirror used to keep 'sol' here, so Tab completed against text the
      // server had already discarded and inserted the tail onto a blank line.
      startedGame();
      for (const ch of 'sol') type(ch);
      type('\x03');
      type('\t');
      expect(emit).toHaveBeenCalledWith('complete', { line: '' });
    });

    it('completes against the tail of a pasted chunk, not the whole chunk', () => {
      // A paste arrives as one event with the newline normalised to CR.
      startedGame();
      type('look\rkno');
      type('\t');
      expect(emit).toHaveBeenCalledWith('complete', { line: 'kno' });
    });

    it('forwards a paste to the server intact', () => {
      startedGame();
      type('look\rkno');
      expect(inputs()).toContain('look\rkno');
    });

    it('forgets the line after Enter, because the server flushes it', () => {
      startedGame();
      for (const ch of 'look') type(ch);
      type('\r');
      type('\t');
      expect(emit).toHaveBeenCalledWith('complete', { line: '' });
    });

    it('forgets the line when the socket drops, since the server drops it too', () => {
      startedGame();
      for (const ch of 'sol') type(ch);
      server('disconnect');
      server('connect');
      server('game_started');
      type('\t');
      expect(emit).toHaveBeenCalledWith('complete', { line: '' });
    });

    it('forgets the line when a new game starts', async () => {
      startedGame();
      for (const ch of 'sol') type(ch);
      server('game_ended', { victory: true });
      await userEvent.click(screen.getByRole('button', { name: /start game/i }));
      server('game_started');
      type('\t');
      expect(emit).toHaveBeenCalledWith('complete', { line: '' });
    });
  });

  describe('applying a completion', () => {
    it('sends only the untyped tail, so the prefix is not doubled', () => {
      startedGame();
      for (const ch of 'sol') type(ch);
      server('completions', { matches: ['solve'] });
      expect(inputs()).toContain('ve');
    });

    it('does not echo the tail locally, since the server echoes it back', () => {
      startedGame();
      for (const ch of 'sol') type(ch);
      written.length = 0;
      server('completions', { matches: ['solve'] });
      expect(written).toEqual([]);
    });

    it('counts an applied completion, so the next Tab sees the whole word', () => {
      startedGame();
      for (const ch of 'sol') type(ch);
      server('completions', { matches: ['solve'] });
      type('\t');
      expect(emit).toHaveBeenCalledWith('complete', { line: 'solve' });
    });

    it('lists several matches the way a shell does', () => {
      startedGame();
      for (const ch of 'so') type(ch);
      server('completions', { matches: ['solve', 'south'] });
      expect(written.join('')).toContain('solve  south');
    });

    it('sends nothing when there is no match', () => {
      startedGame();
      for (const ch of 'sol') type(ch);
      const before = inputs().length;
      server('completions', { matches: [] });
      expect(inputs()).toHaveLength(before);
    });

    it('sends nothing when the word is already complete', () => {
      startedGame();
      for (const ch of 'solve') type(ch);
      const before = inputs().length;
      server('completions', { matches: ['solve'] });
      expect(inputs()).toHaveLength(before);
    });
  });

  describe('terminal output', () => {
    it('writes what the server sends', () => {
      startedGame();
      server('terminal_output', { output: 'MISSION SUCCESSFUL' });
      expect(written.join('')).toContain('MISSION SUCCESSFUL');
    });
  });

  describe('the map', () => {
    it('is hidden until asked for', () => {
      render(<App />);
      expect(screen.getByRole('button', { name: /show map/i })).toBeInTheDocument();
    });

    it('toggles into view', async () => {
      render(<App />);
      await userEvent.click(screen.getByRole('button', { name: /show map/i }));
      expect(screen.getByRole('button', { name: /hide map/i })).toBeInTheDocument();
    });
  });
});
