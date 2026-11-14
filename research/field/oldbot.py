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
import random
import time

RANKS = "23456789TJQKA"
SUITS = "cdhs"

_PRE = 'AA:845,734,631,552,497,439,386;AKs:677,508,423,361,311,272,249;AKo:646,482,375,330,273,236,220;AQs:672,505,394,331,291,251,242;AQo:645,477,364,295,257,208,196;AJs:652,484,392,331,290,248,231;AJo:640,444,348,298,238,206,185;ATs:643,485,364,309,260,247,223;ATo:626,437,336,276,233,193,171;A9s:625,443,360,286,248,205,183;A9o:614,414,320,247,197,168,157;A8s:629,434,331,274,223,209,188;A8o:598,405,306,215,191,157,144;A7s:609,432,325,268,216,192,178;A7o:585,392,289,218,175,162,132;A6s:605,419,307,251,226,190,163;A6o:572,382,273,214,182,142,120;A5s:594,414,321,271,223,187,170;A5o:571,390,278,220,177,159,131;A4s:591,405,319,254,221,189,170;A4o:579,366,264,214,171,151,126;A3s:584,402,316,231,216,178,171;A3o:557,356,260,203,169,149,131;A2s:580,391,292,233,205,187,163;A2o:558,357,265,199,159,131,121;KK:814,680,598,496,427,370,329;KQs:648,472,390,308,276,248,225;KQo:620,448,348,302,250,211,182;KJs:621,469,370,313,252,249,205;KJo:611,426,325,272,242,198,168;KTs:625,440,364,292,251,227,207;KTo:597,418,321,266,233,191,160;K9s:591,414,328,276,233,207,166;K9o:587,396,297,238,199,165,147;K8s:584,398,295,264,222,185,170;K8o:561,372,290,211,166,146,115;K7s:576,383,292,244,194,196,159;K7o:558,366,262,215,161,149,122;K6s:582,395,302,227,201,171,151;K6o:548,351,249,203,161,129,112;K5s:558,370,291,221,196,171,149;K5o:534,336,244,208,150,118,112;K4s:556,372,268,231,187,174,160;K4o:511,338,251,195,147,127,112;K3s:534,360,264,221,191,163,154;K3o:510,317,229,183,145,125,107;K2s:536,360,266,221,189,157,145;K2o:497,309,227,174,140,112,96;QQ:800,648,526,450,364,311,276;QJs:593,439,350,301,270,237,203;QJo:583,415,324,267,243,192,163;QTs:596,433,342,274,251,223,191;QTo:571,401,317,255,216,199,160;Q9s:580,409,322,253,239,196,172;Q9o:569,376,290,235,192,168,153;Q8s:564,374,298,245,209,187,163;Q8o:536,352,250,213,175,144,130;Q7s:535,373,264,211,204,173,147;Q7o:520,332,246,180,161,132,97;Q6s:534,362,259,222,171,157,141;Q6o:500,313,231,183,134,118,108;Q5s:534,355,259,222,192,160,141;Q5o:501,316,214,176,150,120,99;Q4s:527,337,257,201,180,155,135;Q4o:501,311,220,159,130,110,101;Q3s:510,334,249,197,176,161,132;Q3o:496,296,202,155,135,105,89;Q2s:493,324,245,196,150,153,134;Q2o:451,287,183,153,128,107,83;JJ:775,612,494,402,350,276,242;JTs:560,435,321,296,241,220,195;JTo:544,395,323,242,218,184,169;J9s:564,393,317,256,222,192,173;J9o:524,372,286,223,190,158,144;J8s:539,385,294,241,208,178,170;J8o:509,343,267,194,176,138,115;J7s:526,356,286,218,177,165,151;J7o:489,324,235,187,158,127,109;J6s:510,338,255,213,168,148,145;J6o:484,296,213,165,128,105,90;J5s:502,336,259,201,165,141,128;J5o:482,293,197,145,128,115,92;J4s:486,323,251,183,159,139,128;J4o:466,289,194,148,126,91,85;J3s:477,313,231,197,169,137,133;J3o:459,277,197,147,117,96,77;J2s:474,302,237,192,157,149,114;J2o:442,257,172,137,110,102,84;TT:754,568,449,359,300,252,221;T9s:535,387,320,251,225,212,181;T9o:519,361,277,232,185,159,136;T8s:523,363,285,224,193,175,165;T8o:503,327,255,212,164,139,116;T7s:506,345,266,240,186,164,152;T7o:477,314,232,187,154,128,114;T6s:483,334,259,206,174,149,139;T6o:447,285,210,164,137,106,95;T5s:462,304,230,189,156,139,116;T5o:436,266,194,150,114,96,78;T4s:469,308,230,186,146,134,113;T4o:453,270,186,137,105,99,85;T3s:459,294,240,183,159,144,126;T3o:426,245,179,136,104,87,77;T2s:446,281,216,181,146,138,115;T2o:417,246,165,136,102,85,73;99:723,522,415,337,272,222,183;98s:498,365,289,244,200,171,160;98o:474,328,266,202,175,134,123;97s:498,346,251,213,191,150,154;97o:461,296,228,190,152,132,106;96s:476,325,237,197,168,169,133;96o:443,284,213,174,128,103,93;95s:457,307,227,188,156,136,116;95o:432,260,183,146,115,96,81;94s:433,283,206,164,143,124,107;94o:404,249,171,138,114,79,73;93s:436,278,213,160,147,116,117;93o:401,226,183,131,102,89,74;92s:444,267,201,164,147,132,110;92o:388,231,157,133,105,77,65;88:691,493,388,297,244,199,170;87s:475,335,265,210,197,178,152;87o:451,308,226,185,168,138,109;86s:469,327,251,203,191,150,145;86o:435,287,202,162,138,116,102;85s:454,303,212,198,165,159,118;85o:423,261,183,150,118,98,95;84s:433,283,223,166,157,130,119;84o:391,243,163,135,108,89,77;83s:410,258,187,166,132,137,102;83o:374,224,153,115,97,69,67;82s:410,252,198,156,133,116,113;82o:370,220,156,114,90,79,69;77:661,457,343,266,225,187,169;76s:447,317,252,201,188,156,152;76o:434,285,215,162,137,114,110;75s:444,290,236,183,178,147,132;75o:402,264,200,161,136,107,100;74s:412,286,218,174,147,135,118;74o:383,239,166,139,119,96,86;73s:397,258,212,171,135,120,107;73o:365,219,152,124,96,91,74;72s:381,245,179,153,133,115,97;72o:347,189,135,108,87,72,63;66:636,437,315,255,196,177,144;65s:432,313,240,200,176,154,142;65o:404,256,196,164,132,117,101;64s:424,290,226,181,157,137,131;64o:387,257,176,140,121,106,95;63s:397,269,202,160,148,119,112;63o:370,225,152,125,103,102,85;62s:380,254,194,160,118,119,108;62o:350,210,152,108,93,77,63;55:590,396,291,221,187,159,147;54s:413,278,227,189,161,149,130;54o:374,255,204,154,128,103,106;53s:397,258,211,172,151,137,131;53o:363,238,163,130,109,93,91;52s:374,253,195,154,148,137,113;52o:349,215,148,118,103,83,72;44:571,369,267,204,168,154,138;43s:383,274,200,172,142,134,118;43o:350,222,164,124,108,99,75;42s:369,243,183,152,141,118,121;42o:323,220,150,123,94,83,77;33:534,332,238,198,162,145,129;32s:359,235,181,146,125,119,114;32o:322,193,141,95,94,87,70;22:505,295,226,172,145,148,142'


def _parse_pre():
    table = {}
    for item in _PRE.split(";"):
        name, vals = item.split(":")
        table[name] = [int(v) / 1000.0 for v in vals.split(",")]
    return table


PRE = _parse_pre()


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


class _Opp:
    __slots__ = ("hands", "vpip", "pfr", "agg", "pas", "faced", "folded_to_bet", "pfaced", "pfolded")

    def __init__(self):
        self.hands = 0
        self.vpip = 0
        self.pfr = 0
        self.agg = 0
        self.pas = 0
        self.faced = 0
        self.folded_to_bet = 0
        self.pfaced = 0
        self.pfolded = 0

    def vpip_rate(self):
        return (self.vpip + 3.0) / (self.hands + 10.0)

    def pfr_rate(self):
        return (self.pfr + 1.5) / (self.hands + 10.0)

    def agg_rate(self):
        return (self.agg + 3.0) / (self.agg + self.pas + 10.0)

    def fold_rate(self):
        return (self.folded_to_bet + 4.0) / (self.faced + 10.0)

    def pre_fold_rate(self):
        """How often this seat folds when facing a preflop raise."""
        return (self.pfolded + 4.5) / (self.pfaced + 10.0)


class Agent:
    BANK_TARGET = 5.5      # seconds of the 10 s bank we allow ourselves
    MAX_THINK = 0.0022     # seconds per decision, hard ceiling

    def __init__(self):
        self.rng = random.Random()
        self.opps = {}
        self.used = 0.0
        self.seat = 0
        self.n = 8
        self.hands_total = 1000

    # ------------------------------------------------------------ callbacks
    def on_table_start(self, info):
        self.seat = info.get("seat", 0)
        self.n = info.get("num_players", 8)
        self.hands_total = info.get("hands", 1000)
        self.opps = {i: _Opp() for i in range(self.n)}

    def on_hand_end(self, summary):
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
        legal = state["legal_actions"]
        if not out:
            return {"action": "check"} if "check" in legal else {"action": "fold"}
        return out

    # ------------------------------------------------------------- learning
    def _learn(self, history):
        if not self.opps:
            return
        seen = set()
        bets = {}
        current = 0
        street = "preflop"
        pre_raised = False
        for h in history:
            s = h["seat"]
            seen.add(s)
            if h["street"] != street:
                street = h["street"]
                bets = {}
                current = 0
            a = h["action"]
            o = self.opps.get(s)
            if o is None:
                o = self.opps[s] = _Opp()
            mine = bets.get(s, 0)
            facing = current > mine
            if a in ("small_blind", "big_blind"):
                bets[s] = h["amount"]
                current = max(current, h["amount"])
                continue
            if street == "preflop":
                if facing and pre_raised:
                    o.pfaced += 1
                    if a == "fold":
                        o.pfolded += 1
            else:
                if a == "raise":
                    o.agg += 1
                elif a in ("call", "check"):
                    o.pas += 1
                if facing:
                    o.faced += 1
                    if a == "fold":
                        o.folded_to_bet += 1
            if a == "raise":
                bets[s] = h["amount"]
                current = h["amount"]
                if street == "preflop":
                    pre_raised = True
            elif a == "call":
                bets[s] = mine + h["amount"]
        # de-duplicate per-hand preflop counters
        pre_v, pre_r = set(), set()
        for h in history:
            if h["street"] == "preflop":
                if h["action"] in ("call", "raise"):
                    pre_v.add(h["seat"])
                if h["action"] == "raise":
                    pre_r.add(h["seat"])
        # every seat is dealt in every hand (stacks reset each hand)
        for s in range(self.n):
            if s in self.opps:
                self.opps[s].hands += 1
        for s in pre_v:
            self.opps[s].vpip += 1
        for s in pre_r:
            self.opps[s].pfr += 1

    # ------------------------------------------------------------ helpers
    def _budget(self, state):
        left_bank = self.BANK_TARGET - self.used
        hands_left = max(1, self.hands_total - state.get("hand_number", 1) + 1)
        per = left_bank / (hands_left * 2.5)
        return max(0.0004, min(self.MAX_THINK, per))

    def _ranges(self, state, opps):
        """Preflop percentile cut-off and postflop filter strength per opponent."""
        hist = state["history"]
        res = {}
        for s in opps:
            o = self.opps.get(s) or _Opp()
            pre_raise = pre_call = False
            post_agg = 0
            for h in hist:
                if h["seat"] != s:
                    continue
                if h["street"] == "preflop":
                    if h["action"] == "raise":
                        pre_raise = True
                    elif h["action"] == "call":
                        pre_call = True
                elif h["action"] == "raise":
                    post_agg += 1
            if pre_raise:
                cut = 1.0 - min(0.9, o.pfr_rate())
            elif pre_call:
                cut = 1.0 - min(0.95, o.vpip_rate())
            else:
                cut = 0.0
            res[s] = (max(0.0, min(cut, 0.97)), post_agg, o.agg_rate())
        return res

    def _equity(self, hole, board, opp_ranges, deadline, min_sims=60):
        """Monte Carlo share of the pot against opponents' estimated ranges."""
        rng = self.rng
        rand = rng.random
        base_used = set(hole + board)
        deck = [c for c in range(52) if c not in base_used]
        need = 5 - len(board)
        bcat = self._board_cat(board) if len(board) >= 3 else 0
        specs = [(_range_start(cut) if cut > 0 else 0, post_agg, aggr)
                 for cut, post_agg, aggr in opp_ranges.values()]
        ncombo = len(COMBOS)
        win = 0.0
        sims = 0
        perf = time.perf_counter
        hard = deadline + 0.001
        while True:
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
                        improved = evaluate(h + board)[0] > bcat
                        if not improved and not (need and _has_draw(h, board)):
                            keep = min(1.0, aggr * (0.9 if post_agg == 1 else 0.5))
                            if rand() > keep:
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
        name = _class_name(hole[0], hole[1])
        pct = PCT_CLASS[name]
        pos = (me - state["button"]) % n           # 0 btn, 1 sb, 2 bb, 3 utg ...
        hist = state["history"]
        raisers = [h["seat"] for h in hist if h["action"] == "raise"]
        callers = set(h["seat"] for h in hist if h["action"] == "call")
        to_call = state["to_call"]
        pot = state["pot"]
        can_raise = "raise" in legal
        others = [s for s in range(n) if s != me]
        table_fr = sum((self.opps.get(s) or _Opp()).fold_rate() for s in others) / max(1, len(others))
        # Opponents who give up postflop make every playable hand worth more.
        widen = max(0.0, table_fr - 0.42) * 0.9

        if not raisers:
            limpers = len(callers - {me})
            if pos == 0:
                thr = 0.62
            elif pos == n - 1:
                thr = 0.70
            elif pos == 1:
                thr = 0.68
            elif pos == 2:
                thr = 0.78
            elif pos >= n - 3:
                thr = 0.78
            else:
                thr = 0.84
            thr += 0.02 * limpers
            if limpers == 0:
                # Steal more when everyone still to act folds a lot.
                p_fold = 1.0
                k = me
                while True:
                    k = (k + 1) % n
                    if k == (state["button"] + 3) % n or k == me:
                        break
                    if state["folded"][k]:
                        continue
                    o = self.opps.get(k) or _Opp()
                    p_fold *= max(0.0, 1.0 - o.vpip_rate())
                    if k == (state["button"] + 2) % n:
                        break
                if p_fold > 0.55:
                    thr = min(thr, 0.40)
                elif p_fold > 0.35:
                    thr -= 0.10
            thr -= widen
            if pct >= thr and can_raise:
                return self._raise(state, bb * (3 + limpers) if pos != 1 else bb * 3)
            if to_call == 0:
                return {"action": "check"}
            # cheap limp behind / complete with speculative hands
            if to_call <= bb and pct >= 0.55 - widen and (limpers >= 1 or pos == 1):
                return {"action": "call"}
            return {"action": "fold"}

        # Facing a raise: equity against the involved players' ranges.
        involved = set(raisers) | callers
        involved.discard(me)
        involved = [s for s in involved if not state["folded"][s]]
        if not involved:
            return self._passive(state)
        if pct >= 0.985 and can_raise:   # AA, KK, QQ-ish: always build the pot
            cur = max(state["bets"])
            return self._raise(state, cur * 3 + (pot - sum(state["bets"])))
        deadline = t0 + self._budget(state)
        ranges = self._ranges(state, involved)
        eq = self._equity(hole, [], ranges, deadline, min_sims=80)
        po = to_call / float(pot + to_call)
        stack = state["stacks"][me]
        deep = to_call <= 0.15 * (stack + state["bets"][me])
        implied = 0.06 if deep and (name[0] == name[1] or name.endswith("s")) else 0.0
        inv_fr = sum((self.opps.get(s) or _Opp()).fold_rate() for s in involved) / len(involved)
        if deep:
            implied += max(0.0, inv_fr - 0.42) * 0.6
        nlive = len(involved)
        cur = max(state["bets"])
        mine = state["bets"][me]
        ev_call = (eq + implied) * (pot + to_call) - to_call - 0.02 * (pot + to_call)
        best, choice = 0.0, None
        if ev_call > best:
            best, choice = ev_call, {"action": "call"} if to_call > 0 else {"action": "check"}
        if can_raise:
            p_f = 1.0
            for s in involved:
                o = self.opps.get(s) or _Opp()
                cut = ranges[s][0]
                # A tight range that already put money in rarely folds.
                p_f *= o.pre_fold_rate() * min(1.0, (1.0 - cut) / 0.35)
            eq_c = max(0.0, eq - 0.08 * p_f)
            for target in (cur * 3 + (pot - sum(state["bets"])), state["max_raise_to"]):
                target = max(state["min_raise_to"], min(state["max_raise_to"], target))
                add = target - mine
                ev = p_f * pot + (1.0 - p_f) * (eq_c * (pot + add + (target - cur) * nlive) - add)
                if len(raisers) >= 3:
                    ev -= 0.1 * pot
                if ev > best + 0.03 * pot:
                    best, choice = ev, self._raise(state, target)
        return choice or self._passive(state)

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
        if to_call == 0:
            if not can_raise:
                return {"action": "check"}
            # Checking realises only part of our equity; the rest is lost to
            # bets we fold to later. On the river it is exact.
            real = 1.0 if river else 0.85
            ev_check = eq * pot * real
            best, best_size = ev_check, 0
            # Callers are stronger than the field when many hands fold.
            eq_c = max(0.0, eq - 0.12 * avg_fr) if eq < 0.7 else eq
            for frac in (0.5, 0.75, 1.0):
                b = pot * frac
                ev = p_all_fold * pot + (1.0 - p_all_fold) * (eq_c * (pot + b * (1.0 + callers)) - b)
                if ev > best + 0.02 * pot:
                    best, best_size = ev, b
            if best_size:
                return self._raise(state, int(best_size))
            return {"action": "check"}

        po = to_call / float(pot + to_call)
        raise_thr = 0.74 if nopp == 1 else max(0.5, 1.6 / (nopp + 1) + 0.1)
        if eq >= raise_thr and can_raise:
            cur = max(state["bets"])
            return self._raise(state, cur * 3 + (pot - sum(state["bets"])))
        # Semi-bluff raise against a single bettor who folds to raises a lot.
        if (can_raise and nopp == 1 and not river and eq > 0.3 and frs[0] > 0.45
                and self.rng.random() < (frs[0] - 0.3)):
            cur = max(state["bets"])
            return self._raise(state, cur * 3)
        margin = 0.04 if river else 0.0
        if eq > po + margin:
            return {"action": "call"}
        return {"action": "fold"}
