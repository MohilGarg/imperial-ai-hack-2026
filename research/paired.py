import sys, math
def raw(f): return [float(x) for x in [l for l in open(f) if l.startswith('RAW')][0].split()[1:]]
a = []; b = []
for i in range(1, len(sys.argv), 2): a += raw(sys.argv[i]); b += raw(sys.argv[i + 1])
d = [y - x for x, y in zip(a, b)]; m = sum(d) / len(d); sd = (sum((x - m) ** 2 for x in d) / (len(d) - 1)) ** 0.5
print('A %+.1f  B %+.1f  diff(B-A) %+.1f  SE %.1f  n=%d' % (sum(a) / len(a), sum(b) / len(b), m, sd / math.sqrt(len(d)), len(d)))
