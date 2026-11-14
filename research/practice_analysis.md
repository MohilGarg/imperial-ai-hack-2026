# Practice rounds analysis (Sat 14 Nov, rounds r012 and r013, 1,000 hands each)

Our results: r012 -3.5 bb/100 (seat 2, 6-handed), r013 -38.4 bb/100 (seat 5, 7-handed).

## Our stats vs the field

| Bot | bb/100 | VPIP | PFR | Agg freq | Fold to bet | Fold to pre-raise | All-ins | SD win% |
|---|---|---|---|---|---|---|---|---|
| **Us r012** | -3.5 | 33.3 | 26.8 | 0.62 | 0.50 | 0.52 | 60 | 49% |
| **Us r013** | -38.4 | 40.5 | 33.7 | 0.48 | 0.46 | 0.47 | 27 | 45% |
| matcha mille crêpes cake | +111 | 20 | 13.4 | 0.33 | 0.37 | 0.78 | 30 | 57% |
| The Market Makers | +83 | 18.2 | 11.7 | 0.62 | 0.43 | 0.84 | 17 | 55% |
| Chinese people can fly | +82 | 35.6 | 23.4 | 0.44 | 0.40 | 0.66 | 10 | 59% |
| SARS | +26 | 14.5 | 9.4 | 0.46 | 0.22 | 0.89 | 1 | 47% |
| Jump Street | +25 | 22.7 | 8.7 | 0.33 | 0.46 | 0.72 | 8 | 53% |
| Claudebot | +24 | 23.8 | 18.6 | 0.16 | 0.44 | 0.83 | 95 | 52% |
| GamesGone | +13 | 28.6 | 19.3 | 0.60 | 0.33 | 0.65 | 18 | 42% |
| Phil AIvey | -15 | 24.9 | 17.3 | 0.14 | 0.39 | 0.75 | 30 | 54% |
| Kojack | -31 | 20 | 15.9 | 0.30 | 0.44 | 0.80 | 1 | 52% |
| gamblerlove | -36 | 13.8 | 8.7 | 0.30 | 0.14 | 0.89 | 0 | 31% |
| Joca (maniac/station) | -239 | 74.4 | 30.2 | 0.33 | 0.49 | 0.50 | 7 | 42% |

## Where we lose (bb, by our first action and the street of our last action)

r013: preflop raise then showdown on river -403 (n=48); raise then showdown on turn -280 (n=9); raise then fold on flop -226 (n=67); raise then win or fold preflop -82 (n=132); folded preflop -76 (n=585).
r012: raise then fold on flop -423 (n=59); raise then showdown on turn -389 (n=18); limp/call then fold on flop -112 (n=20).
Biggest single losses: many full 100bb stacks lost, a lot of them in the first 200 hands of each round (priors not yet calibrated).

## Diagnosis (to be verified)

1. Far too loose preflop: VPIP 33 to 40 and PFR 27 to 34, against winners at 14 to 24 VPIP. The "widen" / steal / fold-equity terms are firing against a field that does not fold as much as the priors assume (real fold-to-bet is 0.14 to 0.46, not 0.5+).
2. Too many stacks played: 27 to 60 all-ins per round. The preflop EV shove option and the value-raise rule postflop commit 100bb with hands that are behind ranges that call big bets.
3. We fold to preflop raises only about 50% of the time against a field folding 65 to 89%. We defend and 3-bet too wide.
4. Raised pots that we play to the flop and then give up on (c-bet, get raised, fold) lose a lot: the postflop raise-facing filter is too weak, and c-betting multiway into sticky players burns chips.
5. Priors in the opponent model (fold rate 0.4, pre-fold 0.45, PFR 0.15) do not match this field and cost money early in each round.

The raw hand histories can be re-fetched in the browser on imperialaihack.com/pokerbots with the team data token (GET /api/poker/results, then /api/poker/hands?ref=...). The shell cannot reach the site.
