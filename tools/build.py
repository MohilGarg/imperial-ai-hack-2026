import sys
pre = open('tools/pre_str.txt').read()
src = open('tools/bot_template.py').read().replace('"__PRE__"', repr(pre))
out = sys.argv[1] if len(sys.argv) > 1 else 'kit/bot.py'
open(out, 'w').write(src)
print('wrote', out, len(src.encode()), 'bytes')
