# SIGNAL model accuracy (data through 2026-11-17, 157 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.33 | 12.01 | 9.56 | 69.4 |
| Book closing line | 13.93 | 11.12 | 9.16 | 73.9 |
| League average | 14.94 | 13.63 | 10.18 | - |
| Old own-median line | 15.91 | 13.6 | 10.63 | - |

SIGNAL vs the book when they disagree by 3+: totals 37-38, spreads 40-44.

## Situations that move player output (% vs own average)
- **b2b**: scoring +4.6% (n=290), rebounding +2.9% (n=229), assists -4.7% (n=123), minutes +3.8% (n=290)
- **three_in_four**: scoring +1.2% (n=452), rebounding +2.3% (n=366), assists -0.4% (n=191), minutes +2.1% (n=452)
- **big_dog**: scoring +0.8% (n=142), rebounding +0.2% (n=124), minutes +2.3% (n=142), assists -3.6% (n=61)
- **teammate_out**: scoring +14.1% (n=394), rebounding +10.6% (n=297), assists +14.2% (n=132), minutes +10.1% (n=394)
- **new_starter**: scoring +22.2% (n=80), rebounding +32.0% (n=54), minutes +16.8% (n=80)
- **big_fav**: scoring +4.8% (n=152), rebounding +6.7% (n=137), assists -2.9% (n=94), minutes +1.7% (n=152)

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
