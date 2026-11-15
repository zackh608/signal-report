# SIGNAL model accuracy (data through 2026-11-14, 140 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.32 | 12.22 | 9.61 | 67.9 |
| Book closing line | 13.94 | 11.26 | 9.22 | 72.9 |
| League average | 14.88 | 13.66 | 10.21 | - |
| Old own-median line | 15.94 | 13.71 | 10.6 | - |

SIGNAL vs the book when they disagree by 3+: totals 34-33, spreads 35-41.

## Situations that move player output (% vs own average)
- **b2b**: scoring +5.9% (n=267), rebounding +2.7% (n=210), assists -2.8% (n=114), minutes +4.2% (n=267)
- **three_in_four**: scoring +1.1% (n=421), rebounding +1.6% (n=344), assists -1.8% (n=179), minutes +2.1% (n=421)
- **big_dog**: scoring +3.2% (n=110), rebounding -0.7% (n=96), minutes +3.5% (n=110), assists -3.9% (n=50)
- **teammate_out**: scoring +15.4% (n=300), rebounding +12.8% (n=231), assists +14.9% (n=101), minutes +10.7% (n=300)
- **new_starter**: scoring +15.6% (n=68), rebounding +30.5% (n=45), minutes +15.8% (n=68)
- **big_fav**: scoring +4.4% (n=120), rebounding +2.3% (n=109), assists -3.9% (n=74), minutes +1.3% (n=120)

## Matchup signals that tested real
- PTS: pts, pace, pitp, fta
- REB: reb
- OREB: oreb
- DREB: dreb
- AST: ast
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
