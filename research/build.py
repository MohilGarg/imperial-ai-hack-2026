import sys
pre = open('research/pre_str.txt').read(); eq = open('research/eqr_str.txt').read()
tpl = sys.argv[2] if len(sys.argv) > 2 else 'research/bot_template.py'
fp = open(sys.argv[3] if len(sys.argv) > 3 else 'research/fp_str.txt').read()
src = open(tpl).read().replace('"__PRE__"', repr(pre)).replace('"__EQR__"', repr(eq)).replace('"__FP__"', repr(fp))
out = sys.argv[1] if len(sys.argv) > 1 else 'bot.py'
open(out, 'w').write(src); print('wrote', out, len(src.encode()), 'bytes')
