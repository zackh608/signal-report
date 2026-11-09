# signal-report

Sports data tracker for SIGNAL (signaldtt.netlify.app). Free public data only; runs daily in GitHub Actions and publishes to a gist.

| Script | Output | Covers |
| --- | --- | --- |
| `build_signal.py` | `mlb_team_profiles.md` (gist) | MLB / NBA / WNBA team standings, slate, pace, MLB comeback tally |
| `nba_tracker.py` | `nba_player_props.md` (gist) + `data/nba/*.json` (repo) | Every NBA team and every player game log, Over/Under hit rates (L5 / L10 / L20 / season), streaks, trap flags |

## NBA tracker

* Sources: ESPN public JSON first, NBA.com (`cdn.nba.com`) as automatic fallback.
* State: `data/nba/player_games.json`, `team_games.json`, `ingested_days.json` are committed back by the workflow, so a missed run is backfilled next time rather than skipped.
* Hit rates use games with 15+ minutes. With no posted line, the line is the median of the last 20 eligible games rounded to .5 (a season baseline) and labelled `signal-median`; real lines go in `data/nba/lines/` (see its README).
* Manual backfill: Actions → *SIGNAL daily report* → *Run workflow* → set `nba_from` (e.g. `2026-10-20`). Locally: `python nba_tracker.py --from 2026-10-20 --no-gist`.
* Rates only (no network): `python nba_tracker.py --rates-only --no-gist`.
