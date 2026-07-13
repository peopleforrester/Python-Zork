// ABOUTME: Unit + integration tests for the microquiz map (GameMap.tsx).
// ABOUTME: Covers puzzle-status reduction, labels, edge dedup, and a live render.

import { act, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import GameMap, {
  classForRoom,
  edgesFor,
  puzzleLabel,
  puzzleStatus,
  type GameSnapshot,
  type PuzzleState,
  type RoomSnapshot
} from './GameMap';

/** Build a RoomSnapshot with sensible defaults, overriding what a test cares about. */
function makeRoom(overrides: Partial<RoomSnapshot> = {}): RoomSnapshot {
  const puzzles: PuzzleState = { available: [], solved: [], attempted: [] };
  return {
    id: 'r1',
    name: 'Room One',
    visited: false,
    doors: {},
    item_count: 0,
    puzzles,
    ...overrides
  };
}

/** Build a GameSnapshot around a set of rooms. */
function makeSnapshot(rooms: RoomSnapshot[], currentId: string | null = null): GameSnapshot {
  return {
    turn: 1,
    game_over: false,
    victory: false,
    all_viruses_found: false,
    player: {
      name: 'Player',
      location_id: currentId,
      health: 20,
      max_health: 20,
      items: [],
      knowledge: {}
    },
    rooms,
    found_viruses: [],
    quarantined_viruses: []
  };
}

describe('puzzleStatus', () => {
  it('is "none" when the room has no puzzles', () => {
    expect(puzzleStatus(makeRoom())).toBe('none');
  });

  it('is "available" when puzzles exist but none are solved', () => {
    const room = makeRoom({ puzzles: { available: ['a', 'b'], solved: [], attempted: [] } });
    expect(puzzleStatus(room)).toBe('available');
  });

  it('is "partial" when some but not all puzzles are solved', () => {
    const room = makeRoom({ puzzles: { available: ['a', 'b'], solved: ['a'], attempted: [] } });
    expect(puzzleStatus(room)).toBe('partial');
  });

  it('is "solved" when every bound puzzle is solved', () => {
    const room = makeRoom({ puzzles: { available: ['a', 'b'], solved: ['a', 'b'], attempted: [] } });
    expect(puzzleStatus(room)).toBe('solved');
  });
});

describe('classForRoom', () => {
  it('uses the current-room base class when isCurrent', () => {
    expect(classForRoom(makeRoom(), true)).toBe('node current');
  });

  it('uses visited/unvisited base by visit state and adds no puzzle class when none', () => {
    expect(classForRoom(makeRoom({ visited: true }), false)).toBe('node visited');
    expect(classForRoom(makeRoom({ visited: false }), false)).toBe('node unvisited');
  });

  it('composes the puzzle status onto the visit-state base', () => {
    const room = makeRoom({
      visited: true,
      puzzles: { available: ['a', 'b'], solved: ['a', 'b'], attempted: [] }
    });
    expect(classForRoom(room, false)).toBe('node visited puzzles-solved');
  });
});

describe('puzzleLabel', () => {
  it('returns the bare room name when there are no puzzles', () => {
    render(<>{puzzleLabel(makeRoom({ name: 'Bare Room' }))}</>);
    expect(screen.getByText('Bare Room')).toBeInTheDocument();
    expect(screen.queryByText(/[◆✓]/)).not.toBeInTheDocument();
  });

  it('appends a solved badge with a check glyph', () => {
    const room = makeRoom({
      name: 'Solved Room',
      puzzles: { available: ['a'], solved: ['a'], attempted: [] }
    });
    render(<>{puzzleLabel(room)}</>);
    expect(screen.getByText(/✓ 1\/1/)).toBeInTheDocument();
  });

  it('appends a diamond badge with the solved/total count while in progress', () => {
    const room = makeRoom({
      name: 'Partial Room',
      puzzles: { available: ['a', 'b'], solved: ['a'], attempted: [] }
    });
    render(<>{puzzleLabel(room)}</>);
    expect(screen.getByText(/◆ 1\/2/)).toBeInTheDocument();
  });
});

describe('edgesFor', () => {
  it('de-duplicates bidirectional door pairs into a single edge', () => {
    const snapshot = makeSnapshot([
      makeRoom({ id: 'a', doors: { n: 'b' } }),
      makeRoom({ id: 'b', doors: { s: 'a' } })
    ]);
    const edges = edgesFor(snapshot);
    expect(edges).toHaveLength(1);
    expect(edges[0]).toMatchObject({ source: 'a', target: 'b' });
  });

  it('emits one edge per distinct room pair', () => {
    const snapshot = makeSnapshot([
      makeRoom({ id: 'a', doors: { n: 'b', e: 'c' } }),
      makeRoom({ id: 'b', doors: { s: 'a' } }),
      makeRoom({ id: 'c', doors: { w: 'a' } })
    ]);
    expect(edgesFor(snapshot)).toHaveLength(2);
  });
});

/**
 * Minimal socket double: GameMap only calls on/off/emit and reacts to the
 * 'game_state' event. `fire` lets a test deliver a snapshot as the server would.
 */
function makeMockSocket() {
  const handlers = new Map<string, (data: unknown) => void>();
  return {
    on: vi.fn((event: string, cb: (data: unknown) => void) => {
      handlers.set(event, cb);
    }),
    off: vi.fn((event: string) => {
      handlers.delete(event);
    }),
    emit: vi.fn(),
    fire(event: string, data: unknown) {
      handlers.get(event)?.(data);
    }
  };
}

describe('<GameMap />', () => {
  it('shows the placeholder until a snapshot arrives', () => {
    const socket = makeMockSocket();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    render(<GameMap socket={socket as any} />);
    expect(screen.getByText(/Waiting for game state/i)).toBeInTheDocument();
    // It subscribes and asks the server for the current state on mount.
    expect(socket.on).toHaveBeenCalledWith('game_state', expect.any(Function));
    expect(socket.emit).toHaveBeenCalledWith('query_state');
  });

  it('renders the header totals and legend once a snapshot is delivered', () => {
    const socket = makeMockSocket();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    render(<GameMap socket={socket as any} />);

    const rooms = [
      makeRoom({
        id: 'core1_l1',
        name: 'Core 1 L1 Cache',
        visited: true,
        puzzles: { available: ['p1', 'p2'], solved: ['p1', 'p2'], attempted: [] }
      }),
      makeRoom({
        id: 'bios',
        name: 'BIOS',
        visited: true,
        puzzles: { available: ['p3', 'p4'], solved: ['p3'], attempted: [] }
      }),
      makeRoom({ id: 'core1', name: 'Core 1', visited: false })
    ];
    act(() => {
      socket.fire('game_state', makeSnapshot(rooms, 'core1_l1'));
    });

    // Three solved of four available puzzles across two visited rooms.
    expect(screen.getByText(/3\/4 puzzles/)).toBeInTheDocument();
    expect(screen.getByText(/2\/3 visited/)).toBeInTheDocument();
    // Legend appears whenever the world has any puzzles.
    expect(screen.getByText(/available/)).toBeInTheDocument();
    expect(screen.getByText(/solved/)).toBeInTheDocument();
    expect(screen.queryByText(/Waiting for game state/i)).not.toBeInTheDocument();
  });
});
