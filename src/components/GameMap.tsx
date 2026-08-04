// ABOUTME: Live map of the game world driven by the backend `game_state` event.
// ABOUTME: Replaces the previous hardcoded sample with a real snapshot subscription.

import { ReactNode, useEffect, useMemo, useRef, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  Edge,
  Node,
} from 'reactflow';
import { Socket } from 'socket.io-client';
import 'reactflow/dist/style.css';

/** Per-room puzzle progress, emitted by Game.snapshot() since the microquiz. */
export interface PuzzleState {
  available: string[];
  solved: string[];
  attempted: string[];
}

/** Wire shape from server.py; keep in sync with Game.snapshot() in Python. */
export interface RoomSnapshot {
  id: string;
  name: string;
  visited: boolean;
  doors: Record<string, string>;
  /** Canonical grid placement from the server, shared with the ASCII map. */
  grid?: { row: number; col: number };
  item_count: number;
  puzzles: PuzzleState;
}

type PuzzleStatus = 'none' | 'available' | 'partial' | 'solved';

/**
 * Reduce a room's puzzle block to one status the map can color by:
 *   none      - no puzzles bound here
 *   available - has puzzles, none solved yet
 *   partial   - some but not all solved
 *   solved    - every bound puzzle solved
 */
export function puzzleStatus(room: RoomSnapshot): PuzzleStatus {
  const total = room.puzzles?.available.length ?? 0;
  if (total === 0) return 'none';
  const solved = room.puzzles.solved.length;
  if (solved >= total) return 'solved';
  if (solved > 0) return 'partial';
  return 'available';
}

export interface GameSnapshot {
  turn: number;
  game_over: boolean;
  victory: boolean;
  all_viruses_found: boolean;
  player: {
    name: string;
    location_id: string | null;
    health: number;
    max_health: number;
    items: string[];
    knowledge: Record<string, number>;
  };
  rooms: RoomSnapshot[];
  found_viruses: string[];
  quarantined_viruses: string[];
}

interface GameMapProps {
  socket: Socket | null;
}

/** Grid cell to pixels. Wide enough that a full room name fits. */
const COL_PX = 104;
const ROW_PX = 52;

/**
 * Place rooms at their architectural coordinates.
 *
 * The server ships a `grid` per room, the same hand-laid placement the ASCII
 * map uses, so each core sits beside its own caches, the DIMMs stack, and the
 * PCIe slots run in a column. Corridors then read as short local hops between
 * neighbours, which is how the player actually moves.
 *
 * This replaced a circle ordered alphabetically by room id. That ordering had
 * nothing to do with the topology, so unrelated rooms ended up adjacent and
 * every corridor was drawn as a chord across the middle of the ring.
 */
export function layoutRooms(rooms: RoomSnapshot[]): Map<string, { x: number; y: number }> {
  const placed = rooms.filter(r => r.grid);
  if (placed.length === 0) return layoutRingFallback(rooms);

  const minRow = Math.min(...placed.map(r => r.grid!.row));
  const minCol = Math.min(...placed.map(r => r.grid!.col));

  const positions = new Map<string, { x: number; y: number }>();
  for (const room of rooms) {
    positions.set(room.id, room.grid
      ? { x: (room.grid.col - minCol) * COL_PX, y: (room.grid.row - minRow) * ROW_PX }
      : { x: 0, y: 0 });
  }
  return positions;
}

/**
 * The old ring, kept only for a snapshot with no `grid` (an older server).
 * Never the default: it is unreadable at 35 nodes.
 */
export function layoutRingFallback(rooms: RoomSnapshot[]): Map<string, { x: number; y: number }> {
  const sorted = [...rooms].sort((a, b) => a.id.localeCompare(b.id));
  const radius = Math.max(280, sorted.length * 16);
  const positions = new Map<string, { x: number; y: number }>();
  sorted.forEach((room, i) => {
    const angle = (2 * Math.PI * i) / Math.max(sorted.length, 1);
    positions.set(room.id, {
      x: radius + 60 + radius * Math.cos(angle),
      y: radius + 60 + radius * Math.sin(angle),
    });
  });
  return positions;
}

export function classForRoom(room: RoomSnapshot, isCurrent: boolean): string {
  // Base background comes from visit state; puzzle status adds an outline so
  // the two axes (where have I been, what's left to solve) read independently.
  const base = isCurrent ? 'node current' : room.visited ? 'node visited' : 'node unvisited';
  const status = puzzleStatus(room);
  return status === 'none' ? base : `${base} puzzles-${status}`;
}

/** Compact solved/total badge for puzzle rooms, e.g. "◆ 1/2". */
export function puzzleLabel(room: RoomSnapshot): ReactNode {
  const status = puzzleStatus(room);
  if (status === 'none') return room.name;
  const total = room.puzzles.available.length;
  const solved = room.puzzles.solved.length;
  const glyph = status === 'solved' ? '✓' : '◆';
  return (
    <span>
      {room.name}
      <span className={`puzzle-badge badge-${status}`}>
        {' '}
        {glyph} {solved}/{total}
      </span>
    </span>
  );
}

function nodesFor(snapshot: GameSnapshot): Node[] {
  const positions = layoutRooms(snapshot.rooms);
  const currentId = snapshot.player.location_id;

  return snapshot.rooms.map((room) => {
    const pos = positions.get(room.id) ?? { x: 0, y: 0 };
    return {
      id: room.id,
      data: { label: puzzleLabel(room) },
      position: pos,
      className: classForRoom(room, room.id === currentId),
    };
  });
}

export function edgesFor(snapshot: GameSnapshot): Edge[] {
  const edges: Edge[] = [];
  const seen = new Set<string>();

  for (const room of snapshot.rooms) {
    for (const [, destId] of Object.entries(room.doors)) {
      // De-duplicate bidirectional pairs so we don't render two edges between
      // every pair of rooms.
      const key = [room.id, destId].sort().join('|');
      if (seen.has(key)) continue;
      seen.add(key);

      edges.push({
        id: `${room.id}->${destId}`,
        source: room.id,
        target: destId,
        animated: false,
      });
    }
  }
  return edges;
}

function GameMap({ socket }: GameMapProps) {
  const [snapshot, setSnapshot] = useState<GameSnapshot | null>(null);
  // The panel was a fixed 300px box, which put 35 nodes in roughly 50px each
  // and made the labels unreadable. Expanded fills most of the window, which is
  // the mode that matters when this is on a projector.
  const [expanded, setExpanded] = useState(false);
  // ReactFlow fits the view once on init and does not re-fit when its container
  // resizes, so expanding left the graph at the docked zoom, clustered in a
  // corner of a much larger box.
  const flowRef = useRef<{
    fitView: (o?: object) => void;
    setCenter?: (x: number, y: number, o?: object) => void;
  } | null>(null);
  const positionsRef = useRef<Map<string, { x: number; y: number }>>(new Map());
  useEffect(() => {
    const id = window.setTimeout(() => {
      // Centre on the room the player is in, at a zoom where the labels are
      // actually readable. Fitting all 35 nodes crushed the map to ~0.24 zoom
      // and the names became illegible, which defeats the point of the map.
      // The Controls' fit button still shows the whole architecture on demand.
      const here = snapshot?.player.location_id;
      const at = here ? positionsRef.current.get(here) : undefined;
      if (at && flowRef.current?.setCenter) {
        flowRef.current.setCenter(at.x + 66, at.y + 20, { zoom: 0.9, duration: 200 });
      } else {
        flowRef.current?.fitView({ padding: 0.12 });
      }
    }, 180);   // after the width/height transition settles
    return () => window.clearTimeout(id);
  }, [expanded, snapshot?.player.location_id]);

  useEffect(() => {
    if (!socket) return;

    const handleState = (data: GameSnapshot) => {
      setSnapshot(data);
    };

    socket.on('game_state', handleState);
    // Ask the server for the current state on mount so we don't have to
    // wait for the next command.
    socket.emit('query_state');

    return () => {
      socket.off('game_state', handleState);
    };
  }, [socket]);

  const { nodes, edges } = useMemo(() => {
    if (!snapshot) return { nodes: [] as Node[], edges: [] as Edge[] };
    positionsRef.current = layoutRooms(snapshot.rooms);
    return { nodes: nodesFor(snapshot), edges: edgesFor(snapshot) };
  }, [snapshot]);

  // Game-wide puzzle totals across every room, for the header summary.
  const { solvedCount, puzzleCount } = useMemo(() => {
    if (!snapshot) return { solvedCount: 0, puzzleCount: 0 };
    let solved = 0;
    let total = 0;
    for (const room of snapshot.rooms) {
      total += room.puzzles?.available.length ?? 0;
      solved += room.puzzles?.solved.length ?? 0;
    }
    return { solvedCount: solved, puzzleCount: total };
  }, [snapshot]);

  return (
    <div className={`map-container${expanded ? ' map-expanded' : ''}`}>
      <div className="map-title">
        <button
          type="button"
          className="map-expand"
          onClick={() => setExpanded(e => !e)}
          aria-expanded={expanded}
          aria-label={expanded ? 'Shrink map' : 'Expand map'}
          title={expanded ? 'Shrink map' : 'Expand map to fill the window'}
        >
          {expanded ? '⤡' : '⤢'}
        </button>
        Computer Architecture Map
        {snapshot && (
          <span className="map-status">
            {' '}· Turn {snapshot.turn} · {snapshot.rooms.filter((r) => r.visited).length}/
            {snapshot.rooms.length} visited · {solvedCount}/{puzzleCount} puzzles
          </span>
        )}
      </div>
      {snapshot && puzzleCount > 0 && (
        <div className="map-legend">
          <span className="legend-item legend-available">◆ available</span>
          <span className="legend-item legend-partial">◆ started</span>
          <span className="legend-item legend-solved">✓ solved</span>
        </div>
      )}
      <div className="map-content">
        {snapshot ? (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            onInit={(instance) => { flowRef.current = instance; }}
            // The full ring needs ~0.23 zoom in a ~300px panel; the default
            // minZoom of 0.5 clamps fitView onto the empty middle of the ring.
            minZoom={0.05}
            fitViewOptions={{ padding: 0.1 }}
          >
            {/* No MiniMap: the panel is ~300px and fitView already shows the
                whole ring, so a minimap of an already-visible graph bought
                nothing while covering ~48% of the panel in opaque white. */}
            <Controls />
            <Background gap={12} size={1} />
          </ReactFlow>
        ) : (
          <div className="map-placeholder">
            Waiting for game state. Click <strong>Start Game</strong> if you haven&apos;t already.
          </div>
        )}
      </div>
    </div>
  );
}

export default GameMap;
