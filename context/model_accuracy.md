# SIGNAL model accuracy (data through 2026-11-12, 126 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.46 | 12.05 | 9.7 | 69.8 |
| Book closing line | 14.0 | 10.95 | 9.28 | 74.6 |
| League average | 14.89 | 13.75 | 10.29 | - |
| Old own-median line | 16.19 | 13.92 | 10.9 | - |

SIGNAL vs the book when they disagree by 3+: totals 32-32, spreads 30-38.

## Situations that move player output (% vs own average)
- **b2b**: scoring +3.5% (n=238), rebounding +1.3% (n=193), assists -6.2% (n=103), minutes +2.8% (n=238)
- **three_in_four**: scoring -1.6% (n=358), rebounding +0.4% (n=293), assists -5.3% (n=156), minutes +0.1% (n=358)
- **big_dog**: scoring +0.3% (n=96), rebounding -4.6% (n=84), minutes +1.9% (n=96), assists -5.4% (n=44)
- **teammate_out**: scoring +13.1% (n=245), rebounding +10.8% (n=192), assists +11.5% (n=82), minutes +9.1% (n=245)
- **new_starter**: scoring +19.1% (n=57), minutes +14.3% (n=57)
- **big_fav**: scoring +3.0% (n=97), rebounding +0.8% (n=87), assists -5.8% (n=61), minutes -1.2% (n=97)

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
