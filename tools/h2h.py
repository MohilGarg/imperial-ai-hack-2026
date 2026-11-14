import sys, importlib.util
sys.path.insert(0,'kit')
from engine import FixedHandsTable
from engine.players import LocalPlayer
def load(p):
    s=importlib.util.spec_from_file_location('m'+p.replace('/','_').replace('.',''),p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m.Agent
hero, field, seeds = sys.argv[1], sys.argv[2], int(sys.argv[3])
tot=0
for sd in range(seeds):
    ps=[LocalPlayer(load(hero))]+[LocalPlayer(load('examples/'+field)) for _ in range(7)]
    tot+=FixedHandsTable(ps,hands=1000,seed=sd).play()['chips'][0]
print(hero, field, 'bb/100 %+.1f' % (tot/20/(10*seeds)))
