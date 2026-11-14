import sys, importlib.util, collections
sys.path.insert(0,'kit')
from engine import FixedHandsTable
from engine.players import LocalPlayer
def load(p):
    s=importlib.util.spec_from_file_location('m'+p.replace('/','_').replace('.',''),p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m.Agent
hero, field = sys.argv[1], sys.argv[2]
cat=collections.Counter(); cnt=collections.Counter(); tot=0
for sd in range(3):
    ps=[LocalPlayer(load(hero))]+[LocalPlayer(load('examples/'+field)) for _ in range(7)]
    res=FixedHandsTable(ps,hands=1000,seed=sd,record=True).play(); tot+=res['chips'][0]
    for h in res['log']:
        d=h['end'][0]-h['stacks'][0]
        acts=[e for e in h['events'] if e[0]=='act' and e[1]==0]
        streets=[]; st='pre'
        for e in h['events']:
            if e[0]=='board': st=e[1]
            if e[0]=='act' and e[1]==0: streets.append(st)
        last = streets[-1] if streets else 'none'
        k=(acts[-1][2] if acts else 'none')+'@'+last+('/SD' if '0' in h.get('showdown',{}) else '')
        cat[k]+=d; cnt[k]+=1
print(hero, 'bb/100 %+.0f'%(tot/600))
for k,v in sorted(cat.items(), key=lambda x:x[1]): print('  %-22s n=%4d  bb=%+.0f'%(k,cnt[k],v/20))
