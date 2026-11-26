# SIGNAL model accuracy (data through 2026-11-25, 200 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.81 | 11.39 | 9.56 | 68.5 |
| Book closing line | 14.23 | 10.78 | 9.12 | 70.0 |
| League average | 15.52 | 12.83 | 10.18 | - |
| Old own-median line | 16.44 | 12.93 | 10.5 | - |

SIGNAL vs the book when they disagree by 3+: totals 41-52, spreads 50-50.

## Situations that move player output (% vs own average)
- **b2b**: scoring +5.2% (n=355), rebounding +3.1% (n=277), assists -3.0% (n=144), minutes +4.1% (n=355)
- **three_in_four**: scoring +1.2% (n=563), rebounding +3.6% (n=453), assists -0.2% (n=228), minutes +2.5% (n=563)
- **to_bench**: scoring -1.7% (n=49), minutes -4.1% (n=49)
- **big_dog**: scoring +2.7% (n=207), rebounding +0.7% (n=183), minutes +2.3% (n=207), assists -3.8% (n=87)
- **teammate_out**: scoring +11.2% (n=690), rebounding +6.8% (n=525), assists +12.9% (n=235), minutes +8.7% (n=690)
- **new_starter**: scoring +10.7% (n=116), rebounding +18.4% (n=83), minutes +12.8% (n=116)
- **big_fav**: scoring +5.9% (n=220), rebounding +5.6% (n=199), assists +1.8% (n=132), minutes +1.7% (n=220)

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
