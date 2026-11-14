import sys
pre = open('/home/claude/tools/pre_str.txt').read(); eq = open('/home/claude/v2/eqr_str.txt').read()
src = open('/home/claude/v2/bot_template.py').read().replace('"__PRE__"', repr(pre)).replace('"__EQR__"', repr(eq))
out = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/v2/bot.py'
open(out, 'w').write(src); print('wrote', out, len(src.encode()), 'bytes')
