# SIGNAL NBA tracker — manual runbook (no Claude required)

Everything here runs on GitHub's free Actions minutes or on your own PC with plain Python 3.
There is no AI in the loop and no paid data source.

## 1. Normal operation (hands-off)

The workflow `.github/workflows/signal.yml` runs every day at 13:00 UTC (8 AM ET):

1. `build_signal.py` → team report to the gist (existing behaviour).
2. `nba_tracker.py` → pulls any date from the season opener through yesterday that is not yet in
   `data/nba/ingested_days.json`, recomputes every hit rate, writes `nba_player_props.md`, pushes it to the gist.
3. Commits `data/nba/*` back to the repo so tomorrow's run knows what it already has.

If a run fails or is skipped, the next run backfills automatically — nothing to do.

## 2. Run it yourself on Windows

```powershell
cd path\to\signal-report
python nba_tracker.py --no-gist                 # pull missing days, rebuild rates, write report locally
python nba_tracker.py --from 2026-10-20 --no-gist   # force a full re-pull from a date
python nba_tracker.py --rates-only --no-gist    # offline: recompute rates from stored logs only
```

Then `git add data/nba nba_player_props.md && git commit -m "nba data" && git push`.
To also push the report to the gist locally, set `GIST_TOKEN` (a GitHub token with `gist` scope) and drop `--no-gist`.

## 3. Trigger a run from the browser

GitHub → repo → **Actions** → **SIGNAL daily report** → **Run workflow**.
Put a date in `nba_from` (e.g. `2026-10-20`) to force a backfill from that day; leave blank for normal.

## 4. Add real sportsbook lines

Create `data/nba/lines/YYYY-MM-DD.csv`:

```
player,market,line,book
Tyrese Maxey,PTS,24.5,bet365
Onyeka Okongwu,REB,8.5,FD
```

Commit it. Those player/markets are then graded against the posted line and labelled with the book;
everything else stays on the `signal-median` line (trailing-10 median rounded to .5).

## 5. What lives where

| File | What |
| --- | --- |
| `data/nba/team_games.json` | one row per team per game: quarters (own + opp), OT, halves derived, box stats |
| `data/nba/player_games.json` | one row per player per game |
| `data/nba/ingested_days.json` | dates fully ingested (delete a date here to force its re-pull) |
| `data/nba/nba_hit_rates.json` | every player × 11 markets × L5/L10/L20/season, streaks, flags |
| `data/nba/nba_team_stats.json` | every team: records by situation (home/away, led/trailed at half, won 1Q, close, blowout, OT, vs .500+), quarter + half + OT scoring splits (season/L5/L10/home/away), quarters won, comebacks, four factors, box stats, 24 segment markets, full game log |
| `nba_player_props.md` | the human-readable report that goes to the gist |

## 6. Knobs (top of `nba_tracker.py`)

| Constant | Default | Meaning |
| --- | --- | --- |
| `SEASON_START` | 2026-10-20 | first date to pull; change each season |
| `MIN_MINUTES` | 15 | games below this don't count toward player hit rates |
| `WINDOWS` | 5, 10, 20 | rolling windows |
| `PLAYER_MARKETS` / `TEAM_MARKETS` | — | add a line to add a market; nothing else changes |

## 7. When something breaks

* **Actions log says `both sources failed`** for a date: ESPN and NBA.com both errored. Usually transient;
  the date stays un-ingested and is retried next run. If it persists for days, open the two URLs in a browser:
  `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=YYYYMMDD` and
  `https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json` — if one has changed shape, the parsing
  is in `parse_game` (ESPN) / `parse_nba_game` (NBA.com); the field names are listed in the `ESPN_TEAM_STATS` /
  `NBA_TEAM_STATS` dicts at the top.
* **A player's stats look wrong**: find their rows in `player_games.json`, fix or delete, run `--rates-only`.
* **Gist push fails**: the `GIST_TOKEN` secret expired → Settings → Secrets → update it. The repo data is still saved.
* **Want to start clean**: delete `data/nba/*.json`, run with `--from <season start>`.

Python has no third-party dependencies here (standard library only), so there is nothing to install beyond Python itself.
