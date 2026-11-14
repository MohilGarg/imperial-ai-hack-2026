"""Clones of real tournament bots fitted to 21 counted rounds (129,000 opponent hands).
Preflop: nested top-X% ranges per raise level. Postflop: quantiles of a low-noise hand
strength (shared samples per board) so bet/fold/raise rates by street and bet size match."""
import os, random, bisect
import oldbot as B

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = {}
for line in open(os.path.join(HERE, '..', 'profiles.txt'), encoding='utf-8'):
    if '|' in line:
        name, vals = line.rstrip('\n').split('|'); RAW[name] = [int(v) for v in vals.split(',')]
FIELD = RAW['FIELD']

def _v(r, i):
    return (r[i] if r[i] >= 0 else FIELD[i]) / 100.0
def _shr(r, i, ni, k=10.0):
    n = max(0, r[ni]); p = _v(r, i); return (p * n + FIELD[i] / 100.0 * k) / (n + k)

def profile(name):
    r = RAW[name]; p = {}
    p['open'] = {'E': _v(r, 2), 'CO': _v(r, 3), 'BTN': _v(r, 4), 'SB': _v(r, 5)}
    p['limp'] = _v(r, 6); p['size'] = (r[7] if r[7] > 0 else FIELD[7]) / 10.0; p['jam'] = _v(r, 8); p['iso'] = _v(r, 9)
    p['vofold'] = _v(r, 10); p['three'] = _v(r, 11); p['size3'] = (r[12] if r[12] > 0 else FIELD[12]) / 10.0
    p['v3fold'] = _shr(r, 13, 15); p['v3raise'] = _shr(r, 14, 15)
    p['vjr'] = _shr(r, 16, 17); p['vjc'] = _shr(r, 18, 19, 20.0); p['lf'] = _shr(r, 20, 21)
    p['post'] = {}
    for k, s in enumerate(('flop', 'turn', 'river')):
        b = 22 + 7 * k
        p['post'][s] = (_v(r, b), _v(r, b + 1), min(1.5, (r[b + 2] if r[b + 2] > 0 else FIELD[b + 2]) / 100.0), _v(r, b + 3), _v(r, b + 4), _v(r, b + 5))
    return p

_HS = {}
def hand_strength(hole, board, rng, n=60):
    key = tuple(board)
    smp = _HS.get(key)
    if smp is None:
        if len(_HS) > 40: _HS.clear()
        smp = []; bset = set(board); need = 5 - len(board)
        for _ in range(n):
            used = set(bset); cards = []
            while len(cards) < 2 + need:
                c = int(rng.random() * 52)
                if c not in used: used.add(c); cards.append(c)
            run = board + cards[2:]
            smp.append((B.evaluate(cards[:2] + run), frozenset(cards), run))
        _HS[key] = smp
    win = 0.0; tot = 0
    h0, h1 = hole
    for sc, used, run in smp:
        if h0 in used or h1 in used: continue
        me = B.evaluate(hole + run); tot += 1
        win += 1.0 if me > sc else (0.5 if me == sc else 0.0)
    return win / tot if tot else 0.5

class Clone:
    NAME = None
    def __init__(self):
        self.p = profile(self.NAME); self.rng = random.Random(); self.hs = {}; self.myfrac = 1.0
    def act(self, s):
        try:
            return self._pre(s) if s["street"] == "preflop" else self._post(s)
        except Exception:
            return {"action": "check" if "check" in s["legal_actions"] else "fold"}
    def _pre(self, s):
        p = self.p; legal = s["legal_actions"]; bb = s["big_blind"]; me = s["seat"]
        hole = [B.card(c) for c in s["hole_cards"]]
        top = 1.0 - B.PCT_CLASS[B._class_name(*hole)]
        hist = s["history"]; raises = [h for h in hist if h["action"] == "raise"]
        i_raised = any(h["seat"] == me for h in raises)
        i_limped = any(h["seat"] == me and h["action"] == "call" for h in hist) and not i_raised
        cur = max(s["bets"]); to_call = s["to_call"]; can_raise = "raise" in legal
        C = {"action": "call"} if to_call > 0 else {"action": "check"}
        F = {"action": "fold"} if to_call > 0 else {"action": "check"}
        def R(to):
            if not can_raise: return C
            return {"action": "raise", "amount": int(min(max(to, s["min_raise_to"]), s["max_raise_to"]))}
        big = cur >= 25 * bb
        if not raises:
            n = len(s["stacks"]); d = (me - s["button"]) % n
            limpers = sum(1 for h in hist if h["action"] == "call")
            if limpers or d == 2: o = p["iso"] if limpers else 0.0
            else: o = p["open"]["BTN" if d == 0 else "SB" if d == 1 else "CO" if d == n - 1 else "E"]
            if top < o:
                self.myfrac = max(o, 0.02)
                if self.rng.random() < p["jam"]: return R(s["max_raise_to"])
                return R((p["size"] + limpers) * bb)
            if d != 2 and top < o + p["limp"]: return C
            return F
        if not i_raised:
            if big: return C if top < p["vjc"] else F
            if i_limped and len(raises) == 1:
                return F if self.rng.random() < p["lf"] and top > 0.08 else C
            if len(raises) == 1:
                if top < p["three"]:
                    self.myfrac = max(p["three"], 0.02); return R(p["size3"] * cur)
                call = max(0.0, 1.0 - p["vofold"] - p["three"]) * (1.0 if cur <= 5 * bb else 0.5)
                return C if top < p["three"] + call else F
            if top < 0.02: return R(s["max_raise_to"])
            return C if top < 0.035 else F
        r = self.myfrac
        if big or not can_raise:
            return C if top < max(r * p["vjr"], 0.015) else F
        if top < r * p["v3raise"]:
            self.myfrac = max(0.012, r * p["v3raise"]); return R(2.3 * cur)
        if top < r * (1.0 - p["v3fold"]): return C
        return F
    def _post(self, s):
        street = s["street"]; cb, lead, sz, fS, rS, fB = self.p["post"][street]
        legal = s["legal_actions"]; me = s["seat"]; to_call = s["to_call"]; pot = s["pot"]; bb = s["big_blind"]
        hole = [B.card(c) for c in s["hole_cards"]]; board = [B.card(c) for c in s["board"]]
        hs = hand_strength(hole, board, self.rng)
        key = street + (":f" if to_call > 0 else ":b"); arr = self.hs.setdefault(key, [])
        q = bisect.bisect_left(arr, hs) / len(arr) if len(arr) >= 12 else min(1.0, max(0.0, (hs - 0.25) / 0.6))
        bisect.insort(arr, hs)
        can_raise = "raise" in legal
        def R(to):
            return {"action": "raise", "amount": int(min(max(to, s["min_raise_to"]), s["max_raise_to"]))}
        if to_call == 0:
            last = None
            for h in s["history"]:
                if h["street"] == "preflop" and h["action"] == "raise": last = h["seat"]
            rate = cb if last == me else lead
            if can_raise and (q > 1.0 - rate * 0.8 or q < rate * 0.2):
                return R(max(bb, sz * pot))
            return {"action": "check"}
        frac = to_call / float(max(1, pot - to_call))
        f = fB if frac >= 0.6 else fS
        if to_call >= 40 * bb: f = f + (1.0 - f) * 0.4
        if q < f: return {"action": "fold"}
        if can_raise and q > 1.0 - rS: return R(3.0 * max(s["bets"]))
        return {"action": "call"}

def make(name):
    return type("Agent", (Clone,), {"NAME": name})
