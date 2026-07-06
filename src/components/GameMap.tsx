// ABOUTME: Live map of the game world driven by the backend `game_state` event.
// ABOUTME: Replaces the previous hardcoded sample with a real snapshot subscription.

import { useEffect, useMemo, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  Edge,
  MiniMap,
  Node,
} from 'reactflow';
import { Socket } from 'socket.io-client';
import 'reactflow/dist/style.css';

/** Wire shape from server.py; keep in sync with Game.snapshot() in Python. */
export interface RoomSnapshot {
  id: string;
  name: string;
  visited: boolean;
  doors: Record<string, string>;
  item_count: number;
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

/**
 * Lay rooms out on a circle, ordered alphabetically by id so the placement is
 * stable across renders. Good enough for a dev map; a real layout would use a
 * force-directed pass driven by the door graph.
 */
function layoutRooms(rooms: RoomSnapshot[]): Map<string, { x: number; y: number }> {
  const sorted = [...rooms].sort((a, b) => a.id.localeCompare(b.id));
  const n = sorted.length;
  const radius = Math.max(280, n * 16);
  const center = { x: radius + 60, y: radius + 60 };
  const positions = new Map<string, { x: number; y: number }>();

  sorted.forEach((room, i) => {
    const angle = (2 * Math.PI * i) / Math.max(n, 1);
    positions.set(room.id, {
      x: center.x + radius * Math.cos(angle),
      y: center.y + radius * Math.sin(angle),
    });
  });

  return positions;
}

function classForRoom(room: RoomSnapshot, isCurrent: boolean): string {
  if (isCurrent) return 'node current';
  if (room.visited) return 'node visited';
  return 'node unvisited';
}

function nodesFor(snapshot: GameSnapshot): Node[] {
  const positions = layoutRooms(snapshot.rooms);
  const currentId = snapshot.player.location_id;

  return snapshot.rooms.map((room) => {
    const pos = positions.get(room.id) ?? { x: 0, y: 0 };
    return {
      id: room.id,
      data: { label: room.name },
      position: pos,
      className: classForRoom(room, room.id === currentId),
    };
  });
}

function edgesFor(snapshot: GameSnapshot): Edge[] {
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
    return { nodes: nodesFor(snapshot), edges: edgesFor(snapshot) };
  }, [snapshot]);

  return (
    <div className="map-container">
      <div className="map-title">
        Computer Architecture Map
        {snapshot && (
          <span className="map-status">
            {' '}· Turn {snapshot.turn} · {snapshot.rooms.filter((r) => r.visited).length}/
            {snapshot.rooms.length} visited
          </span>
        )}
      </div>
      <div className="map-content">
        {snapshot ? (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            // The full ring needs ~0.23 zoom in a ~300px panel; the default
            // minZoom of 0.5 clamps fitView onto the empty middle of the ring.
            minZoom={0.05}
            fitViewOptions={{ padding: 0.1 }}
          >
            <Controls />
            <MiniMap />
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
