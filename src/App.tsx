import { useState, useEffect, useRef } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import { io, Socket } from 'socket.io-client';
import GameMap from './components/GameMap';

import 'xterm/css/xterm.css';

function App() {
  const [showMap, setShowMap] = useState(false);
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isGameRunning, setIsGameRunning] = useState(false);
  
  const terminalRef = useRef<HTMLDivElement>(null);
  const terminalInstance = useRef<Terminal | null>(null);
  const fitAddon = useRef<FitAddon>(new FitAddon());

  // Refs mirror socket/isGameRunning so the terminal's onData handler (bound
  // once at terminal creation) always reads current values instead of a
  // stale closure.
  const socketRef = useRef<Socket | null>(null);
  const isGameRunningRef = useRef(false);
  useEffect(() => {
    socketRef.current = socket;
  }, [socket]);
  useEffect(() => {
    isGameRunningRef.current = isGameRunning;
  }, [isGameRunning]);

  // Initialize socket connection
  useEffect(() => {
    const newSocket = io('http://localhost:5000');
    
    newSocket.on('connect', () => {
      console.log('Socket connected');
      setIsConnected(true);
    });
    
    newSocket.on('disconnect', () => {
      console.log('Socket disconnected');
      setIsConnected(false);
      setIsGameRunning(false);
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

    // Handle user input
    term.onData((data) => {
      const activeSocket = socketRef.current;
      if (activeSocket && isGameRunningRef.current) {
        activeSocket.emit('terminal_input', { input: data });
      }
    });

    // Handle window resize. The old 'resize' socket event is gone — the
    // server no longer runs a PTY, so there is nothing to resize remotely.
    const handleResize = () => {
      fitAddon.current?.fit();
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