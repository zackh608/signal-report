# SIGNAL model accuracy (data through 2026-11-16, 152 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.33 | 11.96 | 9.58 | 69.7 |
| Book closing line | 13.98 | 11.06 | 9.18 | 74.3 |
| League average | 14.93 | 13.72 | 10.22 | - |
| Old own-median line | 15.83 | 13.5 | 10.57 | - |

SIGNAL vs the book when they disagree by 3+: totals 37-36, spreads 39-43.

## Situations that move player output (% vs own average)
- **b2b**: scoring +4.7% (n=290), rebounding +2.3% (n=229), assists -5.0% (n=123), minutes +4.0% (n=290)
- **three_in_four**: scoring +1.4% (n=452), rebounding +1.6% (n=366), assists -0.6% (n=191), minutes +2.3% (n=452)
- **big_dog**: scoring +0.7% (n=138), rebounding -1.7% (n=120), minutes +2.0% (n=138), assists -4.2% (n=60)
- **teammate_out**: scoring +14.2% (n=359), rebounding +9.6% (n=271), assists +14.5% (n=120), minutes +9.7% (n=359)
- **new_starter**: scoring +16.9% (n=78), rebounding +30.3% (n=53), minutes +16.1% (n=78)
- **big_fav**: scoring +3.6% (n=148), rebounding +6.1% (n=135), assists -3.1% (n=93), minutes +1.3% (n=148)

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
