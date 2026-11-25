# SIGNAL model accuracy (data through 2026-11-24, 198 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.8 | 11.48 | 9.58 | 68.2 |
| Book closing line | 14.23 | 10.81 | 9.14 | 70.7 |
| League average | 15.55 | 12.91 | 10.22 | - |
| Old own-median line | 16.48 | 12.95 | 10.53 | - |

SIGNAL vs the book when they disagree by 3+: totals 41-51, spreads 48-50.

## Situations that move player output (% vs own average)
- **b2b**: scoring +5.1% (n=355), rebounding +3.3% (n=277), assists -2.8% (n=144), minutes +4.1% (n=355)
- **three_in_four**: scoring +1.1% (n=563), rebounding +3.8% (n=453), assists -0.0% (n=228), minutes +2.5% (n=563)
- **to_bench**: scoring -1.7% (n=49), minutes -4.0% (n=49)
- **big_dog**: scoring +2.6% (n=207), rebounding +0.9% (n=183), minutes +2.3% (n=207), assists -3.6% (n=87)
- **teammate_out**: scoring +11.1% (n=683), rebounding +7.0% (n=519), assists +13.0% (n=233), minutes +8.7% (n=683)
- **new_starter**: scoring +11.2% (n=114), rebounding +20.0% (n=81), minutes +12.8% (n=114)
- **big_fav**: scoring +5.9% (n=220), rebounding +5.7% (n=199), assists +1.9% (n=132), minutes +1.7% (n=220)

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
