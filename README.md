# Imperial AI Hack 2026: Poker Bot (Track 04, AI Poker Bots)

Built at the Imperial AI Hackathon, 14 to 15 November 2026, Huxley Building, Imperial College London.

**Track:** AI Poker Bots (Optiver · Jump Trading · AlgoSoc). Decided by the live tournament.
**Team:** Mohil'sPokerBot (Mohil Garg, solo)

## The problem

Six to eight bots play no-limit Texas Hold'em for 1,000 hands, with stacks reset to 100 big blinds every hand. Each decision has 10 ms (10 s in total per round), on one core, with the Python standard library only. The opponents are other teams' unknown bots, and the score is big blinds won per 100 hands (bb/100). A fixed strategy gets exploited, so the bot has to estimate equity quickly and adapt to each seat within a round.

## What we built

`bot.py` is a single-file agent (class `Agent`).

- **Preflop, by table lookup.** Two embedded tables, both computed offline by our own Monte Carlo scripts: equity of each of the 169 starting-hand classes against 1 to 7 random hands, and against an opponent holding the top X% of hands (12 range widths). Every opponent's range is narrowed by what they did (open, 3-bet, 4-bet, call, jam) using that seat's measured frequency for that action, and the bot folds, calls, 3-bets or stacks off by comparing equity against that range with the pot odds. No simulation is needed preflop, which saves most of the time bank.
- **Postflop, by time-budgeted Monte Carlo.** Opponent hands are sampled from their preflop range and filtered by how much strength they have shown: bet size, raises over bets and repeated barrels each demand a stronger hand, scaled by how often that opponent bets. Bets are chosen by comparing EV(check) with EV(bet) at three sizes using each opponent's fold frequency; calls use pot odds with a margin for large bets.
- **Opponent model per seat, per round.** Open frequency by position, 3-bet, fold to 3-bet, 4-bet, call-a-jam, limp-fold, bet frequency as raiser and as caller, and fold to bet. Every statistic starts from a prior set from the real field averages.
- **Time management.** About 1 s of thinking per 1,000 hands, with a throttle that cuts simulation counts if the bank runs low (needed for the 5,000-hand final).

## Results, with their noise

One 1,000-hand round swings by roughly ±55 bb/100, so small samples say little.

**Real tournament tables (Saturday, counted rounds):**

| Version | Rounds | bb/100 | Standard error |
|---|---|---|---|
| v2: preflop rewrite, aggressive postflop | 14 | +26.1 | 14.2 |
| v4: stricter postflop ranges, fewer bluffs | 13 | +4.9 | 6.9 |

The stricter version did not do better on real tables. The field folds too often (71% of blinds fold to an open, 53–62% fold to a 3-bet, about half fold to a bet on each street), so most profit comes from pots that never reach showdown, and betting less gave that profit up. The submitted bot keeps the aggressive postflop play and applies strict ranges only against opponents who have shown strength.

**Local simulation** against clones of the real bots (fitted to 129,000 real opponent hands; 96 rounds, standard error about 6): submitted bot +44, v2 +42, v4 +54. The simulation ranks v4 first and the real tables rank it last. We traced this to the clones paying off too much at showdown, so we use the simulation for bugs, timing and preflop changes, and real tables for style choices.

**Tried and not shipped:**
- A fingerprint table that recognises known teams from their bet sizes and frequencies and loads their profile as a prior: +2.3 (SE 2.9) on one test pool and −2.1 (SE 2.6) on another. No detectable gain.
- EV-based bet sizing from a "who would call" model: −1.1 (SE 2.7).
- Wider opening ranges: −2.2 (SE 4.2).

## Repository layout

| Path | What it is |
|---|---|
| `bot.py` | The submitted bot |
| `research/bot_template.py`, `research/build.py` | Bot source and the script that embeds the two tables |
| `research/preflop_table.py`, `research/gen_eqr.py` | Offline Monte Carlo for the equity tables |
| `research/arena.py`, `research/paired.py` | Paired-seed test harness and A/B comparison |
| `research/field/`, `research/profiles.txt` | Clones of the real bots and the statistics they are fitted to |
| `research/bot_template_fingerprint.py`, `research/gen_fp.py` | The fingerprint experiment (not shipped) |
| `research/NOTES.md` | Working notes: version history, real-table findings, known simulation bias |

The tools expect the organisers' starter kit (engine and `local_sim.py`), which is not included. Some scripts contain absolute paths from the development machine.

## APIs, models and datasets used

| Name | What for |
|---|---|
| Python 3.12 standard library | Everything in `bot.py` |
| AlgoSoc Pokerbots starter kit | Game engine and local simulator |
| Tournament hand histories (our own tables, via the organisers' data token) | Opponent statistics for priors and test clones |
| Claude (Anthropic) | AI coding assistant during development (allowed by the track rules) |

No pretrained models or external datasets.

## Running it

```bash
# from the starter kit folder, with bot.py copied in
python local_sim.py bot.py --rounds 10
```

All code in this repository was written during the hackathon (after 12:10 on Saturday 14 November 2026).
