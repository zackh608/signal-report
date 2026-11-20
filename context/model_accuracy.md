# SIGNAL model accuracy (data through 2026-11-19, 173 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.12 | 11.94 | 9.47 | 68.2 |
| Book closing line | 13.71 | 11.11 | 9.07 | 72.3 |
| League average | 14.92 | 13.53 | 10.17 | - |
| Old own-median line | 15.87 | 13.31 | 10.48 | - |

SIGNAL vs the book when they disagree by 3+: totals 39-41, spreads 45-47.

## Situations that move player output (% vs own average)
- **b2b**: scoring +5.3% (n=342), rebounding +2.3% (n=267), assists -2.7% (n=140), minutes +4.4% (n=342)
- **three_in_four**: scoring +1.2% (n=496), rebounding +3.1% (n=400), assists -0.3% (n=206), minutes +2.2% (n=496)
- **big_dog**: scoring +0.8% (n=158), rebounding -1.9% (n=139), minutes +1.3% (n=158), assists -3.9% (n=69)
- **teammate_out**: scoring +13.7% (n=506), rebounding +6.7% (n=380), assists +13.3% (n=172), minutes +9.4% (n=506)
- **new_starter**: scoring +17.4% (n=94), rebounding +26.3% (n=65), minutes +14.2% (n=94)
- **big_fav**: scoring +5.3% (n=173), rebounding +7.1% (n=154), assists -2.4% (n=104), minutes +1.9% (n=173)

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
