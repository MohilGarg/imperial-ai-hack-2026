"""Parametric clones of real tournament bots, fitted to their observed frequencies
(practice rounds r012-r014). Preflop: nested top-X% ranges per raise level.
Postflop: self-calibrating quantiles of hand strength so bet/fold/raise rates match."""
import random, bisect
import oldbot as B

def P(open_, size, three, call, v3fold, v3raise, vsjam, flop, turn, river, limp=0.0, jam_open=0.0, size3=3.0):
    return dict(open=dict(zip(("UTG", "MP", "CO", "BTN", "SB"), open_)), size=size, three=three, call=call,
                v3fold=v3fold, v3raise=v3raise, vsjam=vsjam, limp=limp, jam_open=jam_open, size3=size3,
                post=dict(flop=flop, turn=turn, river=river))
# post tuple: (bet, cbet, size_frac, fold_vs_bet, raise_vs_bet, raise_mult)
PROFILES = {
 "gamblerlove": P((.08,.17,.23,.34,.26), 3, .02, .12, 1.0, 0.0, .05, (.27,.48,1,.14,.14,4.2), (.32,.47,1,.17,.21,4.1), (.29,.46,1,.12,.06,4.6), size3=4),
 "chinese": P((.18,.34,.61,.84,.68), 2.5, .05, .35, .46, .10, .07, (.61,.45,.33,.41,.07,4.4), (.7,.33,.33,.39,.10,3.2), (.63,.32,.33,.37,.06,2.1)),
 "sars": P((.11,.22,.34,.35,.43), 3, .02, .16, .8, .09, .08, (.47,.81,.6,.37,.16,4), (.48,.67,.6,.19,.19,4.1), (.37,.7,.6,.26,.03,1.6)),
 "kojack": P((.15,.21,.27,.46,.43), 2.5, .08, .09, .34, .44, .2, (.26,.93,.55,.4,.04,4.8), (.27,.43,.55,.39,.03,1.5), (.25,.4,.66,.65,0,2), size3=3.8),
 "gamesgone": P((.23,.3,.33,.58,.6), 2.2, .03, .22, .09, .14, .39, (.59,.8,.5,.32,.1,4.7), (.72,.73,.5,.28,.09,2.4), (.54,.7,.5,.15,.09,5.7)),
 "philaivey": P((.21,.15,.55,.65,.67), 3, .09, .21, .28, .51, .13, (.14,.4,.55,.57,.07,3.7), (.29,.26,.8,.32,.1,4.8), (.29,.29,.75,.28,.08,4.6)),
 "matcha": P((.14,.17,.28,.28,.18), 2.5, .05, .14, .28, .53, .02, (.38,.68,.6,.43,.03,3.8), (.39,.29,.6,.23,.08,4.1), (.24,.45,.5,.41,.14,3.9), limp=.08, size3=3.6),
 "claudebot": P((.26,.21,.25,.42,.42), 11, .01, .11, .45, .02, .31, (.19,.46,.84,.53,.02,2.4), (.2,.05,.84,.29,.05,2.1), (.09,.33,.62,.3,0,2), jam_open=.6, size3=30),
 "jumpstreet": P((.12,.07,.14,.21,.19), 4.5, .05, .27, .09, .27, .09, (.4,.53,.55,.46,.03,4.2), (.5,.23,.55,.48,.07,7.8), (.4,.05,.75,.42,.04,1.2), limp=.2, size3=3.6),
 "marketmakers": P((.2,.16,.16,.22,.18), 2.5, .03, .14, .4, .46, .02, (.73,.74,.7,.5,.07,4.7), (.73,.75,.5,.17,.06,2.8), (.42,.83,.6,.57,.21,1.6), limp=.05, size3=3.6),
 "attention": P((.15,.19,.38,.93,.85), 3.5, .03, .15, .43, .27, .01, (.33,.59,.88,.7,.14,4.4), (.41,.63,1,.37,.07,8.6), (.36,.83,.63,.58,.17,3.8), limp=.1),
 "nd": P((.1,.15,.25,.11,.27), 3, .07, .15, .29, .41, .3, (.31,.83,1,.43,.1,3.7), (.35,.1,1,.23,.13,3.1), (.31,.1,.75,.26,.11,2), limp=.12, size3=4),
}

class Clone:
    NAME = None
    def __init__(self):
        self.p = PROFILES[self.NAME]; self.rng = random.Random(); self.hs = {}; self.myfrac = 1.0
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
        cur = max(s["bets"]); to_call = s["to_call"]; can_raise = "raise" in legal
        C = {"action": "call"} if to_call > 0 else {"action": "check"}
        F = {"action": "fold"} if to_call > 0 else {"action": "check"}
        def R(to):
            if not can_raise: return C
            return {"action": "raise", "amount": int(min(max(to, s["min_raise_to"]), s["max_raise_to"]))}
        big = cur >= 25 * bb
        if not raises:
            n = len(s["stacks"]); d = (me - s["button"]) % n
            pos = "BTN" if d == 0 else "SB" if d == 1 else "BB" if d == 2 else "CO" if d == n - 1 else "UTG" if d == 3 else "MP"
            o = p["open"]["SB"] * 0.5 if pos == "BB" else p["open"][pos]
            limpers = sum(1 for h in hist if h["action"] == "call")
            if top < o:
                self.myfrac = o
                if self.rng.random() < p["jam_open"]: return R(s["max_raise_to"])
                return R((p["size"] + limpers) * bb)
            if top < o + p["limp"]: return C
            return F
        if not i_raised:
            if big: return C if top < p["vsjam"] * 0.8 else F
            if len(raises) == 1:
                if top < p["three"]:
                    self.myfrac = p["three"]; return R(p["size3"] * cur)
                call = p["call"] * (1.0 if cur <= 5 * bb else 0.5)
                return C if top < p["three"] + call else F
            if top < 0.02: return R(s["max_raise_to"])
            return C if top < 0.035 else F
        r = self.myfrac
        if big or not can_raise:
            return C if top < max(p["vsjam"] * 1.5, 0.02) else F
        if top < r * p["v3raise"]:
            self.myfrac = r * p["v3raise"]; return R(2.3 * cur)
        if top < r * (1.0 - p["v3fold"]): return C
        return F
    def _hs(self, hole, board, sims=36):
        rnd = self.rng.random; used0 = set(hole + board); win = 0.0
        for _ in range(sims):
            used = set(used0); opp = []; run = list(board)
            while len(opp) < 2:
                c = int(rnd() * 52)
                if c not in used: used.add(c); opp.append(c)
            while len(run) < 5:
                c = int(rnd() * 52)
                if c not in used: used.add(c); run.append(c)
            a = B.evaluate(hole + run); b = B.evaluate(opp + run)
            win += 1.0 if a > b else (0.5 if a == b else 0.0)
        return win / sims
    def _post(self, s):
        street = s["street"]; bet_r, cbet_r, sz, vfold, vraise, rmult = self.p["post"][street]
        legal = s["legal_actions"]; me = s["seat"]; to_call = s["to_call"]; pot = s["pot"]; bb = s["big_blind"]
        hole = [B.card(c) for c in s["hole_cards"]]; board = [B.card(c) for c in s["board"]]
        hs = self._hs(hole, board)
        key = street + (":f" if to_call > 0 else ":b"); arr = self.hs.setdefault(key, [])
        q = bisect.bisect_left(arr, hs) / len(arr) if len(arr) >= 12 else min(1.0, max(0.0, (hs - 0.25) / 0.65))
        bisect.insort(arr, hs)
        can_raise = "raise" in legal
        def R(to):
            return {"action": "raise", "amount": int(min(max(to, s["min_raise_to"]), s["max_raise_to"]))}
        if to_call == 0:
            last = None
            for h in s["history"]:
                if h["street"] == "preflop" and h["action"] == "raise": last = h["seat"]
            rate = cbet_r if last == me else bet_r
            if can_raise and (q > 1.0 - rate * 0.8 or q < rate * 0.2):
                return R(max(bb, sz * pot))
            return {"action": "check"}
        frac = to_call / float(max(1, pot - to_call))
        f = vfold
        if frac > 1.0 or to_call > 30 * bb: f = f + (1.0 - f) * 0.5
        if q < f: return {"action": "fold"}
        if can_raise and q > 1.0 - vraise: return R(rmult * max(s["bets"]))
        return {"action": "call"}

def make(name):
    return type("Agent", (Clone,), {"NAME": name})
