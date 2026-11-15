"""Imperial AI Hack 2026 poker bot.

Equity-driven no-limit hold'em agent:
  * preflop: precomputed equity table (169 hand classes x 1..7 opponents),
    position-aware opening ranges, range-aware Monte Carlo when facing raises;
  * postflop: time-budgeted Monte Carlo equity against opponents' estimated
    ranges (preflop percentile cut-offs plus filtering on postflop aggression);
  * opponent modelling per seat over the round: VPIP, PFR, postflop aggression
    and fold-to-bet, used both for range estimates and bluff frequency.
Standard library only. Keeps well inside 10 ms per decision and 10 s per round.
"""
import gc
import math
import random
import time

# Fewer, cheaper garbage collections: a collection pause mid-decision is the likeliest
# cause of the rare real-server timeouts.
gc.freeze()
gc.set_threshold(20000, 50, 100)

RANKS = "23456789TJQKA"
SUITS = "cdhs"

_PRE = "__PRE__"


def _parse_pre():
    table = {}
    for item in _PRE.split(";"):
        name, vals = item.split(":")
        table[name] = [int(v) / 1000.0 for v in vals.split(",")]
    return table


PRE = _parse_pre()

_EQR = "__EQR__"
BUCKETS = (0.015, 0.03, 0.05, 0.08, 0.12, 0.17, 0.24, 0.33, 0.45, 0.60, 0.80, 1.0)


def _parse_eqr():
    table = {}
    for item in _EQR.split(";"):
        name, vals = item.split(":")
        row = [int(v) / 1000.0 for v in vals.split(",")]
        for i in range(1, len(row)):          # equity never falls as the range widens
            if row[i] < row[i - 1]:
                row[i] = row[i - 1]
        table[name] = row
    return table


EQR = _parse_eqr()


def eqr(name, f):
    """Heads-up all-in equity of hand class `name` against the top fraction f of hands."""
    row = EQR[name]
    if f <= BUCKETS[0]:
        return row[0]
    for i in range(1, 12):
        if f <= BUCKETS[i]:
            lo = BUCKETS[i - 1]
            w = (f - lo) / (BUCKETS[i] - lo)
            return row[i - 1] * (1.0 - w) + row[i] * w
    return row[-1]


def _class_name(a, b):
    """a, b are int cards. Returns e.g. 'AKs', 'T9o', '77'."""
    ra, rb = a >> 2, b >> 2
    if ra < rb:
        ra, rb = rb, ra
        a, b = b, a
    if ra == rb:
        return RANKS[ra] + RANKS[rb]
    return RANKS[ra] + RANKS[rb] + ("s" if (a & 3) == (b & 3) else "o")


def _build_percentiles():
    combos = {}
    for name in PRE:
        combos[name] = 6 if len(name) == 2 else (4 if name[2] == "s" else 12)
    score = {n: 0.5 * PRE[n][0] + 0.5 * PRE[n][2] for n in PRE}
    order = sorted(PRE, key=lambda n: score[n])
    total = float(sum(combos.values()))
    pct, acc = {}, 0.0
    for n in order:
        acc += combos[n]
        pct[n] = acc / total  # 1.0 = best hand class
    return pct


PCT_CLASS = _build_percentiles()
PCT = [[0.0] * 52 for _ in range(52)]
for _x in range(52):
    for _y in range(52):
        if _x != _y:
            PCT[_x][_y] = PCT_CLASS[_class_name(_x, _y)]
# All 1326 combos sorted weakest to strongest, for sampling from "top X%" ranges.
COMBOS = sorted(((PCT[_x][_y], _x, _y) for _x in range(52) for _y in range(_x + 1, 52)))
COMBO_PCT = [c[0] for c in COMBOS]


def _range_start(cut):
    """Index of the first combo whose percentile is >= cut."""
    lo, hi = 0, len(COMBO_PCT)
    while lo < hi:
        mid = (lo + hi) // 2
        if COMBO_PCT[mid] < cut:
            lo = mid + 1
        else:
            hi = mid
    return min(lo, len(COMBO_PCT) - 20)


def card(s):
    return RANKS.index(s[0]) * 4 + SUITS.index(s[1])


def _straight_high(mask):
    m = (mask << 1) | (1 if mask & 4096 else 0)
    for top in range(13, 3, -1):
        if (m >> (top - 4)) & 31 == 31:
            return top - 1
    return -1


def evaluate(cards):
    """Best 5-card hand from 5-7 int cards as a comparable tuple."""
    counts = [0] * 13
    suits = [0, 0, 0, 0]
    smask = [0, 0, 0, 0]
    mask = 0
    for c in cards:
        r = c >> 2
        s = c & 3
        counts[r] += 1
        suits[s] += 1
        smask[s] |= 1 << r
        mask |= 1 << r
    flush = None
    for s in range(4):
        if suits[s] >= 5:
            sh = _straight_high(smask[s])
            if sh >= 0:
                return (8, sh)
            fm = smask[s]
            flush = tuple(r for r in range(12, -1, -1) if fm >> r & 1)[:5]
            break
    quad = trip = -1
    pairs = []
    singles = []
    for r in range(12, -1, -1):
        n = counts[r]
        if n == 4:
            quad = r
        elif n == 3:
            if trip < 0:
                trip = r
            else:
                pairs.append(r)
        elif n == 2:
            pairs.append(r)
        elif n == 1:
            singles.append(r)
    if quad >= 0:
        return (7, quad, max(r for r in range(13) if counts[r] and r != quad))
    if trip >= 0 and pairs:
        return (6, trip, pairs[0])
    if flush:
        return (5,) + flush
    sh = _straight_high(mask)
    if sh >= 0:
        return (4, sh)
    if trip >= 0:
        return (3, trip) + tuple(singles[:2])
    if len(pairs) >= 2:
        rest = [r for r in range(12, -1, -1) if counts[r] and r != pairs[0] and r != pairs[1]]
        return (2, pairs[0], pairs[1], rest[0])
    if pairs:
        return (1, pairs[0]) + tuple(singles[:3])
    return (0,) + tuple(singles[:5])


def _has_draw(hole, board):
    """Flush draw or open-ended straight draw that uses a hole card."""
    cards = hole + board
    for s in range(4):
        n = sum(1 for c in cards if c & 3 == s)
        if n == 4 and any(c & 3 == s for c in hole):
            return True
    mask = 0
    for c in cards:
        mask |= 1 << (c >> 2)
    hmask = 0
    for c in hole:
        hmask |= 1 << (c >> 2)
    m = (mask << 1) | (1 if mask & 4096 else 0)
    hm = (hmask << 1) | (1 if hmask & 4096 else 0)
    for lo in range(0, 11):
        w = (m >> lo) & 15
        if w == 15 and (hm >> lo) & 15:
            return True
    return False


# Real tables (16,000 hands, ~9,000 field bets): heads-up fold-to-bet rises with size,
# e.g. flop 40% at 1/2 pot, 48% at 3/4, 56% at pot; turn 41/48/61; river 54/62/72.
# A logistic shift of 1.4 per pot around the field's typical bet (0.68 pot) fits all streets.
FOLD_BETA = 1.4
FOLD_S0 = 0.68


def _fold_at(fr, frac):
    """Fold chance against a bet of `frac` pot, given a size-blind fold rate `fr`."""
    fr = min(0.97, max(0.03, fr))
    z = math.log(fr / (1.0 - fr)) + FOLD_BETA * (frac - FOLD_S0)
    return 1.0 / (1.0 + math.exp(-z))


def _made(hole, board):
    """Made-hand level using our hole cards: 0 nothing, 1 weak pair, 2 top pair/overpair,
    3 two pair, 4 trips, 5 straight or better."""
    t = evaluate(hole + board)
    cat = t[0]
    if cat >= 4:
        return 5
    hr = [c >> 2 for c in hole]
    br = [c >> 2 for c in board]
    bmax = max(br)
    if cat == 3:
        return 4 if t[1] in hr else 0
    if cat == 2:
        n_hole = (t[1] in hr) + (t[2] in hr)
        if n_hole == 2 or (n_hole == 1 and br.count(t[1]) + br.count(t[2]) < 3):
            return 3
        return 2 if (t[1] in hr and t[1] >= bmax) or (t[2] in hr and t[2] >= bmax) else (1 if n_hole else 0)
    if cat == 1:
        p = t[1]
        if p not in hr:
            return 0
        return 2 if p >= bmax else 1
    return 0


class _Opp:
    """Per-seat frequencies for one round, each with a prior so hand 1 is sane."""

    def __init__(self):
        self.hands = 0
        self.vpip = 0
        self.un_opp = [0, 0]      # unraised pot: early seats / late seats
        self.un_raise = [0, 0]
        self.vo_opp = 0           # facing one raise, not yet raised
        self.vo_raise = 0
        self.vo_call = 0
        self.v3_opp = 0           # raised, then faced a (non all-in) reraise
        self.v3_fold = 0
        self.v3_raise = 0
        self.vjr_opp = 0          # facing a jam-sized raise after raising
        self.vjr_call = 0
        self.vjc_opp = 0          # facing a jam-sized raise cold
        self.vjc_call = 0
        self.bigr = 0             # jam-sized preflop raises made
        self.agg = 0
        self.pas = 0
        self.faced = 0
        self.folded_to_bet = 0

    def vpip_rate(self):
        return (self.vpip + 2.5) / (self.hands + 10.0)

    def pfr(self, b):
        pri = 0.28 if b else 0.13
        return (self.un_raise[b] + pri * 8.0) / (self.un_opp[b] + 8.0)

    def three(self):
        return (self.vo_raise + 0.6) / (self.vo_opp + 12.0)

    def call_open(self):
        return (self.vo_call + 1.5) / (self.vo_opp + 10.0)

    def fold_open(self):
        return max(0.0, 1.0 - self.three() - self.call_open())

    def v3fold(self):
        return (self.v3_fold + 2.0) / (self.v3_opp + 5.0)

    def v3raise(self):
        return (self.v3_raise + 1.75) / (self.v3_opp + 5.0)

    def jam_call_raised(self):
        return (self.vjr_call + 3.3) / (self.vjr_opp + 6.0)

    def jam_call_cold(self):
        return (self.vjc_call + 0.6) / (self.vjc_opp + 10.0)

    def big_rate(self):
        return (self.bigr + 0.25) / (self.hands + 12.0)

    def agg_rate(self):
        return (self.agg + 3.0) / (self.agg + self.pas + 10.0)

    def fold_rate(self):
        return (self.folded_to_bet + 4.0) / (self.faced + 10.0)


class Agent:
    BANK_TARGET = 5.5      # legacy, unused by the bank model below
    MAX_THINK = 0.0018     # seconds of our own compute per decision, hard ceiling
    # Time-bank model. The server charges every decision for our compute PLUS its own
    # overhead (sending the state, our process reading it), measured on Saturday's real
    # rounds at about 1.6 ms per decision. Organisers confirmed every Agent() lives at most
    # 1,000 hands with its own 10 s bank (the 5,000-hand final is 5 blocks of 1,000 hands
    # with a fresh Agent and a fresh bank each), so budget over this Agent's own lifetime.
    OVERHEAD = 0.0016
    LIFETIME = 1000
    BANK_SAFETY = 0.85
    FIXED_SIMS = None      # testing only: exact simulation count, ignores the clock

    def __init__(self):
        self.rng = random.Random()
        self.opps = {}
        self.used = 0.0
        self.seat = 0
        self.n = 8
        self.bb = 20
        self.hands_total = 1000
        self.decisions = 0
        self.hands_played = 0

    # ------------------------------------------------------------ callbacks
    def on_table_start(self, info):
        self.seat = info.get("seat", 0)
        self.n = info.get("num_players", 8)
        self.bb = info.get("big_blind", 20)
        self.hands_total = info.get("hands", 1000)
        self.opps = {i: _Opp() for i in range(self.n)}

    def on_hand_end(self, summary):
        self.hands_played += 1
        try:
            self._learn(summary.get("history", []))
        except Exception:
            pass

    def act(self, state):
        t0 = time.perf_counter()
        try:
            out = self._decide(state, t0)
        except Exception:
            out = None
        self.used += time.perf_counter() - t0
        self.decisions += 1
        legal = state["legal_actions"]
        if not out:
            return {"action": "check"} if "check" in legal else {"action": "fold"}
        return out

    # ------------------------------------------------------------- learning
    def _learn(self, history):
        if not self.opps or not history:
            return
        n = self.n
        bb = self.bb
        big = 25 * bb
        btn = (history[0]["seat"] - 1) % n if history[0]["action"] == "small_blind" else 0
        bets = {}
        current = 0
        street = "preflop"
        raises = 0
        raised = set()
        vol = set()
        for h in history:
            s = h["seat"]
            a = h["action"]
            if h["street"] != street:
                street = h["street"]
                bets = {}
                current = 0
            o = self.opps.get(s)
            if o is None:
                o = self.opps[s] = _Opp()
            mine = bets.get(s, 0)
            if a in ("small_blind", "big_blind"):
                bets[s] = h["amount"]
                current = max(current, h["amount"])
                continue
            if street == "preflop":
                if current >= big:
                    if s in raised:
                        o.vjr_opp += 1
                        o.vjr_call += a != "fold"
                    else:
                        o.vjc_opp += 1
                        o.vjc_call += a != "fold"
                elif raises == 0:
                    d = (s - btn) % n
                    b = 1 if d in (0, 1, 2, n - 1) else 0
                    o.un_opp[b] += 1
                    o.un_raise[b] += a == "raise"
                elif s in raised:
                    o.v3_opp += 1
                    o.v3_fold += a == "fold"
                    o.v3_raise += a == "raise"
                elif raises == 1:
                    o.vo_opp += 1
                    o.vo_raise += a == "raise"
                    o.vo_call += a == "call"
                if a in ("call", "raise"):
                    vol.add(s)
                if a == "raise":
                    if h["amount"] >= big:
                        o.bigr += 1
                    raises += 1
                    raised.add(s)
            else:
                if a == "raise":
                    o.agg += 1
                elif a in ("call", "check"):
                    o.pas += 1
                if current > mine:
                    o.faced += 1
                    if a == "fold":
                        o.folded_to_bet += 1
            if a == "raise":
                bets[s] = h["amount"]
                current = h["amount"]
            elif a == "call":
                bets[s] = mine + h["amount"]
        for s in range(n):
            if s in self.opps:
                self.opps[s].hands += 1
        for s in vol:
            self.opps[s].vpip += 1

    # ------------------------------------------------------------ helpers
    def _bank(self):
        return 10.0 * self.BANK_SAFETY

    def _budget(self, state):
        """Own compute allowed for this decision, after the server's per-decision overhead."""
        life = min(self.LIFETIME, self.hands_total or self.LIFETIME)
        hands_left = max(1, life - self.hands_played)
        rate = (self.decisions + 12.5) / (self.hands_played + 10.0)   # decisions per hand, prior 1.25
        spent = self.used + self.OVERHEAD * self.decisions
        left = self._bank() - spent
        per = left / (hands_left * rate) - self.OVERHEAD
        return max(0.0, min(self.MAX_THINK, per))

    def _min_sims(self):
        return 60

    def _pre_fracs(self, state):
        """Top-fraction-of-hands range for every seat that acted voluntarily preflop."""
        n = len(state["stacks"])
        btn = state["button"]
        big = 25 * state["big_blind"]
        f = {}
        raises = 0
        raised = set()
        cur = 0
        for h in state["history"]:
            if h["street"] != "preflop":
                break
            a = h["action"]
            if a not in ("raise", "call"):
                continue
            s = h["seat"]
            o = self.opps.get(s) or _Opp()
            prev = f.get(s, 1.0)
            if a == "raise":
                amt = h["amount"]
                if s in raised:
                    x = prev * o.v3raise()
                elif raises == 0:
                    d = (s - btn) % n
                    x = o.pfr(1 if d in (0, 1, 2, n - 1) else 0)
                elif raises == 1:
                    x = o.three()
                else:
                    x = 0.03
                if amt >= big:
                    x = min(x, o.big_rate() * 1.3)
                raises += 1
                raised.add(s)
                cur = amt
            else:
                if cur >= big:
                    x = prev * o.jam_call_raised() if s in raised else o.jam_call_cold()
                elif raises == 0:
                    x = o.vpip_rate()
                elif s in raised:
                    x = prev * (1.0 - o.v3fold())
                elif raises == 1:
                    x = o.three() + o.call_open()
                else:
                    x = 0.05
            f[s] = max(0.012, min(prev, x))
        return f

    def _ranges(self, state, opps):
        """Per opponent: preflop cut-off, postflop aggression level, bluffiness."""
        fr = self._pre_fracs(state)
        bb = state["big_blind"]
        lvl = {}
        pot = 0
        bets = {}
        st = "preflop"
        cur = 0
        for h in state["history"]:
            if h["street"] != st:
                st = h["street"]
                bets = {}
                cur = 0
            a = h["action"]
            s = h["seat"]
            amt = h.get("amount", 0) or 0
            if a in ("small_blind", "big_blind"):
                pot += amt
                bets[s] = amt
                cur = max(cur, amt)
            elif a == "call":
                pot += amt
                bets[s] = bets.get(s, 0) + amt
            elif a == "raise":
                added = amt - bets.get(s, 0)
                if st != "preflop":
                    pts = 1.0
                    if cur > 0:
                        pts += 1.0             # a raise over a bet
                    if added > 0.8 * pot:
                        pts += 0.5
                    if added >= 30 * bb:
                        pts += 0.5
                    lvl[s] = lvl.get(s, 0.0) + pts
                pot += added
                bets[s] = amt
                cur = amt
        res = {}
        for s in opps:
            o = self.opps.get(s) or _Opp()
            res[s] = (max(0.0, min(1.0 - fr.get(s, 1.0), 0.985)), lvl.get(s, 0.0), o.agg_rate())
        return res

    def _equity(self, hole, board, opp_ranges, deadline, min_sims=60):
        """Monte Carlo share of the pot against opponents' estimated ranges."""
        rng = self.rng
        rand = rng.random
        base_used = set(hole + board)
        deck = [c for c in range(52) if c not in base_used]
        need = 5 - len(board)
        bcat = self._board_cat(board) if len(board) >= 3 else 0
        bmax = max(c >> 2 for c in board) if board else 0
        specs = [(_range_start(cut) if cut > 0 else 0, post_agg, aggr)
                 for cut, post_agg, aggr in opp_ranges.values()]
        ncombo = len(COMBOS)
        win = 0.0
        sims = 0
        perf = time.perf_counter
        fixed = self.FIXED_SIMS
        min_sims = min(min_sims, self._min_sims())
        hard = deadline + 0.0004
        while True:
            if fixed:
                if sims >= fixed:
                    break
            else:
                now = perf()
                if now > hard or (sims >= min_sims and now > deadline):
                    break
                if sims >= 3000:
                    break
            taken = set(base_used)
            hands = []
            for start, post_agg, aggr in specs:
                got = None
                fallback = None
                for _try in range(16):
                    # 3% of the time allow any hand: opponents make mistakes.
                    lo = 0 if rand() < 0.03 else start
                    _, a, b = COMBOS[lo + int(rand() * (ncombo - lo))]
                    if a in taken or b in taken:
                        continue
                    if fallback is None:
                        fallback = (a, b)
                    if post_agg and board:
                        h = [a, b]
                        t = evaluate(h + board)
                        cat = t[0]
                        if cat > bcat:
                            if cat >= 3 or (cat == 2 and bcat == 0):
                                sc = 3.0
                            elif cat == 1:
                                sc = 2.0 if t[1] >= bmax else 1.0
                            else:
                                sc = 1.0
                        elif need and _has_draw(h, board):
                            sc = 1.5
                        else:
                            sc = 0.0
                        if post_agg < 2.0:
                            keep = 1.0 if sc >= 1.0 else aggr * 0.9
                        elif post_agg < 3.0:
                            keep = 1.0 if sc >= 1.5 else (max(0.4, min(1.0, aggr * 1.3)) if sc >= 1.0 else aggr * 0.5)
                        elif sc >= 3.0:
                            keep = 1.0
                        else:
                            keep = (max(0.45, min(1.0, aggr * 1.1)) if sc >= 2.0 else
                                    (0.3 if sc >= 1.5 else (max(0.1, aggr * 0.5) if sc >= 1.0 else aggr * 0.2)))
                        if keep < 1.0 and rand() > keep:
                            continue
                    got = (a, b)
                    break
                if got is None:
                    got = fallback
                if got is None:
                    for a in deck:
                        if a not in taken:
                            for b in deck:
                                if b != a and b not in taken:
                                    got = (a, b)
                                    break
                            break
                taken.add(got[0])
                taken.add(got[1])
                hands.append(got)
            runout = list(board)
            while len(runout) < 5:
                c = deck[int(rand() * len(deck))]
                if c not in taken:
                    taken.add(c)
                    runout.append(c)
            me = evaluate(hole + runout)
            ties = 1
            lost = False
            for a, b in hands:
                sc = evaluate([a, b] + runout)
                if sc > me:
                    lost = True
                    break
                if sc == me:
                    ties += 1
            if not lost:
                win += 1.0 / ties
            sims += 1
        return win / sims if sims else 0.5

    def _cheap_equity(self, hole, board, nopp):
        """No-simulation estimate, used only when the time bank cannot afford Monte Carlo."""
        lv = _made(hole, board)
        base = (0.12, 0.38, 0.6, 0.74, 0.82, 0.88)[lv]
        if lv < 2 and len(board) < 5 and _has_draw(hole, board):
            base = max(base, 0.32)
        return base ** (1.0 + 0.45 * (nopp - 1))

    def _cat_partial(self, h, board):
        # category of best hand using available cards (5 or 6 total)
        return evaluate(h + board)[0]

    def _board_cat(self, board):
        cnt = {}
        for c in board:
            cnt[c >> 2] = cnt.get(c >> 2, 0) + 1
        m = max(cnt.values())
        if m >= 3:
            return 3
        if list(cnt.values()).count(2) >= 2:
            return 2
        if m == 2:
            return 1
        return 0

    @staticmethod
    def _raise(state, target):
        lo, hi = state["min_raise_to"], state["max_raise_to"]
        if lo is None:
            return None
        target = int(max(lo, min(hi, target)))
        if target >= hi * 0.8:
            target = hi
        return {"action": "raise", "amount": target}

    @staticmethod
    def _passive(state):
        legal = state["legal_actions"]
        return {"action": "check"} if "check" in legal else {"action": "fold"}

    # ------------------------------------------------------------ decisions
    def _decide(self, state, t0):
        hole = [card(c) for c in state["hole_cards"]]
        board = [card(c) for c in state["board"]]
        if state["street"] == "preflop":
            return self._preflop(state, hole, t0)
        return self._postflop(state, hole, board, t0)

    def _preflop(self, state, hole, t0):
        legal = state["legal_actions"]
        me = state["seat"]
        n = len(state["stacks"])
        bb = state["big_blind"]
        btn = state["button"]
        name = _class_name(hole[0], hole[1])
        top = 1.0 - PCT_CLASS[name]            # 0 = best hand
        pair = name[0] == name[1]
        suited = name.endswith("s")
        d = (me - btn) % n                     # 0 btn, 1 sb, 2 bb, 3 utg ...
        hist = [h for h in state["history"] if h["action"] in ("raise", "call")]
        raises = [h for h in hist if h["action"] == "raise"]
        to_call = state["to_call"]
        pot = state["pot"]
        cur = max(state["bets"])
        mine = state["bets"][me]
        stack = state["stacks"][me]
        can_raise = "raise" in legal
        call = {"action": "call"} if to_call > 0 else {"action": "check"}
        fold = {"action": "fold"} if to_call > 0 else {"action": "check"}

        if not raises:
            limpers = set(h["seat"] for h in hist)
            limpers.discard(me)
            nl = len(limpers)
            # v22: maximum-variance push (top 2 only qualify, ~9 rounds left).
            if d == 0:
                base = 0.75
            elif d == 1:
                base = 0.60
            elif d == 2:
                base = 0.10
            elif d == n - 1:
                base = 0.55
            elif d == n - 2 and n >= 6:
                base = 0.40
            elif d == 3:
                base = 0.28 if n >= 7 else 0.32
            else:
                base = 0.32
            if nl == 0 and d in (0, 1, n - 1):
                blinds = [self.opps.get(x) or _Opp() for x in ((btn + 1) % n, (btn + 2) % n) if x != me]
                if all(o.vo_opp >= 12 and o.fold_open() >= 0.82 for o in blinds):
                    base += 0.12
                elif any(o.vo_opp >= 12 and o.fold_open() < 0.55 for o in blinds):
                    base -= 0.08
            if nl:
                fishy = any((self.opps.get(x) or _Opp()).vpip_rate() > 0.5 for x in limpers)
                base = min(base, 0.20) + (0.06 if fishy else 0.0)
            if top < base and can_raise:
                size = (3.0 if d == 1 else 2.5) + nl
                return self._raise(state, int(size * bb))
            if to_call == 0:
                return {"action": "check"}
            if nl >= 1 and to_call <= bb and top < 0.6 and (pair or suited or d == 1):
                return {"action": "call"}
            return {"action": "fold"}

        fr = self._pre_fracs(state)
        agg = raises[-1]["seat"]
        o = self.opps.get(agg) or _Opp()
        f_agg = fr.get(agg, 0.15)
        involved = [s for s in fr if s != me and not state["folded"][s]]
        extra = max(0, len(involved) - 1)
        i_raised = any(h["seat"] == me for h in raises)
        odds = to_call / float(pot + to_call) if to_call > 0 else 0.0
        e = eqr(name, f_agg) - 0.05 * extra
        total = stack + mine

        # Facing a jam-sized raise: pure pot odds against their jamming range.
        if cur >= 25 * bb or to_call >= 0.4 * total:
            if e >= odds + 0.03:
                return call
            return fold

        idx_me = (me - btn - 1) % n
        idx_agg = (agg - btn - 1) % n
        ip = idx_me > idx_agg
        nb = sum(1 for s in range(n) if s != me and not state["folded"][s] and state["bets"][s] < cur)
        # v19/v20: defend more in position / big blind (Sunday: BTN/CO/BB flat calls were profitable).
        # v21: big-blind/out-of-position calls lost ~2.8bb vs folding in rounds 18-21 -> back to v15 OOP level.
        real = (1.0 if ip else 0.80) + (0.07 if (pair or suited) else 0.0) - 0.04 * min(nb, 2)

        if not i_raised:
            if len(raises) == 1:
                ncall = max(0, len(involved) - 1)
                target = int(cur * (3.0 if ip else 3.6)) + cur * ncall
                if can_raise:
                    f_cont = max(0.012, f_agg * (1.0 - o.v3fold()))
                    if eqr(name, f_cont) - 0.05 * extra >= 0.53:
                        return self._raise(state, target)
                    v3f = o.v3fold()
                    # v17: Sunday Table A, Astra folds 80% to 3-bets (n=269), test 74%. Against
                    # openers measured at >= 70% over >= 15 spots, 3-bet the top 45% every time.
                    if extra == 0 and o.v3_opp >= 6 and v3f >= 0.50 and top < 0.60:
                        add = min(target, state["max_raise_to"]) - mine
                        ev = (v3f * pot - (1.0 - v3f) * add * 0.75) * (0.9 ** nb)
                        if ev > bb:
                            return self._raise(state, target)
                    # v18: second tier. Sunday 3-bets from the blinds vs Attention made +2.8 to +5.6bb each.
                    # v21: tier-2 3-bets only in position (blind 3-bets went negative in rounds 18-21).
                    if extra == 0 and d not in (1, 2) and o.v3_opp >= 8 and v3f >= 0.58 and top < 0.33:
                        add = min(target, state["max_raise_to"]) - mine
                        ev = (v3f * pot - (1.0 - v3f) * add * 0.6) * (0.9 ** nb)
                        if ev > bb:
                            return self._raise(state, target)
                    if extra == 0 and o.v3_opp >= 5 and top < 0.28 and (suited or pair or name[0] == "A"):
                        add = min(target, state["max_raise_to"]) - mine
                        ev = (v3f * pot - (1.0 - v3f) * add * 0.75) * (0.9 ** nb)
                        if ev > bb and self.rng.random() < 0.7:
                            return self._raise(state, target)
                # v18 (Sunday, v12+ rounds): flat calls lost from the small blind vs CO/early opens
                # (-2 to -3bb, folding costs 0.5) and from early seats vs early opens (-7bb, n=30).
                d_agg = (agg - btn) % n
                if (d == 1 and d_agg != 0) or (3 <= d <= n - 2 and d_agg >= 3):
                    return fold
                if e * real >= odds and to_call <= 0.12 * total:
                    return call
                return fold
            if e >= 0.60:
                return {"action": "all_in"} if can_raise else call
            if e >= 0.5 and e * real >= odds and to_call <= 0.15 * total:
                return call
            return fold

        # I raised and got reraised (not jam-sized).
        c = o.jam_call_raised()
        e_call = eqr(name, max(0.012, f_agg * c))
        add_me = total - mine
        add_opp = max(0, total - cur)
        ev_jam = (1.0 - c) * pot + c * (e_call * (pot + add_me + add_opp) - add_me)
        ev_call = e * real * (pot + to_call) - to_call
        if can_raise and extra == 0 and ev_jam > max(ev_call, 0.0) + 2 * bb and (e_call >= 0.33 or e >= 0.5):
            return {"action": "all_in"}
        if e >= 0.60 and can_raise:
            return {"action": "all_in"}
        if ev_call > 0:
            return call
        return fold

    def _postflop(self, state, hole, board, t0):
        legal = state["legal_actions"]
        me = state["seat"]
        to_call = state["to_call"]
        pot = state["pot"]
        opps = [i for i in range(len(state["stacks"])) if i != me and not state["folded"][i]]
        if not opps:
            return self._passive(state)
        deadline = t0 + self._budget(state)
        ranges = self._ranges(state, opps)
        if not self.FIXED_SIMS and deadline - t0 < 0.0003:
            eq = self._cheap_equity(hole, board, len(opps))
        else:
            eq = self._equity(hole, board, ranges, deadline)
        nopp = len(opps)
        can_raise = "raise" in legal
        street = state["street"]
        river = street == "river"

        frs = [(self.opps.get(s) or _Opp()).fold_rate() for s in opps]
        p_all_fold = 1.0
        for f in frs:
            p_all_fold *= f
        callers = max(1.0, sum(1.0 - f for f in frs))
        avg_fr = sum(frs) / nopp
        made = _made(hole, board) if (river or street == "turn") else 9
        if to_call == 0:
            if not can_raise:
                return {"action": "check"}
            # Real tables: river bets below top pair lost about 11bb each (199 bets).
            if river and made < 2:
                return {"action": "check"}
            # Checking realises only part of our equity; the rest is lost to
            # bets we fold to later. On the river it is exact.
            real = 1.0 if river else 0.85
            ev_check = eq * pot * real
            best, best_size = ev_check, 0
            # Callers are stronger than the field when many hands fold.
            for frac in (0.5, 0.75, 1.0):
                b = pot * frac
                fs = [_fold_at(f, frac) for f in frs]
                paf = 1.0
                for f in fs:
                    paf *= f
                cl = max(1.0, sum(1.0 - f for f in fs))
                eq_c = max(0.0, eq - 0.12 * sum(fs) / nopp) if eq < 0.7 else eq
                ev = paf * pot + (1.0 - paf) * (eq_c * (pot + b * (1.0 + cl)) - b)
                if ev > best + 0.02 * pot:
                    best, best_size = ev, b
            if best_size:
                return self._raise(state, int(best_size))
            return {"action": "check"}

        po = to_call / float(pot + to_call)
        stack = state["stacks"][me]
        bet_frac = to_call / float(max(1, pot - to_call))
        lv = max(v[1] for v in ranges.values())
        raise_thr = 0.74 if nopp == 1 else max(0.5, 1.6 / (nopp + 1) + 0.1)
        if eq >= raise_thr and can_raise:
            cur = max(state["bets"])
            target = cur * 3 + (pot - sum(state["bets"]))
            # Only put a big part of the stack in as a raise with a very strong hand.
            if target - state["bets"][me] < 0.5 * stack or eq >= 0.82:
                return self._raise(state, target)
            return {"action": "call"}
        # Semi-bluff raise against a single bettor who folds to raises a lot.
        if (can_raise and nopp == 1 and not river and lv < 2.0 and eq > 0.3 and frs[0] > 0.45
                and self.rng.random() < (frs[0] - 0.3)):
            cur = max(state["bets"])
            return self._raise(state, cur * 3)
        # Real tables: calling river bets with a weak pair or less lost about 25bb each.
        if river and made <= 1 and bet_frac > 0.3:
            return {"action": "fold"}
        # v15 (Sat+Sun real hands): on the turn, calling big bets or raises with a weak pair or
        # less lost ~5-13bb per call (n~56); top pair calling a passive player's big turn/river
        # bet lost ~23bb per call (n=20). Passive players' big late bets are strong.
        if street == "turn" and made <= 1 and bet_frac >= 0.35:
            return {"action": "fold"}
        if made == 2 and bet_frac >= 0.35 and nopp == 1:
            bettor = max(opps, key=lambda s: state["bets"][s])
            if (self.opps.get(bettor) or _Opp()).agg_rate() < 0.4:
                return {"action": "fold"}
        margin = (0.04 if river else 0.0) + (0.03 if bet_frac >= 0.75 else 0.0)
        if eq > po + margin:
            return {"action": "call"}
        return {"action": "fold"}
