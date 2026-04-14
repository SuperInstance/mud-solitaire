#!/usr/bin/env python3
"""Playwright Bridge — controls HTML solitaire from MUD text commands.

Usage:
  python3 demo_visual.py
  
Opens two things:
1. Terminal: text MUD (type commands)
2. Browser: visual solitaire (mirrors every move)

The bridge keeps both in sync. Type "agent play" to watch AI take over.
"""

import sys, os, time, json, random, subprocess, threading
import http.server, socketserver

SUITS = ["♥", "♠", "♦", "♣"]
RANKS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
RANK_VAL = {r:i for i,r in enumerate(RANKS)}

# ═══════════════════════════════════════
# Game Engine (same as text version)
# ═══════════════════════════════════════
class Card:
    def __init__(self, s, r, up=False):
        self.suit, self.rank, self.face_up = s, r, up
    def red(self): return self.suit in "♥♦"
    def val(self): return RANK_VAL[self.rank]
    def __repr__(self): return f"{self.rank}{self.suit}" if self.face_up else "[XX]"
    def to_dict(self): return {"suit": self.suit, "rank": self.rank, "face_up": self.face_up}

class Game:
    def __init__(self):
        self._ai_history = []
        self._ai_draws = 0
        self.reset()
    
    def reset(self):
        deck = [Card(s,r) for s in SUITS for r in RANKS]
        random.shuffle(deck)
        self.tab = [[] for _ in range(7)]
        for i in range(7):
            for j in range(i+1):
                c = deck.pop(); c.face_up = (j==i)
                self.tab[i].append(c)
        self.stock = deck
        self.waste = []
        self.found = [[] for _ in range(4)]
        self.score = 0
        self.moves = 0
        self._ai_history = []
        self._ai_draws = 0
    
    def draw(self):
        if self.stock:
            c = self.stock.pop(); c.face_up = True; self.waste.append(c); self.moves += 1; return True
        elif self.waste:
            self.stock = list(reversed(self.waste))
            for c in self.stock: c.face_up = False
            self.waste = []; return True
        return False
    
    def _can_found(self, card, fi):
        p = self.found[fi]
        if not p: return card.rank == "A"
        return card.suit == p[-1].suit and card.val() == p[-1].val() + 1
    
    def _can_tab(self, card, ci):
        col = self.tab[ci]
        if not col: return card.rank == "K"
        top = col[-1]
        return top.face_up and card.red() != top.red() and card.val() == top.val() - 1
    
    def move_w2f(self, fi):
        if not self.waste: return False
        c = self.waste[-1]
        if self._can_found(c, fi):
            self.waste.pop(); self.found[fi].append(c); self.score += 10; self.moves += 1; return True
        return False
    
    def move_w2t(self, ci):
        if not self.waste: return False
        c = self.waste[-1]
        if self._can_tab(c, ci):
            self.waste.pop(); self.tab[ci].append(c); self.score += 5; self.moves += 1; return True
        return False
    
    def move_t2f(self, ci, fi):
        col = self.tab[ci]
        if not col or not col[-1].face_up: return False
        c = col[-1]
        if self._can_found(c, fi):
            col.pop(); self.found[fi].append(c); self.score += 10; self.moves += 1
            if col and not col[-1].face_up: col[-1].face_up = True; self.score += 5
            return True
        return False
    
    def move_t2t(self, ci, ti):
        src = self.tab[ci]
        if not src: return False
        start = len(src) - 1
        while start > 0 and src[start-1].face_up: start -= 1
        c = src[start]
        if self._can_tab(c, ti):
            cards = src[start:]; del src[start:]; self.tab[ti].extend(cards); self.moves += 1
            if src and not src[-1].face_up: src[-1].face_up = True; self.score += 5
            return True
        return False
    
    def auto(self):
        moved = 0; changed = True
        while changed:
            changed = False
            if self.waste:
                for fi in range(4):
                    if self._can_found(self.waste[-1], fi):
                        self.move_w2f(fi); moved += 1; changed = True; break
            for ci in range(7):
                if self.tab[ci] and self.tab[ci][-1].face_up:
                    for fi in range(4):
                        if self._can_found(self.tab[ci][-1], fi):
                            self.move_t2f(ci, fi); moved += 1; changed = True; break
        return moved
    
    def won(self): return all(len(f)==13 for f in self.found)
    
    def state_json(self):
        return {
            "stock": [{"suit":c.suit,"rank":c.rank,"face_up":c.face_up} for c in self.stock],
            "waste": [{"suit":c.suit,"rank":c.rank,"face_up":c.face_up} for c in self.waste],
            "foundations": [[{"suit":c.suit,"rank":c.rank,"face_up":c.face_up} for c in f] for f in self.found],
            "tableau": [[{"suit":c.suit,"rank":c.rank,"face_up":c.face_up} for c in col] for col in self.tab],
            "score": self.score, "moves": self.moves, "won": self.won()
        }
    
    def render(self):
        lines = []
        lines.append("╔════════════════════════════════════════════════╗")
        lines.append("║           ♠ ♥ MUD SOLITAIRE ♦ ♣               ║")
        lines.append("╠════════════════════════════════════════════════╣")
        stk = f"[{len(self.stock)}]"
        wst = str(self.waste[-1]) if self.waste else "---"
        lines.append(f"║  Stock: {stk:<5}  Waste: {wst:<6}                    ║")
        fnd = " ".join(f"{str(f[-1]) if f else '___':>4}" for f in self.found)
        lines.append(f"║  Foundation: {fnd}                   ║")
        lines.append("╠════════════════════════════════════════════════╣")
        for i, col in enumerate(self.tab):
            cs = " ".join(str(c) for c in col) if col else "(empty)"
            lines.append(f"║  Col {i+1}: {cs}")
        lines.append("╠════════════════════════════════════════════════╣")
        lines.append(f"║  Score: {self.score}  Moves: {self.moves}  {'🎉 WON!' if self.won() else '':>12}    ║")
        lines.append("╚════════════════════════════════════════════════╝")
        return "\n".join(lines)


def ai_play_step(game):
    """Smart AI with loop prevention."""
    # Priority 1: Foundation moves
    for ci in range(7):
        col = game.tab[ci]
        if col and col[-1].face_up:
            for fi in range(4):
                if game._can_found(col[-1], fi):
                    game.move_t2f(ci, fi)
                    return f"move col {ci+1} to foundation {fi+1}"
    
    # Priority 2: Waste to foundation
    if game.waste:
        for fi in range(4):
            if game._can_found(game.waste[-1], fi):
                game.move_w2f(fi)
                return f"move waste to foundation {fi+1}"
    
    # Priority 3: Uncover face-down cards
    for ci in range(7):
        col = game.tab[ci]
        if col and len(col) > 1 and col[-1].face_up and not col[-2].face_up:
            for ti in range(7):
                if ti != ci and game._can_tab(col[-1], ti):
                    game.move_t2t(ci, ti)
                    return f"move col {ci+1} to col {ti+1}"
    
    # Priority 4: Waste to tableau
    if game.waste:
        for ci in range(7):
            if game._can_tab(game.waste[-1], ci):
                game.move_w2t(ci)
                return f"move waste to tableau {ci+1}"
    
    # Priority 5: Other tableau (avoid loops)
    for ci in range(7):
        col = game.tab[ci]
        if col and len(col) > 1 and col[-1].face_up:
            for ti in range(7):
                if ti != ci and game._can_tab(col[-1], ti):
                    desc = f"move col {ci+1} to col {ti+1}"
                    if desc not in game._ai_history[-5:]:
                        game.move_t2t(ci, ti)
                        game._ai_history.append(desc)
                        return desc
    
    # Draw
    game._ai_draws += 1
    if game._ai_draws > 15:
        return "__stuck__"
    game.draw()
    return "draw"


# ═══════════════════════════════════════
# HTTP Server — serves game.html + state API
# ═══════════════════════════════════════
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=os.path.dirname(os.path.abspath(__file__)), **kw)
    
    def do_GET(self):
        if self.path == "/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(game.state_json()).encode())
        elif self.path == "/" or self.path == "/game.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game.html")
            with open(html_path) as f:
                self.wfile.write(f.read().encode())
        else:
            super().do_GET()
    
    def log_message(self, *a): pass  # Quiet

game = Game()
PORT = 8844

def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

# Start HTTP server in background
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

print(f"\n{'='*50}")
print("🃏 MUD SOLITAIRE — Visual Demo")
print(f"{'='*50}")
print(f"\nBrowser: http://localhost:{PORT}")
print("Terminal: type commands below")
print("\nCommands: draw | move | auto | new | agent play | quit")
print("Move: move waste to f|tN | move cN to f|cN")
print()

game.reset()
print(game.render())

# Try to open browser
try:
    import webbrowser
    webbrowser.open(f"http://localhost:{PORT}")
except: pass

ai_mode = False
while True:
    try:
        if ai_mode:
            if game.won():
                print("\n🎉 AI WON!")
                ai_mode = False
                continue
            time.sleep(0.3)
            cmd = ai_play_step(game)
            if cmd == "__stuck__":
                print("\n🤔 Stuck. New game.")
                game.reset(); ai_mode = True
                continue
            print(f"\n> {cmd}")
            print(game.render())
            continue
        
        cmd = input("\n> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nBye!")
        break
    
    if not cmd: continue
    if cmd == "quit": break
    elif cmd == "look": print(game.render())
    elif cmd == "new": game.reset(); print("New game!\n"); print(game.render())
    elif cmd == "draw": game.draw(); print(game.render())
    elif cmd == "auto":
        m = game.auto(); print(f"Auto-moved {m}.\n"); print(game.render())
    elif cmd == "agent play":
        ai_mode = True; print("\n🤖 Agent playing...\n")
    elif cmd.startswith("move"):
        parts = cmd.split()
        if "waste" in parts:
            target = parts[-1]
            if target.startswith("f"): game.move_w2f(int(target[1:])-1)
            elif target.startswith("t"): game.move_w2t(int(target[1:])-1)
        elif "c" in parts[1]:
            ci = int(parts[1][1:])-1; target = parts[-1]
            if target.startswith("f"): game.move_t2f(ci, int(target[1:])-1)
            elif target.startswith("c"): game.move_t2t(ci, int(parts[-1][1:])-1)
        print(game.render())
    else: print(f"Unknown: {cmd}")
