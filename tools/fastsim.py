"""In-process simulator (no time limits) for quick strategy comparison.
usage: fastsim.py ROUNDS HANDS bot1.py bot2.py ...  (fills to 8 with house mix)"""
import sys, os, random, importlib.util, time
sys.path.insert(0, 'kit')
from engine import FixedHandsTable
from engine.players import LocalPlayer
K = 'kit/examples/'
HOUSE = [K+x for x in os.environ.get('FIELD','tight_aggressive.py,calling_station.py,random_bot.py,maniac.py,nit.py,starter.py').split(',')]
def load(p):
    spec = importlib.util.spec_from_file_location('m'+str(abs(hash(p))), p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m.Agent
rounds, hands = int(sys.argv[1]), int(sys.argv[2])
bots = sys.argv[3:]
seed = int(os.environ.get('SEED', '1'))
rng = random.Random(seed)
tot = {b: [0, 0] for b in bots}; maxms = {b: 0.0 for b in bots}; tms = {b: 0.0 for b in bots}
t0 = time.time()
for r in range(rounds):
    seats = list(bots)
    while len(seats) < 8: seats.append(rng.choice(HOUSE))
    rng.shuffle(seats)
    players = [LocalPlayer(load(p)) for p in seats]
    res = FixedHandsTable(players, hands=hands, seed=rng.random()).play()
    for i, p in enumerate(seats):
        if p in tot:
            tot[p][0] += res['chips'][i]; tot[p][1] += hands
            maxms[p] = max(maxms[p], players[i].stats.max_ms); tms[p] = max(tms[p], players[i].stats.total_ms)
for b, (c, h) in tot.items():
    print('%-40s bb/100 %+8.1f  max_ms %.2f  worst_round_think_s %.2f' % (os.path.basename(b), c / 20 / h * 100, maxms[b], tms[b] / 1000))
print('%.0fs' % (time.time() - t0))
