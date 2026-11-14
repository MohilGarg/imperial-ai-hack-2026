import sys, random, json
from multiprocessing import Pool
sys.path.insert(0, '/home/claude/kit')
from engine.cards import evaluate
R = "23456789TJQKA"

def classes():
    out = []
    for a in range(12, -1, -1):
        for b in range(a, -1, -1):
            if a == b: out.append((R[a]+R[b], a, b, None))
            else:
                out.append((R[a]+R[b]+'s', a, b, True)); out.append((R[a]+R[b]+'o', a, b, False))
    return out

def job(args):
    name, a, b, suited, nopp, sims = args
    rng = random.Random(hash((name, nopp)) & 0xffffffff)
    c1 = a*4 + 0
    c2 = b*4 + (0 if suited else 1)
    deck = [c for c in range(52) if c not in (c1, c2)]
    win = 0.0
    for _ in range(sims):
        rng.shuffle(deck)
        board = deck[:5]
        me = evaluate([c1, c2] + board)
        best = None; k = 5; ties = 1; lost = False
        for o in range(nopp):
            s = evaluate([deck[k], deck[k+1]] + board); k += 2
            if s > me: lost = True; break
            if s == me: ties += 1
        if not lost: win += 1.0/ties
    return name, nopp, win/sims

if __name__ == '__main__':
    tasks = [(n,a,b,s,k, 6000 if k<=2 else 3000) for (n,a,b,s) in classes() for k in range(1,8)]
    with Pool() as p:
        res = p.map(job, tasks, chunksize=8)
    table = {}
    for name, k, eq in res:
        table.setdefault(name, [0]*7)[k-1] = round(eq, 3)
    json.dump(table, open('/home/claude/tools/preflop_eq.json','w'))
    for h in ['AA','KK','AKs','72o','T9s','22']: print(h, table[h])
