"""Paired test harness: hero vs random tables drawn from the realistic field.
usage: arena.py HERO.py [rounds=40] [seed0=1000] [sims=60] [pool=real|house]
Same seed -> same table composition, seat and cards for every hero, so runs are comparable."""
import sys, os, random, importlib.util, time, math
from multiprocessing import Pool
V2 = os.path.dirname(os.path.abspath(__file__)); FIELD = os.path.join(V2, 'field'); KIT = '/home/claude/kit'
sys.path.insert(0, KIT); sys.path.insert(0, FIELD)
from engine import FixedHandsTable
from engine.players import LocalPlayer
REAL = ['c_gamblerlove', 'c_chinese', 'c_sars', 'c_kojack', 'c_gamesgone', 'c_philaivey', 'c_matcha', 'c_claudebot',
        'c_jumpstreet', 'c_marketmakers', 'c_attention', 'c_nd', 'fish_joca', 'fish_lehman', 'oldbot']
_cache = {}
def load(path):
    if path not in _cache:
        spec = importlib.util.spec_from_file_location('m' + str(len(_cache)), path); m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m); _cache[path] = m.Agent
    return _cache[path]
def one(args):
    hero, seed, sims, pool, hands = args
    rng = random.Random(seed); n = rng.choice([6, 7, 7, 8])
    names = rng.sample(REAL, n - 1) if pool == 'real' else [pool] * (n - 1)
    seat = rng.randrange(n)
    H = load(hero)
    if hasattr(H, 'FIXED_SIMS'): H.FIXED_SIMS = sims
    players = []
    k = 0
    for i in range(n):
        if i == seat: players.append(LocalPlayer(H))
        else: players.append(LocalPlayer(load(os.path.join(FIELD, names[k] + '.py')))); k += 1
    random.seed(seed)
    res = FixedHandsTable(players, hands=hands, seed=seed, record=True).play()
    st = dict(vpip=0, pfr=0, vo=0, vo3=0, allin=0, flops=0)
    cat = {}
    for h in res['log']:
        raises = 0; v = r = False; inv = 0; street = 'pre'; first = None; lastpre = None; sawflop = False; folded = False
        for e in h['events']:
            if e[0] == 'post' and e[1] == seat: inv += e[2]
            if e[0] == 'board':
                if street == 'pre':
                    street = 'post'; sawflop = not folded
            if e[0] != 'act': continue
            _, s, a, amt = e
            if street == 'pre':
                if s == seat:
                    if raises == 1 and not r: st['vo'] += 1; st['vo3'] += a == 'raise'
                    if first is None: first = {'fold': 'fold', 'check': 'check', 'call': 'limp' if raises == 0 else 'call%d' % min(raises, 2), 'raise': 'open' if raises == 0 else '%dbet' % (raises + 2)}[a]
                    if a == 'fold': folded = True
                    if a in ('call', 'raise'): v = True
                    if a == 'raise': r = True
                if a == 'raise': raises += 1; lastpre = s
            elif s == seat and a == 'fold': folded = True
        st['vpip'] += v; st['pfr'] += r
        dlt = (h['end'][seat] - h['stacks'][seat]) / 20.0
        key = (first or 'none') + ('|noflop' if not sawflop else ('|PFR' if lastpre == seat else '|caller')) + ('|SD' if (sawflop and not folded and len(h['board']) == 5 and any(e[0] == 'win' and e[3] for e in h['events'])) else '')
        c = cat.setdefault(key, [0, 0.0]); c[0] += 1; c[1] += dlt
        if h['end'][seat] - h['stacks'][seat] <= -1900 or h['end'][seat] - h['stacks'][seat] >= 1900: st['allin'] += 1
    opp = {}
    k = 0
    for i in range(n):
        if i != seat: opp[names[k]] = res['chips'][i] / 20.0 / hands * 100; k += 1
    return res['chips'][seat] / 20.0 / hands * 100, st, players[seat].stats.errors, players[seat].stats.max_ms, opp, players[seat].stats.error_samples[:1], cat
if __name__ == '__main__':
    hero = os.path.abspath(sys.argv[1]); rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    seed0 = int(sys.argv[3]) if len(sys.argv) > 3 else 1000; sims = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    pool = sys.argv[5] if len(sys.argv) > 5 else 'real'; hands = int(os.environ.get('HANDS', '1000'))
    t0 = time.time()
    with Pool(2) as p: out = p.map(one, [(hero, seed0 + i, sims, pool, hands) for i in range(rounds)], chunksize=1)
    xs = [o[0] for o in out]; m = sum(xs) / len(xs); sd = (sum((x - m) ** 2 for x in xs) / max(1, len(xs) - 1)) ** 0.5
    H = hands * rounds / 100.0; S = {k: sum(o[1][k] for o in out) for k in out[0][1]}
    print('%s  bb/100 %+.1f  SE %.1f  (n=%d rounds, sd %.0f)  VPIP %.1f PFR %.1f 3bet %.0f%% stacks/1000h %.0f  errors %d max_ms %.1f  %.0fs' % (
        os.path.basename(hero), m, sd / math.sqrt(len(xs)), len(xs), sd, S['vpip'] / H, S['pfr'] / H, 100.0 * S['vo3'] / max(1, S['vo']),
        S['allin'] / H * 10, sum(o[2] for o in out), max(o[3] for o in out), time.time() - t0))
    for o in out:
        if o[5]: print('ERR', o[5][0][-600:]); break
    if os.environ.get('OPP'):
        agg = {}
        for o in out:
            for k, v in o[4].items(): agg.setdefault(k, []).append(v)
        print('  field: ' + '  '.join('%s %+.0f' % (k[2:] if k.startswith('c_') else k, sum(v) / len(v)) for k, v in sorted(agg.items())))
    if os.environ.get('CAT'):
        agg = {}
        for o in out:
            for k, v in o[6].items():
                a = agg.setdefault(k, [0, 0.0]); a[0] += v[0]; a[1] += v[1]
        for k, v in sorted(agg.items(), key=lambda x: x[1][1]): print('   %-22s n=%5d  bb/100 hands %+7.1f  (%+.2f bb each)' % (k, v[0], v[1] / H, v[1] / v[0]))
    if os.environ.get('RAW'): print('RAW', ' '.join('%.1f' % x for x in xs))
