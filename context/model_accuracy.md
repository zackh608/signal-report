# SIGNAL model accuracy (data through 2026-11-21, 188 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.75 | 11.53 | 9.6 | 68.6 |
| Book closing line | 14.22 | 10.76 | 9.16 | 71.8 |
| League average | 15.59 | 12.98 | 10.29 | - |
| Old own-median line | 16.5 | 13.01 | 10.59 | - |

SIGNAL vs the book when they disagree by 3+: totals 39-47, spreads 46-50.

## Situations that move player output (% vs own average)
- **b2b**: scoring +5.1% (n=355), rebounding +3.3% (n=277), assists -2.7% (n=144), minutes +4.4% (n=355)
- **three_in_four**: scoring +1.1% (n=555), rebounding +3.6% (n=447), assists -0.3% (n=225), minutes +2.7% (n=555)
- **to_bench**: scoring -3.9% (n=44), minutes -4.5% (n=44)
- **big_dog**: scoring +2.2% (n=187), rebounding +2.2% (n=166), minutes +2.8% (n=187), assists -4.5% (n=80)
- **teammate_out**: scoring +11.8% (n=616), rebounding +7.1% (n=467), assists +12.4% (n=210), minutes +9.2% (n=616)
- **new_starter**: scoring +15.4% (n=106), rebounding +23.8% (n=73), minutes +14.4% (n=106)
- **big_fav**: scoring +5.5% (n=201), rebounding +5.9% (n=181), assists +1.9% (n=121), minutes +2.5% (n=201)

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
