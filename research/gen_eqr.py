"""Equity of each of the 169 hand classes vs a single opponent holding the top X% of hands."""
import sys, random, json, importlib.util
from multiprocessing import Pool
spec = importlib.util.spec_from_file_location('oldbot', '/home/claude/kit/bot.py'); B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
BUCKETS = [0.015, 0.03, 0.05, 0.08, 0.12, 0.17, 0.24, 0.33, 0.45, 0.60, 0.80, 1.0]
R = "23456789TJQKA"
def job(name):
    rng = random.Random(hash(name) & 0xffffff)
    a = R.index(name[0]); b = R.index(name[1])
    c1 = a * 4; c2 = b * 4 + (0 if name.endswith('s') else 1)
    out = []
    N = len(B.COMBOS)
    for frac in BUCKETS:
        start = max(0, min(N - 10, int(round(N * (1 - frac)))))
        pool = [(x, y) for _, x, y in B.COMBOS[start:] if x not in (c1, c2) and y not in (c1, c2)]
        win = 0.0; sims = 2500
        for _ in range(sims):
            x, y = pool[int(rng.random() * len(pool))]
            used = {c1, c2, x, y}; board = []
            while len(board) < 5:
                c = int(rng.random() * 52)
                if c not in used: used.add(c); board.append(c)
            me = B.evaluate([c1, c2] + board); op = B.evaluate([x, y] + board)
            win += 1.0 if me > op else (0.5 if me == op else 0.0)
        out.append(int(round(win / sims * 1000)))
    return name, out
if __name__ == '__main__':
    with Pool(2) as p: res = p.map(job, list(B.PRE.keys()), chunksize=4)
    s = ';'.join(n + ':' + ','.join(map(str, v)) for n, v in res)
    open('/home/claude/v2/eqr_str.txt', 'w').write(s)
    d = dict(res)
    for h in ['AA', 'KK', 'QQ', 'AKs', 'AKo', 'TT', 'AJo', '77', '76s', '72o']: print(h, d[h])
