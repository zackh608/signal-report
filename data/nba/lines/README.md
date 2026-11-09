# Posted lines (optional)

Drop one CSV per day here, named `YYYY-MM-DD.csv`, and `nba_tracker.py` grades that
player/market against the real posted line instead of the SIGNAL baseline (median of the last 20 eligible games).

```
player,market,line,book
Tyrese Maxey,PTS,24.5,bet365
Tyrese Maxey,AST,3.5,DK
Onyeka Okongwu,REB,8.5,FD
```

Markets: PTS REB AST 3PM STL BLK PRA PR PA RA S+B. The newest CSV wins for a given player+market.
