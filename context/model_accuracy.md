# SIGNAL model accuracy (data through 2026-11-13, 135 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.3 | 12.07 | 9.6 | 68.9 |
| Book closing line | 13.84 | 11.01 | 9.2 | 74.1 |
| League average | 14.96 | 13.67 | 10.28 | - |
| Old own-median line | 16.01 | 13.79 | 10.71 | - |

SIGNAL vs the book when they disagree by 3+: totals 33-33, spreads 33-40.

## Situations that move player output (% vs own average)
- **b2b**: scoring +3.7% (n=238), rebounding +1.5% (n=193), assists -5.1% (n=103), minutes +3.2% (n=238)
- **three_in_four**: scoring -0.1% (n=399), rebounding +0.6% (n=330), assists -2.5% (n=171), minutes +1.3% (n=399)
- **big_dog**: scoring +3.1% (n=107), rebounding -2.1% (n=94), minutes +3.6% (n=107), assists -2.6% (n=49)
- **teammate_out**: scoring +14.3% (n=271), rebounding +11.6% (n=212), assists +15.5% (n=90), minutes +10.2% (n=271)
- **new_starter**: scoring +16.1% (n=64), rebounding +32.8% (n=41), minutes +14.9% (n=64)
- **big_fav**: scoring +4.8% (n=115), rebounding +2.3% (n=104), assists -3.6% (n=71), minutes +1.0% (n=115)

## Matchup signals that tested real
- PTS: pts, pace, pitp, fta
- REB: reb
- OREB: oreb
- DREB: dreb
- AST: ast
- 3PM: fg3a
- STL: stl
- TOV: tov
- FGM: fgm, pace
- FTM: fta
- PF: pf
- PRA: pts, pace
- PR: pts, pace, reb
- PA: pts, pace, ast
- RA: reb, ast
- S+B: stl

Grade bands: A+ 70%, A 65%, B 60%, C 55%, D 52%, F below. Break-even at -110 is 52.4%.
