# SIGNAL NBA tracker — manual runbook (no Claude required)

Everything here runs on GitHub's free Actions minutes or on your own PC with plain Python 3.
There is no AI in the loop and no paid data source.

## 1. Normal operation (hands-off)

The workflow `.github/workflows/signal.yml` runs twice a day, ~5:17 AM and ~2:43 PM ET (odd minutes, because GitHub
delays jobs scheduled on the hour), never two at once. GitHub is the one place the tracker runs. The PC only mirrors
the results with `sync_from_github.py` (Desktop\SIGNAL NBA Tracker; scheduled by "SETUP AUTO (run once).bat" at
6:30 AM, 3:30 PM, at logon and on wake after a missed time; "SYNC NOW.bat" to do it by hand). Each run:

1. `build_signal.py` → team report to the gist (existing behaviour).
2. `nba_tracker.py` → pulls any date from the season opener through yesterday that is not yet in
   `data/nba/ingested_days.json`, recomputes every hit rate, writes `nba_player_props.md`, pushes it to the gist.
3. Commits `data/nba/*` back to the repo so tomorrow's run knows what it already has.

If a run fails or is skipped, the next run backfills automatically — nothing to do.

## 2. Run it yourself on Windows

```powershell
cd path\to\signal-report
python nba_tracker.py --no-gist                 # pull missing days, rebuild rates, write report locally
python nba_tracker.py --from 2026-10-20 --no-gist   # pull from a date (already-stored games are kept)
python nba_tracker.py --rebuild --no-gist            # throw away stored logs and re-pull everything (after a parser fix)
python nba_tracker.py --rates-only --no-gist    # offline: recompute rates from stored logs only
```

Then `git add data/nba nba_player_props.md && git commit -m "nba data" && git push`.
To also push the report to the gist locally, set `GIST_TOKEN` (a GitHub token with `gist` scope) and drop `--no-gist`.

## 3. Trigger a run from the browser

GitHub → repo → **Actions** → **SIGNAL daily report** → **Run workflow**.
Put a date in `nba_from` (e.g. `2026-10-20`) to force a backfill from that day; leave blank for normal.

## 4. Posted lines (automatic since 2026-11-12)

Every run now does two things with no key and no paid feed:

* **Closing total + spread for every stored game** come from ESPN's game summary (`pickcenter`). `--backfill-lines`
  patches any stored game that lacks them (one call per game, skips games already done, safe to pass every run).
  Each team's `book` block in `nba_team_stats.json` is its over/under record and against-the-spread record
  **graded against that game's actual number** — the only hit rate that means anything.
* **Today's pregame total + spread** are read from the ESPN scoreboard and written to
  `data/nba/lines/team-YYYY-MM-DD.csv` (`home,FULL|SPREAD,line,book`) so Jarvis and the site grade tonight
  against a posted number instead of a median. `--no-lines` skips this.

Player prop lines are still not captured automatically (ESPN does not publish them). Until they are, player
hit rates are against the player's own median and **are not bettable** — the 2026-11-09/11 record (3-19) is what
betting them looks like.

## 4b. Add player prop lines by hand

Create `data/nba/lines/YYYY-MM-DD.csv`:

```
player,market,line,book
Tyrese Maxey,PTS,24.5,bet365
Onyeka Okongwu,REB,8.5,FD
```

Commit it. Those player/markets are then graded against the posted line and labelled with the book;
everything else stays on the `signal-median` line (median of the last 20 eligible games, rounded to .5 — the player's season baseline).

## 4c. Projections and the accuracy scoreboard (since 2026-11-12)

Every run writes two more files:

* `data/nba/accuracy.json` — SIGNAL grading itself. Every stored game is predicted **from prior games only** and
  scored: average miss on total / margin / team points and winner %, for the SIGNAL model, the old own-median
  line, the league average, and (once `--backfill-lines` has run) the book's closing number. It also keeps the
  record of games where the model disagreed with the book by 3+ points. If the model is not beating a baseline
  here, it is not accurate, whatever a single night looks like.
* `data/nba/projections.json` — today's games: projected score, total, margin, win probability, quarter/half
  totals, back-to-back flags, and the gap to the posted total and spread.

Model (constants at the top of the projection section in `nba_tracker.py`): pace x efficiency, every team
rating shrunk 8 games toward the league average, home court measured from the data, -1.5 on a back-to-back.
Chosen by walk-forward test (`tools/model_experiments.py`); on 112 games it missed totals by 14.5 and margins by
12.2 vs 16.1 / 14.0 for the old median line. Totals are barely more predictable than the league average.

Players: each market now carries `proj` (season mean of 15+ minute games) and `proj_sd`. On 1,081 player-games
the season mean beat the L20 median, per-minute x minutes, opponent adjustment and every recency blend;
the last-5 average was the worst predictor. `proj_edge` appears only when a real book line is on file.

## 4d. Every stat, matchups and grades (since 2026-11-12)

* **Every stat is stored.** Player rows keep attempts (FGA/3PA/FTA), plus-minus and any column ESPN adds;
  team rows keep every statistic in the box score (unmapped ones under an `x_` name), for and against.
  Games ingested before this date only have the old columns - run **REBUILD** once to re-pull them all
  (it also stores the closing lines, so it replaces "GET BOOK LINES").
* `nba_team_stats.json` -> each team's `stats`: every stat per game, **for and against, with league rank and z-score**.
* `accuracy.json` -> `matchup_effects`: for every player stat, how much opposing players actually gained or lost
  against weak vs strong defenses in that stat, measured walk-forward. A signal is `used` only if it has 150+
  graded player-games and a positive effect; only half of the measured effect is applied, capped at 12%.
  `calibration` is how over-confident the raw probabilities were; grades are corrected by it.
* `grades.json` (today's slate) -> every player x market: season average, matchup-adjusted projection, the chance
  the pick hits and a letter (A+ 70%+, A 65, B 60, C 55, D 52, F), with one-grade penalties for unstable minutes
  and blowout risk and a cap at B under 8 games; and, per game, **every stat ranked strength-vs-weakness** with the
  players it points to. A `*` on a grade means no book line was on file. The site's GRADE A PICK box re-grades
  any player/stat against the line you type.

Nothing here knows about injuries. A player who is out still gets a grade.

## 4f. Spread and total tally (since 2026-11-12)

`nba_team_stats.json` -> each team's `book.COVER`: against-the-spread record vs each game's closing spread, with
home/away, favourite/underdog, 7+ point favourite/underdog, after-a-win/after-a-loss splits, last 5/10/20, current
streak, average cover margin and the last 10 results. `book.TOTALS` is the same for over/under. The site's
**COVERS** tab shows every team, sortable, with league-wide lines underneath.

## 4e. Context tracking (since 2026-11-12) - all free, all from ESPN

| Tracked | Where | Used in grades? |
| --- | --- | --- |
| **Injuries** (ESPN league report, every run) | `injuries.json`; `grades.json` -> `out` | Players listed Out are removed. Day-to-day / questionable = one grade down. |
| **Teammate out** (a top-3 minutes teammate ruled out) | `accuracy.json` -> `context_effects.teammate_out` | Yes - half of the measured lift (scoring about +18%, rebounds +14%, assists +13% measured). |
| **Role change** (new starter / moved to bench, from his last game) | player `role`, `starts_l5` | New starter yes (+26% scoring measured); to-bench not yet (too few cases). |
| **Minutes trend** (last 3 vs season) | player `min_trend`, `min_l3` | No - tested, no effect on scoring. Displayed. |
| **Rest and travel** (back-to-back, 3 in 4, 4 in 6, road-trip game number, time zones) | `projections.json` -> `home_sched` / `away_sched` | Team model: back-to-back -1.5, 3-in-4 -1.5. Time zones and road trips are tracked only (noise so far). |
| **Game script** (minutes and points in 15+ point games; team 4th quarters in blowouts) | player `blowout`, team `blowout_script` | Heavy favourite / heavy underdog effects, measured from pregame odds of a blowout. |
| **With/without splits** vs each top-5 teammate | player `splits` | No - samples are tiny. Shown in the grader when that teammate is out. |
| **Defense by position** (what a team allows to guards / forwards / centers) | team `allowed_by_position` | Not yet - needs positions, which are stored from now on (REBUILD back-fills them). |
| **Referee crews** | `refs.json`; tonight's crew on each matchup card when ESPN has posted it | No - display only. |
| **Line movement** | `lines/history-<date>.csv`; `projections.json` -> `open` | Display only. |
| **Player prop lines** | `lines/<date>.csv` | Yes, automatically, whenever a file exists. Type them by hand (section 4b), or set an `ODDS_API_KEY` (The Odds API free tier, 500 credits/month, no card): the tracker then pulls points/rebounds/assists lines once a day and stops itself before the free allowance runs out. With no key nothing is called. |

Every effect above is re-measured on every run (`accuracy.json` -> `context_effects`), needs 40+ cases before it is
used, is applied at half strength, and all of them together can never move a projection more than 20%.

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
