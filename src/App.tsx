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
    
    newSocket.on('game_ended', (data) => {
      console.log('Game ended with exit code:', data.exit_code);
      setIsGameRunning(false);
    });
    
    setSocket(newSocket);
    
    return () => {
      newSocket.disconnect();
    };
  }, []);
  
  // Initialize terminal
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
      if (socket && isGameRunning) {
        socket.emit('terminal_input', { input: data });
      }
    });
    
    // Handle window resize
    const handleResize = () => {
      if (fitAddon.current) {
        fitAddon.current.fit();
        if (socket && isGameRunning) {
          const { rows, cols } = term;
          socket.emit('resize', { rows, cols });
        }
      }
    };
    
    window.addEventListener('resize', handleResize);
    
    // Store terminal instance
    terminalInstance.current = term;
    
    return () => {
      window.removeEventListener('resize', handleResize);
      term.dispose();
    };
  }, [socket, isGameRunning]);
  
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