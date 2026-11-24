# SIGNAL model accuracy (data through 2026-11-23, 197 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.72 | 11.47 | 9.55 | 68.0 |
| Book closing line | 14.2 | 10.76 | 9.13 | 71.1 |
| League average | 15.44 | 12.88 | 10.18 | - |
| Old own-median line | 16.39 | 12.94 | 10.5 | - |

SIGNAL vs the book when they disagree by 3+: totals 41-50, spreads 47-50.

## Situations that move player output (% vs own average)
- **b2b**: scoring +5.0% (n=355), rebounding +3.3% (n=277), assists -3.0% (n=144), minutes +4.2% (n=355)
- **three_in_four**: scoring +1.0% (n=563), rebounding +3.8% (n=453), assists -0.2% (n=228), minutes +2.5% (n=563)
- **to_bench**: scoring -1.8% (n=49), minutes -4.0% (n=49)
- **big_dog**: scoring +2.5% (n=207), rebounding +0.9% (n=183), minutes +2.4% (n=207), assists -3.8% (n=87)
- **teammate_out**: scoring +11.0% (n=675), rebounding +7.2% (n=514), assists +12.3% (n=231), minutes +8.7% (n=675)
- **new_starter**: scoring +11.1% (n=114), rebounding +20.0% (n=81), minutes +12.8% (n=114)
- **big_fav**: scoring +5.7% (n=220), rebounding +5.7% (n=199), assists +1.7% (n=132), minutes +1.7% (n=220)

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
- BLK: blk

Grade bands: A+ 70%, A 65%, B 60%, C 55%, D 52%, F below. Break-even at -110 is 52.4%.
