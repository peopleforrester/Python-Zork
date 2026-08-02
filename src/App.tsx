import { useState, useEffect, useRef } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import { io, Socket } from 'socket.io-client';
import GameMap from './components/GameMap';
import { LineMirror, remainderFor } from './completion';

import 'xterm/css/xterm.css';

function App() {
  const [showMap, setShowMap] = useState(false);
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isGameRunning, setIsGameRunning] = useState(false);
  
  const terminalRef = useRef<HTMLDivElement>(null);
  const terminalInstance = useRef<Terminal | null>(null);
  const fitAddon = useRef<FitAddon>(new FitAddon());
  // The single mirror of the server's line buffer. It was previously a ref
  // plus a closure variable updated in different places, and the two drifted.
  const pending = useRef<LineMirror>(new LineMirror());

  // Refs mirror socket/isGameRunning so the terminal's onData handler (bound
  // once at terminal creation) always reads current values instead of a
  // stale closure.
  const socketRef = useRef<Socket | null>(null);
  const isGameRunningRef = useRef(false);
  useEffect(() => {
    socketRef.current = socket;
  }, [socket]);

  // Completion results arrive out of band; a single match completes the word,
  // several are listed the way a shell does.
  useEffect(() => {
    if (!socket) return;
    const onCompletions = (payload: { matches?: string[] }) => {
      const term = terminalInstance.current;
      const matches = payload?.matches ?? [];
      if (!term || matches.length === 0) return;
      if (matches.length === 1) {
        // The player has already typed a prefix, and the server's buffer
        // holds it, so send only the remainder. Sending the whole match
        // produced 'solsolve'.
        const remainder = remainderFor(pending.current.value, matches[0]);
        if (remainder) {
          // Do not write locally: the server echoes printable input back, the
          // same as ordinary typing. Writing here too rendered 'solveve'.
          socketRef.current?.emit('terminal_input', { input: remainder });
          pending.current.accept(remainder);
        }
      } else {
        // Several matches: list them the way a shell does. This is client-only
        // output, so writing directly is correct here.
        term.write('\r\n' + matches.join('  ') + '\r\n> ' + pending.current.value);
      }
    };
    socket.on('completions', onCompletions);
    return () => {
      socket.off('completions', onCompletions);
    };
  }, [socket]);
  useEffect(() => {
    isGameRunningRef.current = isGameRunning;
  }, [isGameRunning]);

  // Initialize socket connection
  useEffect(() => {
    // Dev: the Vite page on :5173 talks to the Flask server on :5000.
    // Prod (Railway): Flask serves the page itself, so same origin.
    const newSocket = io(import.meta.env.PROD ? window.location.origin : 'http://localhost:5000');
    
    newSocket.on('connect', () => {
      console.log('Socket connected');
      setIsConnected(true);
    });
    
    newSocket.on('disconnect', () => {
      console.log('Socket disconnected');
      setIsConnected(false);
      setIsGameRunning(false);
      // The server discards this session's buffer on disconnect.
      pending.current.reset();
    });
    
    newSocket.on('game_started', () => {
      console.log('Game started');
      setIsGameRunning(true);
    });
    
    newSocket.on('game_ended', (data: { victory: boolean }) => {
      console.log('Game ended. Victory:', data.victory);
      setIsGameRunning(false);
    });
    
    setSocket(newSocket);

    return () => {
      // Remove listeners before disconnecting: under StrictMode's dev
      // double-mount, the first socket's disconnect event otherwise fires
      // after the second socket has connected and stomps isGameRunning /
      // isConnected back to false.
      newSocket.removeAllListeners();
      newSocket.disconnect();
    };
  }, []);
  
  // Initialize terminal once on mount. Deps stay empty: the previous
  // [socket, isGameRunning] deps made the cleanup dispose the terminal on
  // the first socket-state change, and the guard on terminalInstance.current
  // then blocked recreation — leaving no terminal at all. onData reads the
  // refs above so it never goes stale.
  useEffect(() => {
    if (!terminalRef.current || terminalInstance.current) return;

    // Create terminal instance
    const term = new Terminal({
      fontFamily: 'monospace',
      fontSize: 14,
      theme: {
        background: '#1e1e1e',
        foreground: '#f0f0f0',
        cursor: '#f0f0f0',
        cursorAccent: '#1e1e1e',
        selectionBackground: '#4444dd',
        selectionForeground: '#ffffff'
      },
      cursorBlink: true,
      cursorStyle: 'block',
      convertEol: true
    });

    // Add addons
    term.loadAddon(fitAddon.current);
    term.loadAddon(new WebLinksAddon());

    // Open terminal in the container
    term.open(terminalRef.current);
    fitAddon.current.fit();

    // Handle user input. The mirror of the line being typed lives in
    // completion.ts, where it is tested against server.py's own rules; a paste
    // arrives as one multi-character event, so it must be walked per character.
    term.onData((data) => {
      if (data === '\t') {
        // Tab never reaches the game: it asks for completions instead.
        socketRef.current?.emit('complete', { line: pending.current.value });
        return;
      }
      pending.current.push(data);
      const activeSocket = socketRef.current;
      if (activeSocket && isGameRunningRef.current) {
        activeSocket.emit('terminal_input', { input: data });
      }
    });

    // Handle window resize. The old 'resize' socket event is gone (the server
    // no longer runs a PTY), but the server does need the height so it can page
    // long output rather than dumping past the top of the viewport.
    const handleResize = () => {
      fitAddon.current?.fit();
      const rows = terminalInstance.current?.rows;
      if (rows && socketRef.current) {
        socketRef.current.emit('terminal_size', { rows });
      }
    };

    window.addEventListener('resize', handleResize);

    // Store terminal instance
    terminalInstance.current = term;

    return () => {
      window.removeEventListener('resize', handleResize);
      term.dispose();
      terminalInstance.current = null;
    };
  }, []);
  
  // Handle terminal output
  useEffect(() => {
    if (!socket || !terminalInstance.current) return;
    
    const handleTerminalOutput = (data: { output: string }) => {
      if (terminalInstance.current) {
        terminalInstance.current.write(data.output);
      }
    };
    
    socket.on('terminal_output', handleTerminalOutput);
    
    return () => {
      socket.off('terminal_output', handleTerminalOutput);
    };
  }, [socket]);
  
  // Start game
  const startGame = () => {
    if (socket && isConnected) {
      if (terminalInstance.current) {
        terminalInstance.current.clear();
      }
      // start_game resets the server's buffer, so the mirror follows.
      pending.current.reset();
      // Report the viewport height up front so the first long output pages.
      const rows = terminalInstance.current?.rows;
      if (rows) {
        socket.emit('terminal_size', { rows });
      }
      socket.emit('start_game');
    }
  };
  
  // Toggle map visibility
  const toggleMap = () => {
    setShowMap(!showMap);
  };
  
  return (
    <div className="terminal-container">
      <div className="controls">
        <button onClick={startGame} disabled={!isConnected || isGameRunning}>
          {isGameRunning ? 'Game Running' : 'Start Game'}
        </button>
        <button onClick={toggleMap}>
          {showMap ? 'Hide Map' : 'Show Map'}
        </button>
      </div>
      
      <div ref={terminalRef} className="terminal" />
      
      {showMap && <GameMap socket={socket} />}
    </div>
  );
}

export default App;