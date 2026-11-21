# SIGNAL model accuracy (data through 2026-11-20, 182 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.36 | 11.67 | 9.47 | 68.1 |
| Book closing line | 13.9 | 10.91 | 9.06 | 72.0 |
| League average | 15.17 | 13.18 | 10.16 | - |
| Old own-median line | 16.01 | 13.05 | 10.42 | - |

SIGNAL vs the book when they disagree by 3+: totals 39-44, spreads 46-48.

## Situations that move player output (% vs own average)
- **b2b**: scoring +5.2% (n=342), rebounding +2.1% (n=267), assists -2.5% (n=140), minutes +4.4% (n=342)
- **three_in_four**: scoring +0.8% (n=528), rebounding +3.0% (n=423), assists +0.1% (n=215), minutes +2.5% (n=528)
- **to_bench**: scoring -1.5% (n=42), minutes -3.2% (n=42)
- **big_dog**: scoring +2.0% (n=173), rebounding +0.3% (n=153), minutes +2.4% (n=173), assists -4.1% (n=74)
- **teammate_out**: scoring +12.1% (n=570), rebounding +6.6% (n=427), assists +12.5% (n=190), minutes +9.2% (n=570)
- **new_starter**: scoring +16.6% (n=101), rebounding +24.5% (n=69), minutes +14.0% (n=101)
- **big_fav**: scoring +5.1% (n=189), rebounding +5.5% (n=169), assists -0.5% (n=111), minutes +2.5% (n=189)

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
