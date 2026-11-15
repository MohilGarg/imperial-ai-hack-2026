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
- README.md on main describes site v6 (v7.py) as the submitted bot; update it and bot.py on main if the live bot changes.

## Added 17:55 Sat: real-hand evidence by situation (31,000 hands, all versions)
- Opens: our weakest opened hands are about break-even in every position (BTN top 32-40%: +0.1bb, SE 1.4; CO 24-32%: +0.2, SE 2.3; EP 16-24%: +0.1, SE 1.3). No support for wider opens. v8 (/home/claude/v3/v8.py, wider opens + more 3-bets) is -0.4 (SE 3.8) in sim. NOT shipped.
- 3-bets: all the profit is in the top 6% of hands (top 0-3%: +11.7bb each, SE 2.5; 3-6%: +6.1, SE 2.7). Beyond that it is zero or negative (20%+ bluffs: -2.0, SE 1.5). No support for wider 3-bets.
- Flat calls: in position fine (+1 to +3bb). From the small blind they lose (298 calls, about -3.3bb each, SE 1.9, vs -0.5 for folding). Big-blind calls with top 20-50% hands lose about 3bb (vs 1bb for folding).
- v9 (/home/claude/v3/v9.py, template tpl_v9.py) = v7 + never flat-call from the small blind + slightly tighter big-blind calls. Sim: +1.8 (SE 2.1, 192 rounds) vs v7; strong table +3.5 (SE 4.6). Same direction as the real hands but below the 2-SE ship rule, so NOT shipped. Waiting for Mohil's OK.
- Hand ranking table for page-JS analysis: /home/claude/v3/top_pct.json (class -> top %).
- Standings at 17:45: 16th of ~38, +13.0 over 33 rounds. Leader Gherkers +62.

## Update 18:06 Sat: NEW LIVE BOT = site v7 = /home/claude/v3/v10.py (template tpl_v10.py, sha 02187dea), uploaded 18:05:45
- v10 = v7 (site v6) + river rules: check the river without top pair or better (_made level < 2); fold a weak pair or less to river bets > 30% pot.
- Real-hand evidence (36,000 hands): river bets below top pair lost ~11bb each over 199 bets (~6 bb/100); river calls with a weak pair lost ~29bb each (n=20).
- Top bots (from our tables): Gherkers +61 and Attention +52 make all their profit at showdown (+68/+75 bb/100) and lose slightly without showdown; they almost never bluff the river. They open far wider late (SB 86-95%, BTN 64-69%) and 3-bet 15-17%, but our own opens beyond our current ranges were break-even, so ranges unchanged.
- Sim: +4.8 (SE 2.0, 192 rounds) vs v7 on the real field; +3.3 (SE 3.7) on the strong table. Timing 0.9 s/round, 5,000-hand run fine.
- 19:10 DECISION RULE (replaces the earlier one): site v7 will have only ~13 rounds. Keep site v7 unless it is below site v2 (+26.1) by more than 2x its SE, or shows errors/timeouts. Do not revert on noise.
- v9 (no small-blind flat calls) still not shipped; could be combined with v10 if Mohil agrees.

## 19:11 Sat check (done): keep site v7 (v10.py). Real: +32.9 bb/100, SE 10.8, 12 rounds (v2 was +26.1, SE 14.2). No flags, last load check OK (sha 02187dea). No upload made. Site v7 plays Sunday from 09:00 unless replaced.

## Window 1 progress, paused 23:22 Sat at Mohil's request (switching model). Nothing uploaded, staged or scheduled yet.
- Final Saturday: site v7 (v10.py) +26.9 bb/100 over 16 rounds (SE ~9). We finished 9th at +17.6. Sunday = Table A (7 bots): Attention Is All In, Kojack, us, Astra La Vista, gamblerlove, munchlax, test.
- Table A profiles (43-int clone format) saved in /home/claude/v3/tableA.txt and merged into profiles.txt (backup profiles_backup.txt). New clones field2/c2_gamblerlove.py, c2_munchlax.py. arena.py has pool 'tableA'. v10 on it: +14.2 (SE 4.6) but the Attention clone scores -5 (real +52), so the Table A sim does NOT predict rank.
- At our tables so far: Attention +52 (5 rounds), Kojack -9 (6), Astra -4 (8), gamblerlove +4 (10), munchlax -20 (5), test -3 (10). Notable: Attention folds 77% to 3-bets (n=398) and 74/85/96% to big bets by street; test folds 81% to flop bets and 89% to 3-bets; Kojack folds only 29% to small flop bets.
- Timeouts: results API has timeouts and think_s per round. Server think is ~2.7 s per round, about 1.8 ms overhead per decision even preflop, so postflop decisions run near 5.5 ms of the 10 ms limit. v7 timed out 9 times in 16 rounds. Planned fix (not built): MAX_THINK 2.5 -> 1.8 ms, hard stop +1.0 -> +0.4 ms, gc.disable() with gc.collect() in on_hand_end. RISK TO RAISE WITH ORGANISERS: at 2.7 s per 1,000 hands, the 5,000-hand final needs ~13.5 s; if the 10 s bank is not scaled, every bot runs out.
- Calibration (unfinished): /home/claude/v3/calib.py compares sim and real showdown stats. Non-showdown profit matches real (v2a +19 vs +16; v10 +2 vs +3). The whole gap is showdown: sim SD profit +35 to +69 vs real +10 to +24; sim has more showdown wins per 100 hands (1.76 vs 1.1-1.5) and bigger pots (avg win +75-82bb vs +57-71). Field river-bet weakness matches (33% vs 36%). Next step was splitting SD pots into preflop all-ins vs postflop (calib.py now prints preW/preL/postW/postL; the matching real numbers still need pulling in page JS).
- Still to do: finish or abandon calibration (90 min cap), re-measure small-blind flat calls with halves on all 54 rounds, timing fix build + tests, stage one build, replace the three stale Sunday triggers with 09:01 / 09:40 / 10:30 / 11:20 / 11:35 tasks, final summary.

## WINDOW 1 RESULT (Sat 23:55). READ THIS SECTION FIRST ON SUNDAY.
STAGED FOR 09:01: site upload of v11 = /home/claude/v3/v11.py (template tpl_v11.py)
  commit 9647537661694b10b3e9261e821bc6bdad83ba1d on bot-staging, sha256 130640fd1a1c4575bf6f1e5e4acf2c42dbb6719e4bb7fe5bf77ef666964ae355
ALTERNATIVE FOR THE FINAL ONLY: v11s = /home/claude/v3/v11s.py
  commit 5b5d7f92a1496e909548e6a9da78a60de349840b, sha256 fd619e48ac069f81073e9245b38b023e7be18b7038af688dd0fb3d8cb658eef3
  Upload v11s before 11:45 ONLY IF Mohil confirms the organisers scale the time bank for the 5,000-hand final (e.g. 50 s). Otherwise keep v11.
ROLLBACK: v10.py (site v7), commit 40c0f83fddc1b43903da5a04704d440209b20375, sha256 02187dea8f47cb2e926be257ac75e3824492d9055dc1ca7f216d16c63b03e712.

v11 = v10 strategy unchanged (identical action logs with seeded randomness over 300 hands) + timing:
- Per-decision compute ceiling 2.5 -> 1.8 ms, hard stop +1.0 -> +0.4 ms, gc.freeze() and higher gc thresholds (pauses were the likely cause of the rare real timeouts: 9 in 16 v7 rounds).
- Bank model counts the server's per-decision overhead (OVERHEAD = 1.6 ms, from Saturday's real think_s: 1.59 ms per preflop decision, 5.0 ms per postflop). BANK_SCALES=False assumes a 10 s bank even for 5,000 hands. When the remaining bank can't afford simulation, postflop uses a no-simulation estimate (_cheap_equity): costs about 14 bb/100 (SE 5.3) vs simulation, far less than running out of bank.
- In 1,000-hand bucket rounds v11 and v11s behave identically (bank 10 s either way); local think 0.8 s vs 0.9 s for v10, 0 timeouts.
- Final scenario, local, 5,000 hands, 10 s bank: v10 used 3.7 s of own compute, v11 1.3 s, v11s 3.4 s. On the server add roughly 8-9 s of overhead: v10 would run out of bank around hand 3,900; v11 stays near the limit (may run out in the last ~100-200 hands); v11s needs a scaled bank.

Evidence-standard results (window 1):
- Small-blind flat calls (never flat-call from SB): FAILED. All 54 rounds: 524 calls, -0.68 bb each vs -0.5 for folding (z = -0.13); halves opposite signs (-2.09 then +0.76). Not shipped.
- Table-tuned starting assumptions: NOT ATTEMPTED; seats are anonymous and the fingerprint test already showed no gain. The bot's per-seat model already learns each opponent's fold-to-3-bet etc. within a round.
- Simulator calibration: ABANDONED (cap). Non-showdown profit matches real tables (v2a sim +19 vs real +16; v10 +2 vs +3); the whole error is at showdown (sim +35 to +69 vs real +10 to +24, more and bigger showdown wins). Root cause not fixed. Sim = bug and regression screen only. Table A sim exists (arena pool 'tableA') but the Attention clone loses (-5 vs real +52), so it can't predict rank.

Table A notes (from our stored hands; small samples):
- Attention Is All In: +52 at our tables (5 rounds). Opens 30/44/64/86% (EP/CO/BTN/SB), folds 77% to 3-bets (n=398), folds 74/85/96% to big bets by street. Strongest bot here.
- Kojack: -9 at our tables (6 rounds). Folds only 29% to small flop bets (sticky), 68% to 3-bets. Main rival for 2nd.
- test: folds 81% to flop bets and 89% to 3-bets. munchlax: -20 at our tables (5 rounds), weakest. Astra La Vista -4, gamblerlove +4.
- Our live bot already adapts per seat within each round, so no Table A-specific change was shipped.

SUNDAY RULES:
- 09:01: upload v11 (fetch by commit SHA from raw.githubusercontent.com in page JS on imperialaihack.com/pokerbots, verify sha256, set on #pk-file, dispatch change, confirm "loaded fine in the sandbox").
- Checks: Table A chips and rank (page "Sunday bucket tables"), our timeouts/errors/flags (from /api/poker/results: fields timeouts, errors, bank_out, think_s, violations). Roll back to v10 on any error, bank_out, flag, or timeouts clearly worse than v10's (v10 averaged 0.6 per round). No strategy changes during bucket rounds.
- Final bot decision by 11:45: v11 unless the organisers confirmed a scaled bank (then v11s).
- 11:35: main must have the live bot.py, template in research/, honest README; push before 11:50. Remind Mohil about Devpost.

## Scheduled tasks (set 23:29 Sat)
09:01 upload v11 (trig_01Ka4aCRGPw6HqTSvXHUUiMR), 09:40 check (trig_01Cosnu6eo2evvcH831ZqZMQ), 10:30 check (trig_018HJiRhjM7e4bm992pomQzN), 11:20 check + final-bot decision (trig_01PqGfEr7LoBFkpmgWfbaMBZ), 11:35 repo freeze + Devpost reminder (trig_013TBtGuNFi3A8cHcPs5CDUS).
STALE 09:12 task (trig_011ZB2yQz2Mb7oRLt3ZSupTE, "Poker: Sunday check 1") could not be deleted (permission denied). If it fires: do ONLY the health check in the Sunday rules above. Do not make strategy changes or uploads other than a rollback to v10 on a clear problem.

## 01:05 Sun: STAGED BUILD IS NOW v12 (supersedes v11 above)
v12 = /home/claude/v3/v12.py (template tpl_v12.py). Commit 3cdae317e2747e5b6c063a2dd0a81b0b1d890a78 on bot-staging,
sha256 77de8415bb91ab24542eb3efbf114727b937a06569d9584061c9ce52df64a2db. Approved by Mohil 00:59.
Validation (/tmp/val/val.py): 2 x 1,000-hand blocks, fresh Agent each. Seeded fixed-sims: v11 and v12 identical hashes,
0 caught exceptions. Real clock: max decision 4.9 ms, ~2.4 s of 10 s modelled bank, 0 cheap fallbacks, with info hands=1000
AND 5000. v11 with hands=5000 uses cheap fallback on every postflop decision (~200/block) -> v12 preferred.
Scheduled tasks updated: 09:01 uploads v12 (or an approved v13+ recorded here), 10:30/11:20/11:35 reference v12. Rollback stays v10.
v13 work: Mohil wants strategy/memory improvements. Evidence standard applies: only ship if measured on real hands.

## 01:40 Sun: v13 CANDIDATE (NOT approved for upload yet; 09:01 uploads v12 unless Mohil approves v13 here)
v13 = /home/claude/v3/v13.py (template tpl_v13.py) = v12 + size-dependent fold model in postflop bet sizing:
fold(frac) = logistic(logit(fold_rate) + 1.4*(frac-0.68)). Old model assumed size-blind folds, so EV was linear in size
and the bot only bet 0.5 or 1.0 pot, mostly 0.5 with weak hands.
Evidence (real v7 hands, 16 rounds, 16,000 hands; field bets ~9,000): heads-up fold-all rises with size on every street
(flop 40/48/56/59% at .5/.75/1/big; turn 41/48/61/72; river 54/62/72/80). Our bets: 36% at .5 vs 60% at 1.0.
Sim paired vs v12: Table A pool +6.1 (SE 1.1, n=384); real pool +0.1 (SE 1.5, n=384). Errors 0, timing OK (val.py 2x1000
hands, max 5 ms, ~2.4 s bank, hands=5000 OK; local_sim 0 timeouts, 1.8 s/round).
Commit 3a2f79a198c3234000cce57d45762e541607def6 on bot-staging, sha256 281aadee18aae4be9ba533aa7d421182d4f3187d65d302b30eca44ded427fb17.
Other findings: all-in fold-equity bug never occurred (0 of 1,524 bets) -> no patch. Calls vs folding gain on nearly every
street/level -> no calling change. Seat names are not given to the bot -> no team-profile memory. v13b (heads-up pot-size
river bluffs) sim +1.8 (SE 1.2) tableA, -1.0 (SE 1.6) real -> dropped.

## 08:51 Sun: MOHIL APPROVED v13 FOR THE 09:01 UPLOAD
Upload v13: commit 3a2f79a198c3234000cce57d45762e541607def6 on bot-staging,
sha256 281aadee18aae4be9ba533aa7d421182d4f3187d65d302b30eca44ded427fb17 (page should show SHA 281aadee).
Rollback order: v12 (commit 3cdae317e2747e5b6c063a2dd0a81b0b1d890a78, sha256 77de8415...) on any strategy doubt;
v10 (commit 40c0f83f..., sha256 02187dea...) on any technical problem with both.
Health checks judge v13 on errors/timeouts/bank_out first; one bad round is not a reason to roll back.
Next: keep improving using Sunday bucket hands (ref "sunday/..."), same evidence standard; last upload 11:45.

## 09:00:45 Sun: v13 UPLOADED AND LIVE (done manually at 09:00). Page: SHA 281aadee, 'loaded fine in the sandbox'. 09:01 task need not upload again.
- 09:12 check (stale 09:12 task): r003 v13 +4651 (+23.3), clean (0 miss/err/bank). Table A: Astra +20247, us +6019 (2nd), Kojack -2066 (3rd). No change.
- 09:18 r004 v13 -2832 (-14.2) clean. Table A: Astra +27591, us +3187 (2nd), test -119 (3rd, gap 3306). v13 HU flop pot bets 70% fold (n=178), turn 51% (n=68).
- 09:40 thru r008: v13 7 rounds -17233 (-12.3). Table A: Astra 41588, Attention 16509, test -2848, Kojack -5664, us -15913 (5th). v14 (cap+jam) failed sim vs v13 (-4.6 SE1.1 tableA, -6.6 SE1.5 real; cap -5.3, jam -1.5) -> not shipped. Recommended rollback to v12; awaiting Mohil.

## 09:41:37 Sun: v12 UPLOADED AND LIVE (Mohil approved rollback from v13). SHA 77de8415, loaded fine. v13 retired (7 live rounds -12.3 bb/100). v14 not shipped.
- 09:44 r009 v13 -1452 (last v13 round). Us -17365 (6th); 3rd gamblerlove -4399 (gap 12966); 2nd Attention 18740 (gap 36105). v12 live from r010.
- 09:47 r010 v12(site v9) -1348 (-6.7) clean. Stacks won 3 lost 4 (3 coolers: AK 2pair vs set, AK 2pair vs straight, QQ full vs aces full; 1 bad: 88 vs AQ trips on QKQ). nonSD +5504, SD -6852. Us -18713 (6th), 3rd gamblerlove -3348 (gap 15365).
- ~10:02 v15 CANDIDATE staged (commit 5e6d926f6b7039a4eba3308bdbd7d6dbd53a53a4, sha256 559b51297320f931db0c0ae246316d4598e114b40546b9a10c322655e20a808d) (v12 + fold weak pair to turn bets>=35% pot; fold top pair to passive (agg<0.4) bettor's turn/river bet>=35% HU). Real-hand basis: weak/no-pair calls vs big bets/raises -5..-13bb each; top pair vs passive big turn/river bets -21bb (n=17). Sim vs v12: tableA -0.2 (SE1.2), real -1.2 (SE1.4) = no harm. Awaiting Mohil.
- 09:59 v12 rounds: r010 -1348, r011 -2361, r012 +78. Stacks lost mostly coolers; r011 3J (bottom pair) stack-off = v15 rule case. Us -20996 (5th); 3rd test +1033 (gap 22029); 2nd Attention +33517 (gap 54513). Top-2 now unlikely.

## 09:59:38 Sun: v15 UPLOADED AND LIVE (Mohil approved). SHA 559b5129, loaded fine. Rollback: v12 (commit 3cdae317..., sha 77de8415). Site label will be v10.
- 10:07 v16 CANDIDATE (not uploaded): v15 + wider opens (BTN .50, SB .42, CO .35, HJ .25, EP .16/.19) + no turn/river raises with made<=2. Commit d749b7e1027dab8596232a5b62470488d52271c4 sha256 9818cefe09291d26e2ac25a31c3653bb5c262a0fd14c736869f4062d56fa6972. Checks: 0 exc, max 4.3 ms; sim tableA +15.4 vs v15 +16.1 (diff -0.7, SE 2.4, n=96), VPIP 23.2 PFR 16.7. Not certain it is better -> awaiting Mohil.
- 10:08 r013 v15(site v10) +4898 (+24.5), miss=2, stacks +3/-2 (both coolers). Us -16098 (5th); 3rd test -1025; 2nd Attention +36915 (gap 53013).
- 10:07 r014 v15 +4391 (+22.0), miss=0. v15 2 rounds +9289. Us -11707 (5th); 3rd test -1819 (gap 9888); 2nd Attention +41339 (gap 53046).
- 10:12 v16 checks on 30 real rounds (16 Sat + 14 Sun): (1) turn/river raises with <=one pair facing a bet: n=19, +13..+29bb avg -> no-raise rule NOT supported. (2) marginal opens: BTN top30-40% -0.17bb (n=133), SB top20-40% ~-0.44bb (n=101), CO top30-40% -1.11bb (n=24); steals succeed only ~42-46% -> wider opens NOT supported. Recommend stay on v15; v16 shelved.
- 10:18 v17 CANDIDATE: v15 + 3-bet top 45% vs openers with fold-to-3bet>=0.70 (v3_opp>=15). Real: Astra folds 80% to 3-bets (n=269), test 74%; anyone re-raising Astra +1.26bb (n=673), us +2.87 (n=19), vs test us +2.92 (n=38). Sim tableA vs v15 -1.2 (SE2.3), 3bet 5->8%. 0 exc. Commit c7e589731b71ad299049d49805ded0b5c11fb3af sha256 9ea5dae1a3a27cd5f9ddf6cac4e913a3aa91b250a956182be2a95eba9fae8c21. Awaiting Mohil.
- 10:19 r015 v15 +455 (+2.3) clean, stacks +3/-1 (JJ vs KK). v15 3 rounds +9744. Us -11252 (5th); 3rd test -3776 (gap 7476); 2nd Attention +51087 (gap 62339).

## 10:16:22 Sun: v17 UPLOADED AND LIVE (Mohil approved). SHA 9ea5dae1, loaded fine. Site label probably v11. Rollback: v15 (commit 5e6d926f..., sha 559b5129). Watch: our 3-bet rate, results of 3-bets vs Astra/test.
- 10:20 r016 v15 -2279 (-11.4), miss=1. Study: opens +141bb, 3bets +26bb, callOpen -144bb, showdown 18 hands -138bb (K6h straight vs higher straight cooler; Q3s Q+99 vs AQ kicker). Sunday preflop by line: 3bets +3.7..+7.6bb each (n=313) -> supports v17; opens -0.5bb (n=1711, break-even) -> don't widen; SB flat calls -3.0bb (n=151) vs fold -0.5 (Sat +1.6, mixed).

## 10:24:30 Sun: v18 UPLOADED AND LIVE (Mohil asked: go for upside, build v18 and upload). Commit 915f534c3daf04883f061263728af86bce4ca7b9, SHA 3f1ab65e, loaded fine.
v18 = v17 + 3-bet tier 2 (v3fold>=0.58, n>=8, top 33%) + no flat calls SB vs non-BTN opens and EP vs EP opens. Sim tableA vs v15 +4.0 (SE 2.6), 3bet 11%. v17 r017 -4949 (1 round).
Rollback order: v15 (5e6d926f, sha 559b5129) is the last version with a positive live record (+9,744 over 3 rounds). Last upload 11:45.
- 10:25 r017 v17 -4949 (-24.7) clean, stacks +1/-4 (TT vs AA cooler; AQ top pair vs set; KJ two pair (K+QQ board) vs trips Q; KQ top pair vs set). No new round yet beyond r017. Us -18480 (5th); 3rd test +873 (gap 19353).
- 10:27 r018 v18(site v12) -9470 (-47.3) clean. 3bets 33 (only 17 got folds = 52%, need ~67%), net -51bb. Stacks +1/-3 (KQs flush vs nut flush, AT top pair vs straight, 98 straight vs quads). Us -27950 (5th); 3rd test +6937 (gap 34887). Recommending rollback to v15.
- 10:32 v19 CANDIDATE (high variance): v17 + opens BTN .55 SB .45 CO .38 HJ .27 EP .18/.21 + defend real +0.08 IP/+0.04 OOP. Sim tableA VPIP 27.3 PFR 19.1, vs v15 -0.8 (SE 2.8). 0 exc. Commit 5879e1af0146a44ec875458ee6543f7ef6d9cde0 sha 1ce37b70dca4ae5c5d358a1954fbf7d1dabc424bb57f13b8c5293dec7e2eea65.
- 10:31 scheduled 10:30 check: no technical issues (0 err/bank/viol, no flags). Unchanged since r018: us 5th -27950, 2nd Attention +62558 (gap 90508). v18 live; v15 or v19 awaiting Mohil.

## 10:33:18 Sun: v20 UPLOADED AND LIVE (Mohil: upload v19 or a quick v20). Commit 2be34efa77e50c521af78e34dc332d5f21cae55c, SHA 3e984b61, loaded fine.
v20 = v18 (tier-2 3-bets, SB/EP flat-call cuts) + v19 wider opens + looser IP/BB defends. Sim tableA vs v15 +3.6 (SE 2.7), VPIP 26.6 PFR 20.5 3bet 11%.
r019 v18 +2274; v18 3-bets over 2 rounds: 68, 45 folds (66%), net +101bb. Us -25676 (5th); 2nd Attention +64496 (gap 90172); 3rd test +4456.
Rollback: v18 (915f534c, sha 3f1ab65e) or v15 (5e6d926f, sha 559b5129). Last upload 11:45.
- 10:40 r020 v20(site v13) -5300 (-26.5) clean. 3bets 18, 15 folds, +23bb. Opens CO -93bb, BTN -34, EP +102, SB -6. Stacks +0/-1 (A2 two pair vs AK). Us -30976 (5th); 2nd Attention +62621 (gap 93597); 3rd test +3497.
- 10:43 r021 v20 +6840 (+34.2), miss=1. 3bets 16, 14 folds, +85bb. Opens BTN +237bb, CO +186, EP +46, SB -39. Stacks +6/-2 (AK vs 9s-full, AK vs straight). Us -24136 (5th); 3rd gamblerlove +3595 (gap 27731); 2nd Attention +71190 (gap 95326). Reviews now at :x2/:x7.

## 10:46:38 Sun: v21 UPLOADED AND LIVE (Mohil approved). Commit 41f3f759f645adc0489d3998ba910530c52cb875, SHA 1374549c, loaded fine.
v21 = v20 with OOP defend back to 0.68 (BB calls -3.78bb n=178 in r18-21) and tier-2 3-bets in position only (blind 3-bets -0.6/-2.5 in r18-21). 0 exc; timing 2.2-3.4 ms (one 9.4 ms outlier not repeated).
Rollback: v20 (2be34efa, sha 3e984b61). Last upload 11:45.
- 10:48 r022 v20 +4998 (+25.0) clean. 3bets 19/17 folds -29bb; opens CO +240 SB +98 EP -121 BTN -28; calls all positive (BB 48:+32). Stacks +5/-3. v20 3 rounds +6538. Us -19138 (5th); 3rd gamblerlove +6645 (gap 25783); 2nd Astra +70537 (gap 89675). v21 live verified (SHA 1374549c).
- 10:54 r023 v21(site v14) -4073 (-20.4) clean. 3bets 13/11 folds +106bb; opens BTN -91 EP -59 CO +73; calls BB 37:-129 (still losing), BTN +72. Stacks +1/-2 (77 full vs aces full cooler; A9 trips vs 97 full cooler). Us -23211 (5th); 3rd gamblerlove +8815 (gap 32026); 2nd Astra +75169.
- 10:58 r024 v21 -7118 (-35.6) clean. 3bets 25/20 folds +39bb; opens BTN -180; calls BB -74. Stacks +2/-4 (TT vs 77 full; QQ vs KK; AQ vs TT full; 99 vs QQ) mostly coolers. v21 2 rounds -11191. Us -30329 (5th); 3rd gamblerlove +18031 (gap 48360). Devpost: video link still missing.
- 11:03 r025 v21 +7772 (+38.9) miss=1. 3bets 19/17 folds +124bb. Stacks +6/-3 (coolers: KJ vs set 2s, AQ vs set Qs, 33 full vs quads 6s). v21 3 rounds -3419. Us -22557 (5th); 3rd gamblerlove +21557 (gap 44114).
- 11:07 r026 v21 +279 (+1.4). 3bets 22/15 folds -35bb. Stacks +2/-1 (AJ vs AK kicker). v21 4 rounds -3140. Us -22278 (5th); 4th test -13160 (gap 9118); 3rd gamblerlove +19784; Attention now 1st +94521.

## 11:10:54 Sun: v22 UPLOADED AND LIVE (Mohil: 'dream is dead', go for pure upside). Commit 3ffcdde26a45873d91fe12fa4541454881bf1f56, SHA cfbbac01, loaded fine.
v22 = v21 + opens BTN .75 SB .60 CO .55 HJ .40 EP .28/.32, defend real 1.0 IP / 0.80 OOP, 3-bet top 60% vs openers folding >= 50% (n>=6), v13 size-dependent fold model (bigger bets). Sim VPIP 36.6 PFR 27.7 3bet 12%, sd 44 vs ~33. Rollback v21 (41f3f759, sha 1374549c). Last upload 11:45.
- 11:13 r027 v21 (last v21 round) -2543 (-12.7). 3bets 38/28 folds +16bb. Stacks +2/-1 (KK vs AA cooler). Us -24821 (5th); 4th test -13942 (gap 10879). Devpost SUBMITTED by Mohil (organisers: no video needed).
- 11:18 r028 v22(site v15) +1456 (+7.3) clean, think 3.03. Played 38%. 3bets 16/11 folds -153bb. Stacks +5/-7 (high variance as intended). Us -23365 (5th); 4th test -15615 (gap 7750); 3rd gamblerlove +10011 (gap 33376).
- 11:20 scheduled check: v22 live and healthy (r028 0 miss/err/bank/viol, think 3.03). v22 inherits v12's lifetime time budget, so it is correct for the final's 1,000-hand blocks. Keep v22 (Mohil approved). No upload. Us 5th -23365.
- 11:23 r029 v22 -7902 (-39.5) clean. Played 38%. 3bets 39/23 folds -130bb. Stacks +10/-12; at least 4 lost with ace-high or worse (J8 vs AK, Q8 vs AK, AQ high vs TT, K4 pair vs JJ). v22 2 rounds -6446. Us -31267 (5th); 4th test -12359 (gap 18908); 2nd Attention +98413 (gap ~130k).
- 11:28 r030 v22 -15136 (-75.7) clean. Stacks +3/-8. v22 3 rounds -21582. Us -46403 (5th); 6th Kojack -51922 (gap 5519 behind us); 4th test -13164. Strongly recommending rollback to v20 before 11:45.
- 11:33 r031 v22 +799 (+4.0) miss=1. Stacks +5/-2. Us -45604 (5th); 6th Kojack -53029 (7425 behind); 4th test -16056. Still recommending v20 before 11:45; awaiting Mohil.
