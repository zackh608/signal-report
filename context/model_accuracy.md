# SIGNAL model accuracy (data through 2026-11-18, 169 games scored walk-forward)

| Method | Total miss | Margin miss | Team pts miss | Winner % |
|---|---|---|---|---|
| SIGNAL model | 14.22 | 12.01 | 9.52 | 68.0 |
| Book closing line | 13.82 | 11.21 | 9.11 | 71.6 |
| League average | 14.98 | 13.53 | 10.19 | - |
| Old own-median line | 15.93 | 13.41 | 10.55 | - |

SIGNAL vs the book when they disagree by 3+: totals 39-41, spreads 43-46.

## Situations that move player output (% vs own average)
- **b2b**: scoring +5.0% (n=319), rebounding +4.1% (n=248), assists -4.2% (n=130), minutes +4.5% (n=319)
- **three_in_four**: scoring +0.9% (n=489), rebounding +3.6% (n=394), assists -1.3% (n=202), minutes +2.4% (n=489)
- **big_dog**: scoring +0.4% (n=150), rebounding -0.6% (n=132), minutes +1.7% (n=150), assists -3.1% (n=64)
- **teammate_out**: scoring +13.2% (n=469), rebounding +8.3% (n=349), assists +12.7% (n=157), minutes +9.6% (n=469)
- **new_starter**: scoring +17.6% (n=92), rebounding +25.4% (n=63), minutes +14.4% (n=92)
- **big_fav**: scoring +3.9% (n=164), rebounding +6.9% (n=145), assists -3.6% (n=99), minutes +1.5% (n=164)

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
