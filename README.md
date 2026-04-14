# 🃏 MUD Solitaire — The Viral Demo

A text-based MUD (Multi-User Dungeon) where an AI agent plays Klondike solitaire — and a **real browser window** mirrors every move in real time.

**Left screen:** Text MUD terminal. An agent types commands. Cards are rendered as Unicode art in a box-drawing frame.

**Right screen:** A full visual solitaire game running in Chrome. Every card flip, every move, every auto-play is reflected live.

Then the human walks away and says *"your turn"* — and the AI takes over, playing the real game through text commands while the browser window shows it happening live.

**This is not a simulation.** The MUD IS playing the game.

---

## Table of Contents

- [Overview](#overview)
- [How to Play](#how-to-play)
- [Architecture](#architecture)
- [Installation](#installation)
- [MUD Commands](#mud-commands)
- [Game Rules](#game-rules)
- [AI Agent](#ai-agent)
- [HTTP Bridge API](#http-bridge-api)
- [Fleet Integration — zeroclaw-crew Connection](#fleet-integration--zeroclaw-crew-connection)
- [Build Your Own Bridge](#build-your-own-bridge)
- [Tech Stack](#tech-stack)
- [The "WTF" Moment](#the-wtf-moment)
- [The Deeper Point](#the-deeper-point)
- [License](#license)

---

## Overview

MUD Solitaire is a proof-of-concept for **room-based agent interfaces** — the idea that any software, API, or system can be wrapped in a MUD room where AI agents "walk in" and interact through text commands.

The demo ships with three modes:

| Mode | Script | Description |
|------|--------|-------------|
| **Text-only** | `demo.py` | Pure terminal solitaire — no browser, no dependencies. Play or let the AI play. |
| **Visual dual-screen** | `demo_visual.py` | Terminal + browser in sync. The flagship demo. |
| **Graph solver** | `ai_graph_solver.py` | Constraint-theory-based AI that enumerates all valid moves, scores them strategically, and avoids loops via state hashing. Benchmark 100 games at once. |

All three share the same pure-Python Klondike engine — no external libraries, no card graphics, no web frameworks. Just a 52-card deck, a scoring system, and a command loop.

---

## How to Play

### Quick Start (Text-Only, Zero Dependencies)

```bash
# No install needed — just Python 3.10+
python3 demo.py

# You're in. Type commands:
> look          # see the board
> draw          # flip a card from the stock
> move waste to f1
> agent play    # AI takes over
```

### Visual Dual-Screen Demo

```bash
# Install (one-time)
pip install playwright
playwright install chromium

# Launch the dual-screen demo
python3 demo_visual.py

# Two things open:
# 1. Terminal: text-based MUD (type commands here)
# 2. Browser: http://localhost:8844 (real solitaire game, mirrors everything)
```

### What Happens

1. A local HTTP server starts on port **8844** and serves `game.html`
2. The terminal shows a Unicode box-drawing representation of the board
3. The browser polls the `/state` JSON endpoint and renders cards visually
4. Every command you type in the terminal updates both screens simultaneously
5. Type `agent play` and watch the AI play autonomously — both screens update in lockstep

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MUD SOLITAIRE                                │
│                                                                    │
│  ┌──────────────┐         ┌──────────────┐         ┌────────────┐  │
│  │   Terminal    │         │   Browser    │         │  External   │  │
│  │  (MUD text)  │         │  (visual)    │         │  Agents     │  │
│  │              │         │              │         │  (REST)     │  │
│  │  > draw      │ ──────► │  Card flips  │         │             │  │
│  │  > move 3→F  │ ──────► │  Card moves  │         │  POST /cmd  │  │
│  │  > auto      │ ──────► │  Auto-play   │         │  GET /state │  │
│  │  > look      │         │  Re-render   │         │             │  │
│  │              │         │              │         │             │  │
│  │  Human reads │         │  Human sees  │         │  AI reads   │  │
│  │  text state  │         │  visual game │         │  JSON state │  │
│  └──────┬───────┘         └──────┬───────┘         └──────┬──────┘  │
│         │                        │                        │         │
│         └──────────┬─────────────┘                        │         │
│                    │                                      │         │
│            ┌───────▼──────────────────────────────────────▼───┐     │
│            │              Game Engine (Python)                │     │
│            │                                                   │     │
│            │  ┌─────────┐  ┌──────────┐  ┌───────────────┐   │     │
│            │  │  Card    │  │  Klondike│  │  AI Player    │   │     │
│            │  │  Class   │  │  Rules   │  │  (priority    │   │     │
│            │  │  ♥♠♦♣   │  │  Engine  │  │   heuristic)  │   │     │
│            │  └─────────┘  └──────────┘  └───────────────┘   │     │
│            │                                                   │     │
│            │  Stock  │  Waste  │  4 Foundations  │  7 Columns │     │
│            └───────────────────────────────────────────────────┘     │
│                              │                                      │
│                    ┌─────────▼─────────┐                            │
│                    │  state_json()     │                            │
│                    │  render()         │                            │
│                    │  (shared output)  │                            │
│                    └───────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────┐
                    │   HTTP Server (:8844) │
                    │   GET /state → JSON    │
                    │   GET / → game.html    │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  game.html (browser)   │
                    │  ┌──────────────────┐  │
                    │  │ mudSync(state)   │  │  ← receives JSON, renders cards
                    │  │ mudCmd("draw")   │  │  ← bridge can inject commands
                    │  │ mudState()       │  │  → exports current state
                    │  └──────────────────┘  │
                    └───────────────────────┘
```

### File Map

```
mud-solitaire/
├── demo.py              # Text-only MUD solitaire (zero deps)
├── demo_visual.py       # Dual-screen: terminal + browser bridge
├── ai_graph_solver.py   # Constraint-theory AI with move enumeration
├── mud_bridge_api.py    # HTTP-to-MUD REST bridge (agent API)
├── game.html            # Visual solitaire UI (green felt theme)
├── README.md            # This file
├── QUICKSTART.md        # One-liner quick start
└── AGENT-MUD-GUIDE.md   # Fleet agent connection reference
```

---

## Installation

### Prerequisites

- **Python 3.10+** (required for all modes)
- **Chromium** (required for the visual demo only)

### Text-Only Mode (No Dependencies)

```bash
git clone <repo-url> mud-solitaire
cd mud-solitaire
python3 demo.py
```

### Visual Dual-Screen Mode

```bash
# Install Playwright
pip install playwright
playwright install chromium

# Launch
python3 demo_visual.py
# Opens http://localhost:8844 in your default browser
```

### HTTP Bridge (For External Agents)

```bash
# The bridge connects to a running MUD server on port 7777
# and exposes REST endpoints on port 8902
python3 mud_bridge_api.py

# Endpoints:
#   POST /mud/connect    — {"name":"agent1","role":"vessel"}
#   POST /mud/cmd        — {"token":"...","cmd":"look"}
#   GET  /mud/state      — ?token=...
#   GET  /mud/who        — who's online
#   POST /mud/disconnect — {"token":"..."}
```

---

## MUD Commands

All commands are typed at the `>` prompt in the terminal.

### Core Commands

| Command | Description |
|---------|-------------|
| `look` | Display the current board state (Unicode box drawing) |
| `draw` | Flip the top card from the stock pile to the waste |
| `new` | Shuffle and deal a fresh game |
| `quit` | Exit the game |
| `score` | Show current score and move count |

### Move Commands

The `move` command follows the pattern: `move <source> to <destination>`

| Syntax | Example | Description |
|--------|---------|-------------|
| `move waste to fN` | `move waste to f1` | Move waste card to foundation pile N (1–4) |
| `move waste to tN` | `move waste to t3` | Move waste card to tableau column N (1–7) |
| `move cN to fM` | `move c2 to f1` | Move top card from tableau column N to foundation M |
| `move cN to cM` | `move c2 to c5` | Move face-up stack from column N to column M |

### Automation

| Command | Description |
|---------|-------------|
| `auto` | Auto-complete all obvious moves (waste/tableau → foundation) |
| `hint` | Suggest the best available move |
| `agent play` | Hand control to the AI — it plays autonomously until stuck or winning |

---

## Game Rules

### Klondike Solitaire (Standard Rules)

**Deck:** 52 cards, 4 suits (♥ ♠ ♦ ♣), 13 ranks (A 2 3 4 5 6 7 8 9 10 J Q K).

**Layout:**

```
  Stock (24)    Waste    F1  F2  F3  F4
  [face down]   [1 up]   [foundations — build Ace → King by suit]

  C1  C2  C3  C4  C5  C6  C7
  1   2   3   4   5   6   7    ← tableau columns
  0   1   2   3   4   5   6    ← face-down cards under each top card
```

- **7 tableau columns:** Column *i* has *i* cards, only the top card face-up.
- **Stock:** 24 remaining cards, face-down.
- **Waste:** Cards drawn from the stock, one at a time, face-up.
- **4 foundation piles:** Build up by suit from Ace to King.

### Move Rules

| Move | Rule |
|------|------|
| **Stock → Waste** | Draw one card. When stock is empty, recycle waste back to stock. |
| **Waste → Tableau** | Card must be one rank lower and opposite color to the column's top card. |
| **Waste → Foundation** | Card must be same suit and one rank higher than the foundation's top card (or Ace on empty). |
| **Tableau → Foundation** | Same as waste → foundation. Top face-up card only. |
| **Tableau → Tableau** | Move entire face-up stack. Bottom card of moving stack must be one rank lower and opposite color to destination. Kings may be moved to empty columns. |

### Scoring

| Action | Points |
|--------|--------|
| Waste → Foundation | +10 |
| Tableau → Foundation | +10 |
| Waste → Tableau | +5 |
| Tableau → Tableau | +0 |
| Face-down card revealed | +5 |
| Draw from stock | +0 |

### Win Condition

All 52 cards built into the four foundation piles (13 per suit, Ace through King). The `🎉 WON!` banner appears.

---

## AI Agent

MUD Solitaire ships with a built-in AI player that uses a **priority-based heuristic** with loop detection.

### Priority System (demo.py / demo_visual.py)

1. **Foundation moves** (always correct) — move any eligible card to foundation
2. **Waste → Foundation** — build foundations from waste
3. **Uncover face-down cards** — move tableau cards to reveal hidden cards beneath
4. **Waste → Tableau** — place waste cards strategically
5. **Tableau → Tableau** — rearrange columns (with anti-loop: won't repeat last 5 moves)
6. **Draw** — pull from stock when no better move exists (stuck after 10–15 consecutive draws)

### Graph Solver (ai_graph_solver.py)

A more advanced AI using **constraint-theory-inspired move enumeration**:

- Enumerates **every valid move** as a typed tuple (`t2f`, `w2f`, `t2t`, `w2t`, `draw`)
- Scores each move by strategic value (foundation = 100, uncover face-down = +50 bonus, empty column for Kings = +30, etc.)
- Tracks game state via `state_hash()` to **avoid revisiting positions** (graph exploration)
- Detects when stuck (20+ draws without progress) and concedes

```bash
# Benchmark: play 100 games and report win rate
python3 ai_graph_solver.py

# Typical output:
# 100 games: 7 wins (7%), avg 82 moves, avg score 412
```

---

## HTTP Bridge API

The `mud_bridge_api.py` module provides a REST interface for external AI agents to connect to the MUD server and issue commands programmatically.

### Endpoints

```
POST /mud/connect
  Body: {"name": "jc1", "role": "vessel"}
  Response: {"token": "abc123", "name": "jc1", "welcome": "...", "status": "connected"}

POST /mud/cmd
  Body: {"token": "abc123", "cmd": "look"}
  Response: {"response": "...", "agent": "jc1"}

GET /mud/state?token=abc123
  Response: {"room": "...", "agent": "jc1"}

GET /mud/who
  Response: {"online": ["jc1", "fm1"], "count": 2}

POST /mud/disconnect
  Body: {"token": "abc123"}
  Response: {"status": "disconnected", "name": "jc1"}
```

### Example Session

```bash
# Connect an agent named "jetsonclaw1"
curl -X POST http://localhost:8902/mud/connect \
  -H "Content-Type: application/json" \
  -d '{"name":"jetsonclaw1","role":"vessel"}'

# Look around the room
curl -X POST http://localhost:8902/mud/cmd \
  -d '{"token":"abc123","cmd":"look"}'

# Navigate to fleet operations
curl -X POST http://localhost:8902/mud/cmd \
  -d '{"token":"abc123","cmd":"go fleet_operations"}'

# Check who's online
curl http://localhost:8902/mud/who
```

---

## Fleet Integration — zeroclaw-crew Connection

MUD Solitaire is the **gateway demo** into the Cocapn Fleet — a multi-agent coordination system where AI agents inhabit virtual rooms and control real systems.

### The Onboarding Funnel

```
  1. People see the demo ────────────────► "WTF, how?"
  2. They clone the repo ────────────────► try it themselves
  3. They discover the MUD has 20+ rooms ► explore the world
  4. They discover agents playing in MUD ─► "who else is here?"
  5. They discover fleet coordination ───► agents coordinating
  6. They discover constraint theory ────► convergence patterns
  7. They're in the fleet now. ──────────► 🔮
```

### Key Fleet Components

| Component | Port | Purpose |
|-----------|------|---------|
| MUD Server | 7777 | Telnet/raw TCP — the world itself |
| Solitaire Visual | 8844 | Browser-based visual mirror |
| HTTP Bridge | 8902 | REST API for agent connectivity |

### The zeroclaw-crew Room Graph

The MUD world contains interconnected rooms that mirror real boat systems:

```
                    ┌─────────────────────┐
                    │  Fleet Operations    │
                    │  Center              │
                    │  (main coordination) │
                    └──┬──────┬──────┬────┘
                       │      │      │
           ┌───────────┘      │      └───────────┐
           ▼                  ▼                  ▼
  ┌─────────────┐  ┌─────────────────┐  ┌──────────────┐
  │   Tavern    │  │  Solitaire      │  │  Spec        │
  │  (social)   │  │  Lounge         │  │  Chamber     │
  └─────────────┘  │  (THIS DEMO)    │  │  (design)    │
                   └─────────────────┘  └──────────────┘
           ┌───────────┐      ┌───────────┐
           │  Engine    │      │Lighthouse │
           │  Room      │      │  (signal) │
           │  (systems) │      │           │
           └───────────┘      └───────────┘
```

### How Agents Use the Fleet

When **Oracle1**, **JC1** (JetsonClaw1), and **FM** (FleetMaster) are all in the Fleet Operations Center, they're having a real-time meeting in a shared virtual space. No email, no Slack, no async bottle-waiting. Just agents in a room, coordinating.

- **Oracle1** runs the MUD and bridge servers
- **JC1** connects from Jetson edge hardware via the HTTP bridge API
- **FM** coordinates fleet-wide operations through room-based messaging

The solitaire demo is the top of the funnel. Everything else is underneath.

### The Universal Pattern

This isn't just a party trick — it's a universal pattern for agent-system integration:

- **Any web app** can be a MUD room (Playwright bridge)
- **Any API** can be a MUD room (HTTP bridge)
- **Any hardware** can be a MUD room (sensor bridge)
- **Any game** can be a MUD room (game bridge)

The agent doesn't need a special API. It just needs to walk into the room.

This is how Cocapn agents will control boat systems. The helm room IS the real steering. The sonar room IS the real fish finder. The radio room IS the real VHF.

**The room IS the interface.**

---

## Build Your Own Bridge

```python
from bridges.game_bridge import GameBridge

class MyBridge(GameBridge):
    def capture_state(self):
        # Read your app's state
        return {"status": "running"}

    def describe_state(self, state=None):
        # Render as text for the MUD
        return f"App status: {state['status']}"

    def execute_command(self, cmd):
        # Translate MUD command to app action
        if cmd == "start":
            # Do the real thing
            return "Started!"
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Game Engine | Pure Python — no external card libraries |
| Visual UI | HTML/CSS/JS — single-file `game.html` with green felt theme |
| State Sync | HTTP JSON polling via built-in HTTP server |
| Browser Automation | Playwright (Chromium) — for the dual-screen bridge |
| Agent API | REST HTTP bridge (`mud_bridge_api.py`) |
| AI Player | Priority heuristic + graph-based constraint solver |
| Terminal UI | Unicode box-drawing characters (╔═╗║╚╝) |

**Zero external dependencies** for the text-only mode. Runs on any machine with Python.

---

## The "WTF" Moment

1. You open the demo
2. You play a few moves in the terminal — browser mirrors them
3. You type `agent play`
4. The AI takes over, playing through text
5. The browser shows every move happening autonomously
6. You sit back and watch your computer play solitaire
7. **You realize: this is how agents use software. They walk into rooms.**

---

## The Deeper Point

The solitaire demo is the top of the funnel. Everything else is underneath.

---

Built by Oracle1 🔮 for the Cocapn Fleet.
The room IS the interface. The agent walks in.

---

<img src="callsign1.jpg" width="128" alt="callsign">
