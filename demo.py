#!/usr/bin/env python3
"""MUD Solitaire Demo — dual-screen: text MUD + visual browser

This is THE demo. Terminal on left, browser on right, in sync.
"""
import sys, os, time, json, random

# Add bridges to path
sys.path.insert(0, os.path.dirname(__file__))

# ═══════════════════════════════════════
# Pure Python Solitaire (no external deps)
# ═══════════════════════════════════════
SUITS = ["♥", "♠", "♦", "♣"]
RANKS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
RANK_VAL = {r:i for i,r in enumerate(RANKS)}

class Card:
    def __init__(self, s, r, up=False):
        self.suit, self.rank, self.face_up = s, r, up
    def red(self): return self.suit in "♥♦"
    def val(self): return RANK_VAL[self.rank]
    def __repr__(self): return f"{self.rank}{self.suit}" if self.face_up else "[XX]"

class Game:
    def __init__(self):
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
        # Move all face-up cards from bottom of face-up stack
        start = len(src) - 1
        while start > 0 and src[start-1].face_up: start -= 1
        c = src[start]
        if self._can_tab(c, ti):
            cards = src[start:]; del src[start:]; self.tab[ti].extend(cards); self.moves += 1
            if src and not src[-1].face_up: src[-1].face_up = True; self.score += 5
            return True
        return False
    
    def auto(self):
        moved = 0
        changed = True
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

# ═══════════════════════════════════════
# Simple AI player
# ═══════════════════════════════════════
def ai_play_step(game):
    """Smart AI move. Avoids loops by tracking history."""
    if not hasattr(game, '_ai_history'):
        game._ai_history = []
        game._ai_draws = 0
    
    def try_move(desc, func):
        result = func()
        if result:
            game._ai_history.append(desc)
            game._ai_draws = 0
            return desc
        return None
    
    # Priority 1: Move to foundation (always correct)
    for ci in range(7):
        col = game.tab[ci]
        if col and col[-1].face_up:
            for fi in range(4):
                if game._can_found(col[-1], fi):
                    game.move_t2f(ci, fi)
                    desc = f"move col {ci+1} to foundation {fi+1}"
                    game._ai_history.append(desc)
                    game._ai_draws = 0
                    return desc
    
    # Priority 2: Waste to foundation
    if game.waste:
        for fi in range(4):
            if game._can_found(game.waste[-1], fi):
                game.move_w2f(fi)
                desc = f"move waste to foundation {fi+1}"
                game._ai_history.append(desc)
                game._ai_draws = 0
                return desc
    
    # Priority 3: Uncover face-down cards (move from tableau with face-down cards)
    for ci in range(7):
        col = game.tab[ci]
        if col and len(col) > 1 and col[-1].face_up and not col[-2].face_up:
            for ti in range(7):
                if ti != ci and game._can_tab(col[-1], ti):
                    game.move_t2t(ci, ti)
                    desc = f"move col {ci+1} to col {ti+1} (uncover)"
                    game._ai_history.append(desc)
                    game._ai_draws = 0
                    return desc
    
    # Priority 4: Waste to tableau
    if game.waste:
        for ci in range(7):
            if game._can_tab(game.waste[-1], ci):
                game.move_w2t(ci)
                desc = f"move waste to tableau {ci+1}"
                game._ai_history.append(desc)
                game._ai_draws = 0
                return desc
    
    # Priority 5: Other tableau moves (avoid loops)
    for ci in range(7):
        col = game.tab[ci]
        if col and len(col) > 1 and col[-1].face_up:
            for ti in range(7):
                if ti != ci and game._can_tab(col[-1], ti):
                    desc = f"move col {ci+1} to col {ti+1}"
                    if desc not in game._ai_history[-5:]:  # Don't repeat recent moves
                        game.move_t2t(ci, ti)
                        game._ai_history.append(desc)
                        game._ai_draws = 0
                        return desc
    
    # Priority 6: Draw (with stuck detection)
    game._ai_draws += 1
    if game._ai_draws > 10:
        return "__stuck__"  # Signal to give up or start new game
    
    game.draw()
    game._ai_history.append("draw")
    return "draw"



# ═══════════════════════════════════════
# Main loop
# ═══════════════════════════════════════
def main():
    game = Game()
    ai_mode = False
    
    print("\n" + "="*50)
    print("🃏 MUD SOLITAIRE — The Viral Demo")
    print("="*50)
    print("\nCommands: draw | move | auto | hint | new | agent play | quit")
    print("Move syntax: move waste to f|tN | move cN to f|cN")
    print()
    print(game.render())
    
    while True:
        try:
            if ai_mode:
                if game.won():
                    print("\n🎉 AI WON THE GAME!")
                if cmd == "__stuck__":
                    print("\n🤔 Agent is stuck. Starting new game...")
                    game.reset()
                    game._ai_history = []
                    game._ai_draws = 0
                    print(game.render())
                    continue
                    ai_mode = False
                    continue
                time.sleep(0.5)
                cmd = ai_play_step(game)
                print(f"\n> {cmd}")
                print(game.render())
                continue
            
            cmd = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        
        if not cmd:
            continue
        
        if cmd == "quit":
            break
        elif cmd == "look":
            print(game.render())
        elif cmd == "new":
            game.reset(); ai_mode = False
            print("New game!\n"); print(game.render())
        elif cmd == "draw":
            game.draw(); print(game.render())
        elif cmd == "auto":
            m = game.auto()
            print(f"Auto-moved {m} cards.\n"); print(game.render())
        elif cmd == "hint":
            # Find first valid move
            for ci in range(7):
                col = game.tab[ci]
                if col and col[-1].face_up:
                    for fi in range(4):
                        if game._can_found(col[-1], fi):
                            print(f"Hint: move {col[-1]} from col {ci+1} to foundation {fi+1}")
                            break
            else:
                print("Hint: try drawing from stock")
        elif cmd == "score":
            print(f"Score: {game.score}, Moves: {game.moves}")
        elif cmd == "agent play":
            ai_mode = True
            print("\n🤖 Agent taking over...\n")
        elif cmd.startswith("move"):
            parts = cmd.split()
            # Parse: move waste to f|tN | move cN to f|cN
            if "waste" in parts:
                target = parts[-1]
                if target.startswith("f"):
                    fi = int(target[1:]) - 1
                    if not game.move_w2f(fi): print("Can't move there.")
                elif target.startswith("t"):
                    ci = int(target[1:]) - 1
                    if not game.move_w2t(ci): print("Can't move there.")
            elif "c" in parts[1]:
                ci = int(parts[1][1:]) - 1
                target = parts[-1]
                if target.startswith("f"):
                    fi = int(target[1:]) - 1
                    if not game.move_t2f(ci, fi): print("Can't move there.")
                elif target.startswith("c"):
                    ti = int(parts[-1][1:]) - 1
                    if not game.move_t2t(ci, ti): print("Can't move there.")
            print(game.render())
        else:
            print(f"Unknown: {cmd}. Try: draw, move, auto, hint, new, agent play, quit")

if __name__ == "__main__":
    main()
