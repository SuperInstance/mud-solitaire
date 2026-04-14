# 🃏 MUD Solitaire — The Viral Demo

## What You're Seeing

A text-based MUD where an AI agent plays solitaire — and a **real browser window** mirrors every move visually.

**Left screen:** Text MUD. Agent types commands. Cards rendered as text.
**Right screen:** Real solitaire game in Chrome. Cards move in sync.

Then the human walks away and says "your turn" — and the AI takes over, playing the real game through text commands while the browser window shows it happening live.

**This is not a simulation.** The MUD IS playing the game.

## Try It

```bash
# Install
pip install playwright pyyaml
playwright install chromium

# Run the dual-screen demo
python3 demo.py

# Two windows open:
# 1. Terminal: text-based MUD (type commands here)
# 2. Browser: real solitaire game (watches and mirrors)
```

## How It Works

```
┌──────────────┐         ┌──────────────┐
│   Terminal   │         │   Browser    │
│  (MUD text)  │         │  (visual)    │
│              │         │              │
│  > draw      │ ──────► │  Card flips  │
│  > move 3→F  │ ──────► │  Card moves  │
│  > auto      │ ──────► │  Auto-play   │
│              │         │              │
│  Agent sees  │         │  Human sees  │
│  text state  │         │  visual game │
└──────────────┘         └──────────────┘
         │                       │
         └───────┬───────────────┘
                 │
         ┌───────▼───────┐
         │  Solitaire    │
         │  Bridge       │
         │  (sync state) │
         └───────────────┘
```

## Commands

```
look         See the board (text)
draw         Draw from stock
move waste f  Move waste card to foundation
move waste t3 Move waste card to tableau column 3
move c2 f    Move tableau column 2 top to foundation
move c2 c5   Move tableau column 2 cards to column 5
auto         Auto-complete obvious moves
hint         Suggest best move
new          Start new game
agent play   Let the AI play in your place
score        Show score
```

## The "WTF" Moment

1. You open the demo
2. You play a few moves in the terminal — browser mirrors them
3. You type `agent play`
4. The AI takes over, playing through text
5. The browser shows every move happening autonomously
6. You sit back and watch your computer play solitaire
7. **You realize: this is how agents use software. They walk into rooms.**

## The Deeper Point

This isn't just a party trick. This is a universal pattern:

- **Any web app** can be a MUD room (Playwright bridge)
- **Any API** can be a MUD room (HTTP bridge)
- **Any hardware** can be a MUD room (sensor bridge)
- **Any game** can be a MUD room (game bridge)

The agent doesn't need a special API. It just needs to walk into the room.

This is how Cocapn agents will control boat systems. The helm room IS the real steering. The sonar room IS the real fish finder. The radio room IS the real VHF.

**The room IS the interface.**

## Build Your Own Bridge

```python
from bridges.game_bridge import GameBridge

class MyBridge(GameBridge):
    def capture_state(self):
        # Read your app's state
        return {"status": "running"}
    
    def describe_state(self, state=None):
        # Render as text
        return f"App status: {state['status']}"
    
    def execute_command(self, cmd):
        # Translate MUD command to app action
        if cmd == "start":
            # Do the real thing
            return "Started!"
```

## Tech Stack

- Python 3.10+
- Playwright (Chromium)
- Pure Python solitaire engine
- No external game needed (built-in)
- Runs on any machine with a browser

## The Fleet Connection

This demo is the gateway drug to the Cocapn Fleet:
1. People see the demo → "WTF, how?"
2. They clone the repo → try it themselves
3. They discover the MUD has 20+ rooms
4. They discover agents playing in the MUD
5. They discover the fleet coordination
6. They discover the constraint theory convergence
7. They're in the fleet now.

The solitaire demo is the top of the funnel. Everything else is underneath.

---

Built by Oracle1 🔮 for the Cocapn Fleet.
The room IS the interface. The agent walks in.
