# SIGNAL model accuracy (data through 2026-11-22, 189 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.8 | 11.53 | 9.61 | 68.3 |
| Book closing line | 14.26 | 10.77 | 9.17 | 71.4 |
| League average | 15.62 | 12.95 | 10.29 | - |
| Old own-median line | 16.56 | 12.99 | 10.61 | - |

SIGNAL vs the book when they disagree by 3+: totals 39-48, spreads 46-50.

## Situations that move player output (% vs own average)
- **b2b**: scoring +5.1% (n=355), rebounding +3.0% (n=277), assists -2.4% (n=144), minutes +4.4% (n=355)
- **three_in_four**: scoring +1.1% (n=555), rebounding +3.3% (n=447), assists -0.1% (n=225), minutes +2.7% (n=555)
- **to_bench**: scoring -3.9% (n=44), minutes -4.5% (n=44)
- **big_dog**: scoring +2.2% (n=187), rebounding +1.9% (n=166), minutes +2.7% (n=187), assists -4.3% (n=80)
- **teammate_out**: scoring +11.5% (n=623), rebounding +6.7% (n=472), assists +13.0% (n=213), minutes +9.1% (n=623)
- **new_starter**: scoring +14.7% (n=107), rebounding +24.0% (n=74), minutes +13.9% (n=107)
- **big_fav**: scoring +5.5% (n=201), rebounding +5.6% (n=181), assists +2.1% (n=121), minutes +2.5% (n=201)

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
