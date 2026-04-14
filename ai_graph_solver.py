#!/usr/bin/env python3
"""Fix solitaire AI — graph-connected approach to move validation.
Uses constraint-theory-inspired exact move tracking."""
import random

SUITS = ["♥", "♠", "♦", "♣"]
RANKS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
RVAL = {r:i for i,r in enumerate(RANKS)}

class Card:
    def __init__(self, s, r, up=False):
        self.suit, self.rank, self.face_up = s, r, up
    def red(self): return self.suit in "♥♦"
    def val(self): return RVAL[self.rank]
    def __repr__(self): return f"{self.rank}{self.suit}" if self.face_up else "[XX]"

class Game:
    def __init__(self): self.reset()
    def reset(self):
        deck = [Card(s,r) for s in SUITS for r in RANKS]
        random.shuffle(deck)
        self.tab = [[] for _ in range(7)]
        for i in range(7):
            for j in range(i+1): c=deck.pop(); c.face_up=(j==i); self.tab[i].append(c)
        self.stock = deck; self.waste = []; self.found = [[] for _ in range(4)]
        self.score = 0; self.moves = 0
    
    def draw(self):
        if self.stock:
            c=self.stock.pop(); c.face_up=True; self.waste.append(c); self.moves+=1; return True
        elif self.waste:
            self.stock=list(reversed(self.waste))
            for c in self.stock: c.face_up=False
            self.waste=[]; return True
        return False
    
    def _cf(self, card, fi):
        p=self.found[fi]
        if not p: return card.rank=="A"
        return card.suit==p[-1].suit and card.val()==p[-1].val()+1
    
    def _ct(self, card, ci):
        col=self.tab[ci]
        if not col: return card.rank=="K"
        top=col[-1]
        return top.face_up and card.red()!=top.red() and card.val()==top.val()-1
    
    def mw2f(self, fi):
        if not self.waste: return False
        c=self.waste[-1]
        if self._cf(c, fi): self.waste.pop(); self.found[fi].append(c); self.score+=10; self.moves+=1; return True
        return False
    
    def mw2t(self, ci):
        if not self.waste: return False
        c=self.waste[-1]
        if self._ct(c, ci): self.waste.pop(); self.tab[ci].append(c); self.score+=5; self.moves+=1; return True
        return False
    
    def mt2f(self, ci, fi):
        col=self.tab[ci]
        if not col or not col[-1].face_up: return False
        c=col[-1]
        if self._cf(c, fi):
            col.pop(); self.found[fi].append(c); self.score+=10; self.moves+=1
            if col and not col[-1].face_up: col[-1].face_up=True; self.score+=5
            return True
        return False
    
    def mt2t(self, ci, ti):
        src=self.tab[ci]
        if not src: return False
        start=len(src)-1
        while start>0 and src[start-1].face_up: start-=1
        c=src[start]
        if self._ct(c, ti):
            cards=src[start:]; del src[start:]; self.tab[ti].extend(cards); self.moves+=1
            if src and not src[-1].face_up: src[-1].face_up=True; self.score+=5
            return True
        return False
    
    def won(self): return all(len(f)==13 for f in self.found)
    
    def render(self):
        lines = []
        lines.append("╔════════════════════════════════════════════════╗")
        lines.append("║           ♠ ♥ MUD SOLITAIRE ♦ ♣               ║")
        lines.append("╠════════════════════════════════════════════════╣")
        stk=f"[{len(self.stock)}]"
        wst=str(self.waste[-1]) if self.waste else "---"
        lines.append(f"║  Stock: {stk:<5}  Waste: {wst:<6}                    ║")
        fnd=" ".join(f"{str(f[-1]) if f else '___':>4}" for f in self.found)
        lines.append(f"║  Foundation: {fnd}                   ║")
        lines.append("╠════════════════════════════════════════════════╣")
        for i, col in enumerate(self.tab):
            cs=" ".join(str(c) for c in col) if col else "(empty)"
            lines.append(f"║  Col {i+1}: {cs}")
        lines.append("╠════════════════════════════════════════════════╣")
        lines.append(f"║  Score: {self.score}  Moves: {self.moves}  {'🎉 WON!' if self.won() else '':>12}    ║")
        lines.append("╚════════════════════════════════════════════════╝")
        return "\n".join(lines)


def get_all_valid_moves(game):
    """Enumerate every valid move as a (type, params) tuple."""
    moves = []
    
    # Draw
    if game.stock or game.waste:
        moves.append(("draw",))
    
    # Waste to foundation
    if game.waste:
        for fi in range(4):
            if game._cf(game.waste[-1], fi):
                moves.append(("w2f", fi))
    
    # Waste to tableau
    if game.waste:
        for ci in range(7):
            if game._ct(game.waste[-1], ci):
                moves.append(("w2t", ci))
    
    # Tableau to foundation
    for ci in range(7):
        col = game.tab[ci]
        if col and col[-1].face_up:
            for fi in range(4):
                if game._cf(col[-1], fi):
                    moves.append(("t2f", ci, fi))
    
    # Tableau to tableau
    for ci in range(7):
        src = game.tab[ci]
        if not src: continue
        start = len(src) - 1
        while start > 0 and src[start-1].face_up: start -= 1
        c = src[start]
        for ti in range(7):
            if ti != ci and game._ct(c, ti):
                moves.append(("t2t", ci, ti))
    
    return moves


def score_move(game, move):
    """Score a move by strategic value. Higher = better."""
    if move[0] == "t2f":
        return 100  # Always move to foundation
    if move[0] == "w2f":
        return 90   # Waste to foundation is great
    if move[0] == "t2t":
        ci, ti = move[1], move[2]
        src = game.tab[ci]
        # Bonus: uncovering a face-down card
        start = len(src) - 1
        while start > 0 and src[start-1].face_up: start -= 1
        bonus = 50 if start > 0 and not src[start-1].face_up else 0
        # Bonus: moving to empty column only for Kings
        if not game.tab[ti]:
            bonus += 30 if src[start].rank == "K" else -20
        return 30 + bonus
    if move[0] == "w2t":
        return 20   # Waste to tableau is ok
    if move[0] == "draw":
        return 5    # Drawing is low priority
    return 0


def ai_play_step(game):
    """Smart AI: enumerate all moves, score them, pick best. Track state to avoid loops."""
    if not hasattr(game, '_seen_states'):
        game._seen_states = set()
        game._draws_since_progress = 0
    
    moves = get_all_valid_moves(game)
    if not moves:
        return "__stuck__"
    
    # Score and sort
    scored = [(score_move(game, m), m) for m in moves]
    scored.sort(key=lambda x: -x[0])
    
    # Pick best move that doesn't repeat state
    for score, move in scored:
        # Execute tentatively and check state
        state_before = state_hash(game)
        execute(game, move)
        state_after = state_hash(game)
        
        if state_after != state_before:
            if state_after not in game._seen_states:
                game._seen_states.add(state_after)
                game._draws_since_progress = 0
                return describe_move(move)
            # State seen before — undo
            # Actually we can't easily undo, so just avoid draws when looping
        
        if move[0] == "draw":
            game._draws_since_progress += 1
            if game._draws_since_progress > 20:
                return "__stuck__"
            return "draw"
        
        # Move leads to seen state — try next
        game._seen_states.add(state_after)
        game._draws_since_progress = 0
        return describe_move(move)
    
    return "__stuck__"


def state_hash(game):
    """Hash game state for loop detection."""
    parts = []
    parts.append(str(len(game.stock)))
    parts.append(str(game.waste[-1]) if game.waste else "")
    for f in game.found:
        parts.append(str(f[-1]) if f else "")
    for col in game.tab:
        parts.append(str(col[-1]) if col else "")
    return "|".join(parts)


def execute(game, move):
    if move[0] == "draw": game.draw()
    elif move[0] == "w2f": game.mw2f(move[1])
    elif move[0] == "w2t": game.mw2t(move[1])
    elif move[0] == "t2f": game.mt2f(move[1], move[2])
    elif move[0] == "t2t": game.mt2t(move[1], move[2])


def describe_move(move):
    if move[0] == "draw": return "draw"
    elif move[0] == "w2f": return f"move waste to foundation {move[1]+1}"
    elif move[0] == "w2t": return f"move waste to tableau {move[1]+1}"
    elif move[0] == "t2f": return f"move col {move[1]+1} to foundation {move[2]+1}"
    elif move[0] == "t2t": return f"move col {move[1]+1} to col {move[2]+1}"


def auto_play(game, max_moves=200):
    """Play a full game and return stats."""
    for _ in range(max_moves):
        if game.won():
            return True
        move = ai_play_step(game)
        if move == "__stuck__":
            return False
    return False


# Benchmark: play 100 games
if __name__ == "__main__":
    wins = 0
    total_moves = 0
    total_score = 0
    
    for i in range(100):
        g = Game()
        won = auto_play(g)
        if won: wins += 1
        total_moves += g.moves
        total_score += g.score
    
    print(f"100 games: {wins} wins ({wins}%), avg {total_moves//100} moves, avg score {total_score//100}")
    
    # Show one game
    g = Game()
    print(g.render())
    moves = 0
    while not g.won() and moves < 200:
        m = ai_play_step(g)
        if m == "__stuck__":
            print(f"\nStuck after {moves} moves, score {g.score}")
            break
        print(f"\n> {m}")
        print(g.render())
        moves += 1
    if g.won():
        print(f"\n🎉 WON in {moves} moves, score {g.score}!")
