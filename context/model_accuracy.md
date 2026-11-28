# SIGNAL model accuracy (data through 2026-11-27, 211 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.98 | 11.27 | 9.59 | 67.8 |
| Book closing line | 14.31 | 10.67 | 9.12 | 69.2 |
| League average | 15.6 | 12.72 | 10.2 | - |
| Old own-median line | 16.63 | 12.81 | 10.54 | - |

SIGNAL vs the book when they disagree by 3+: totals 44-56, spreads 53-53.

## Situations that move player output (% vs own average)
- **b2b**: scoring +6.2% (n=355), rebounding +3.0% (n=277), assists -1.7% (n=144), minutes +4.2% (n=355)
- **three_in_four**: scoring +2.3% (n=563), rebounding +3.6% (n=453), assists +1.1% (n=228), minutes +2.6% (n=563)
- **to_bench**: scoring +2.6% (n=55), rebounding +19.2% (n=42), minutes -3.2% (n=55)
- **big_dog**: scoring +3.6% (n=212), rebounding +1.4% (n=188), minutes +2.7% (n=212), assists -2.0% (n=89)
- **teammate_out**: scoring +11.8% (n=772), rebounding +6.6% (n=588), assists +12.6% (n=266), minutes +8.3% (n=772)
- **new_starter**: scoring +13.1% (n=128), rebounding +19.1% (n=91), minutes +13.9% (n=128)
- **big_fav**: scoring +6.9% (n=225), rebounding +5.3% (n=203), assists +2.6% (n=134), minutes +1.5% (n=225)

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
- 3PA: fg3a
- FGA: fga, pace
- FTA: fta

Grade bands: A+ 70%, A 65%, B 60%, C 55%, D 52%, F below. Break-even at -110 is 52.4%.
