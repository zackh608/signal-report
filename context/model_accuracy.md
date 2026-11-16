# SIGNAL model accuracy (data through 2026-11-15, 149 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.38 | 12.0 | 9.59 | 69.8 |
| Book closing line | 14.04 | 11.06 | 9.21 | 74.5 |
| League average | 14.9 | 13.74 | 10.24 | - |
| Old own-median line | 15.91 | 13.55 | 10.59 | - |

SIGNAL vs the book when they disagree by 3+: totals 35-35, spreads 38-43.

## Situations that move player output (% vs own average)
- **b2b**: scoring +4.9% (n=276), rebounding +2.5% (n=217), assists -4.2% (n=117), minutes +4.0% (n=276)
- **three_in_four**: scoring +0.3% (n=430), rebounding +1.5% (n=351), assists -3.0% (n=182), minutes +2.0% (n=430)
- **big_dog**: scoring +0.3% (n=122), rebounding -0.4% (n=106), minutes +2.1% (n=122), assists -5.4% (n=55)
- **teammate_out**: scoring +13.7% (n=337), rebounding +10.0% (n=256), assists +11.9% (n=111), minutes +9.8% (n=337)
- **new_starter**: scoring +18.8% (n=72), rebounding +32.0% (n=48), minutes +16.2% (n=72)
- **big_fav**: scoring +2.6% (n=137), rebounding +5.2% (n=125), assists -3.9% (n=85), minutes +1.0% (n=137)

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
