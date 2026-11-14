"""Build the embedded fingerprint table from profiles.txt (shrunk toward field averages)."""
import sys
rows = {}
for line in open('/home/claude/v3/profiles.txt', encoding='utf-8'):
    if '|' in line:
        n, v = line.rstrip('\n').split('|'); rows[n] = [int(x) for x in v.split(',')]
F = rows.pop('FIELD')
only = sys.argv[2] if len(sys.argv) > 2 else 'all'
def v(r, i): return r[i] if r[i] >= 0 else F[i]
def shr(r, i, ni, gen, k=10.0):
    n = max(0, r[ni]); return (v(r, i) * n + gen * k) / (n + k)
out = []
for j, (name, r) in enumerate(rows.items()):
    if only == 'even' and j % 2: continue
    if only == 'odd' and not j % 2: continue
    hands = r[0]; w = hands / (hands + 1500.0)             # few hands -> lean on the field
    mix = lambda x, g: x * w + g * (1 - w)
    pfrE = mix(v(r, 2), 19); pfrL = mix(0.45 * v(r, 3) + 0.35 * v(r, 4) + 0.20 * v(r, 5), 45)
    three = mix(v(r, 11), 8); vof = mix(v(r, 10), 78); callo = max(1.0, 100 - vof - three)
    v3f = shr(r, 13, 15, 60); v3r = shr(r, 14, 15, 16); vjr = shr(r, 16, 17, 50); vjc = shr(r, 18, 19, 6, 20.0); lf = shr(r, 20, 21, 50)
    pb = mix(v(r, 43), 41); nb = mix(v(r, 44), 27); fp = mix(v(r, 45), 50); limp = mix(v(r, 6), 3)
    size = v(r, 7) / 10.0
    b = 5 if v(r, 8) >= 50 else (0 if size < 2.3 else 1 if size < 2.75 else 2 if size < 3.25 else 3 if size < 4.0 else 4 if size < 12 else 5)
    vals = [pfrE, pfrL, three, callo, v3f, v3r, vjr, vjc, lf, pb, nb, fp, limp, vof]
    out.append(','.join(str(int(round(min(99, max(1, x))))) for x in vals) + ',' + str(b))
open(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/v3/fp_str.txt', 'w').write(';'.join(out)); print(len(out), 'profiles')
