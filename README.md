# KodeKloud Computer Quest

An educational text-based adventure game that teaches computer architecture concepts.

![KodeKloud Computer Quest](https://img.shields.io/badge/KodeKloud-Computer%20Quest-blue)
![Python Version](https://img.shields.io/badge/python-3.10%2B-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## Overview

KodeKloud Computer Quest is an interactive text adventure where players navigate through a computer system, learning about various hardware components while searching for and neutralizing viruses. The game simulates the internals of a modern computer, from the CPU cores to memory, storage, and peripherals.

Play the hosted demo at https://python-zork-production.up.railway.app (click Start Game, then Show Map).

## Features

- Detailed simulation of computer architecture components
- Exploration-based learning of computer hardware concepts
- Virus hunting gameplay that teaches security concepts
- Progressive knowledge system that tracks player learning
- Mini-games that demonstrate CPU pipelines and memory hierarchies
- Persistent save/load: JSON snapshots under `~/.kodekloud_quest/saves/`
- Enhanced UI with improved visuals and readability
- Web-based terminal interface for running the game in a browser

## Web Interface Setup

The game now includes a web interface using TypeScript, React, ReactFlow, and Vite, allowing you to play the game directly in a browser.

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher (Vite 5 requirement)
- npm or yarn

### Installation

```bash
# Clone the repository
git clone https://github.com/peopleforrester/Python-Zork.git
cd Python-Zork

# Install Python dependencies (uv handles the venv automatically)
uv sync --dev

# Install Node.js dependencies
npm install
```

### Running the Web Interface

The web interface requires both a backend server and a frontend development server:

```bash
# Start the backend server (in one terminal)
npm run api

# Start the frontend development server (in another terminal)
npm run dev
```

Then open your browser to http://localhost:5173 to play the game.

### Server Environment Variables

The Flask backend reads its configuration from environment variables. Defaults are conservative: the server binds to `127.0.0.1` and rejects all browsers except `http://localhost:5173`.

| Variable | Default | Notes |
|---|---|---|
| `CQ_HOST` | `127.0.0.1` | Bind address. Do not change unless you understand the security implications below. |
| `CQ_PORT` | `5000` | TCP port. |
| `CQ_CORS_ORIGINS` | `http://localhost:5173` | Comma-separated list of allowed browser origins. |
| `CQ_DEBUG` | `false` | Set to `1`/`true`/`yes` to enable Flask debug mode. Off in production. |

### Security Caveat

The game runs in-process in the Flask server. Each Socket.IO connection gets its own isolated Game instance, and player input only reaches the game's command parser. There is no authentication: anyone who can reach the server can play (and only play). Fine for a demo deployment; add auth before putting anything sensitive behind it.

### Building for Production

```bash
# Build the frontend
npm run build

# Serve the built files
npm run serve
```

## Terminal-Only Mode

You can still run the game directly in a terminal without the web interface:

```bash
# Run the game in terminal mode
python main.py
```

## Game Commands

The game supports a wide range of commands, including:

- Movement: `north` (n), `south` (s), `east` (e), `west` (w), etc.
- Exploration: `look` (l), `map` (m), `motherboard` (mb)
- Inventory: `inventory` (i), `take` (t), `drop` (d)
- Security: `scan` (sc), `analyze` (a), `quarantine` (q)
- Information: `help` (h), `about`, `knowledge` (k)
- Educational: `visualize` (v), `simulate` (sim)

Type `help` in-game for a complete list of commands.

## Project Structure

The project now includes both the original Python game and a web interface:

```
.
├── computerquest/       # Main Python package
│   ├── models/          # Data models (Component, Player)
│   ├── world/           # World generation (Architecture)
│   ├── mechanics/       # Game mechanics (Progress, Minigames)
│   └── utils/           # Utility functions
├── data/                # Game data files
├── tests/               # Unit tests for Python code
├── src/                 # React frontend
│   ├── components/      # React components
│   └── ...              # Other frontend files
├── server.py            # Flask backend for web interface
├── main.py              # Entry point for terminal mode
└── package.json         # Node.js dependencies and scripts
```

## Web Interface Architecture

The web interface consists of:

1. **Backend**:
   - Flask server with Socket.IO for real-time communication
   - Runs the Game in-process, one instance per connected session
   - Buffers keystrokes server-side and feeds whole command lines to the game
   - Emits terminal output plus a structured game_state snapshot after every command

2. **Frontend**:
   - React application with TypeScript
   - xterm.js for terminal emulation
   - ReactFlow for the interactive map visualization
   - Socket.IO client for communication with the backend

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Install all dependencies
4. Make your changes
5. Test your changes thoroughly
6. Commit your changes
7. Push to the branch
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.