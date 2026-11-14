# Poker bot state (read this first when resuming)

Last updated: Sat 14 Nov 2026, 17:45. Team "Mohil'sPokerBot" (solo), Imperial AI Hack, AI Poker Bots track.

## Version map (site number = upload order)
| Site | Local file | What |
|---|---|---|
| v1 | /home/claude/kit/bot.py (old) | original loose-aggressive bot |
| v2 | /home/claude/v2/v2a.py (sha 478fa4d5) | preflop rewrite, old postflop |
| v3 | /home/claude/v2/v3a.py | strict postflop ranges |
| v4 | /home/claude/v2/v3b.py (sha 9b9add42) | v3a minus junk 3-bet bluffs and multi-barrel bluffs |
| v5 | /home/claude/v3/v6.py (sha bd815b0b) | v3b + fingerprint table, played 1 round |
| v6 | /home/claude/v3/v7.py (sha 3c4c3ad5), template /home/claude/v3/tpl_v7.py | v2a aggression + strict ranges only vs shown strength. LIVE since 17:35 |

## Real-table results (bb/100, counted rounds; one round swings about +-55)
- site v2 (v2a): +26.1, SE 14.2, 14 rounds
- site v3 (v3a): +11.5, 3 rounds
- site v4 (v3b): +4.9, SE 6.9, 13 rounds  <- tighter postflop did NOT help live
- site v5: 1 round (-46), no information
- site v6 (v7): check /api/poker/results

## What the real hands say
- Field over-folds: 71% of blinds fold to an open, 53-62% fold to a 3-bet, ~50% fold to a flop bet, 44% turn, 49% river. It calls jams 45%.
- v2a makes its money WITHOUT showdown (c-bets, barrels, raises). v3b cut turn/river betting (river c-bet 70% -> 27%) and folded more (river fold 56% -> 71%) and lost about 20 bb/100 of non-showdown profit. Pots of 90bb+: v2a net +19, v3b net +16, so the "discipline" did not pay for itself.
- Leaders (Attention Is All In, Gherkers, ~+54) are loose and aggressive: open 27-45%, 3-bet 17-25% from the blinds.

## Simulation: how far to trust it
- Harness: /home/claude/v3/arena.py HERO.py ROUNDS SEED0 60 real|strong (env RAW=1 for paired.py, CAT=1 breakdown, OPP=1, HERO_ATTR=K=V,...). Clones in /home/claude/v3/field2 (regbase2.py, fitted from /home/claude/v3/profiles.txt, 21 counted rounds), pool weights in field2/pool.json.
- Known bias: clones pay off at showdown. For v2a the sim matches real non-showdown categories well but overstates showdown profit by ~8 bb/100; for v3b by ~30. So the sim OVERRATES strict/value-heavy styles. Sim says v3b +54, v7 +44, v2a +42 (seed 3000, 96 rounds, SE 6); real says v2a > v3b. Trust real tables over the sim for style choices; use the sim for bugs, timing and preflop-level changes.
- Strong table (top-5 clones + 2 copies of v3b): v7 +24.0 (SE 6.5), v2a +14.6 (SE 7.0), v3b +21.9 (SE 4.5).
- Fingerprint table (v6.py, gen_fp.py, fp_str.txt, patch7.py): +2.3 (SE 2.9) on one pool, -2.1 (SE 2.6) on the other. No detectable gain, NOT shipped.

## How to upload
1. cd /home/claude/imperial-ai-hack-2026 && git checkout bot-staging && cp <bot> bot.py && commit && git -c push.negotiate=true push origin bot-staging && git checkout main. Note commit sha and sha256sum bot.py.
2. Built-in browser tab on https://imperialaihack.com/pokerbots (tabId usually "seed"; the user must be logged in). In page JS: fetch https://raw.githubusercontent.com/MohilGarg/imperial-ai-hack-2026/<commit>/bot.py, check SHA-256, wrap in File('bot.py'), set on #pk-file via DataTransfer, dispatch 'change', wait 4.5 s, read #team text for "loaded fine in the sandbox".
3. Timing check before any upload: cd /home/claude/kit && python3 local_sim.py <bot> <6 clone files> --rounds 2 (0 errors, ~0 timeouts, think < 6 s).
Data: token on the page ("--token X"); GET /api/poker/results and /api/poker/hands?ref=... with Authorization: Bearer X. Analyse in page JS (shell cannot reach the site).

## Schedule and rules that matter
- Sat uploads close 19:30. The bot live at 19:30 plays Sunday's first rounds.
- Sat 20:30: Sunday bucket tables announced on the poker page.
- Sun 09:00-11:55: bucket rounds every 5 min at ONE fixed table; score is cumulative chips; top 2 per table reach the final. Uploads open 09:00-12:00.
- Sun 12:05 final: 8 bots, 5,000 hands (bot throttles itself for the time bank).
- Devpost: public repo, last commit before Sun 12:00; Mohil still has to join the hackathon on Devpost and add team details.

## Decision rules
- Sat 19:15: if site v6 (v7) real mean is below site v2's (+26.1) by more than its SE, re-upload v2a; otherwise keep v7.
- Sunday: after each ~6 rounds compare cumulative chips with the table; only switch bots on real evidence at that table or a clear bug. Never upload without the timing check.
