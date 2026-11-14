# SIGNAL — overview, where everything lives, and the rules

SIGNAL (signaldtt.netlify.app) is Zachary's free-data sports tracker. The NBA part tracks every team and player,
grades picks, and grades itself. No paid data, ever.

## Where the data lives
- **GitHub:** github.com/zackh608/signal-report — `nba_tracker.py`, `data/nba/*.json`, `site/nba.html`, `RUNBOOK.md`,
  `tools/` (backtests and experiments). The daily GitHub workflow and the PC scheduled task both push here.
- **PC tracker:** `Desktop\SIGNAL NBA Tracker` (same script + data). Shortcuts: RUN NBA TRACKER, REBUILD, RATES ONLY,
  GET BOOK LINES, PUBLISH TO SITE, DAILY AUTO (scheduled 8:30 AM via "SIGNAL daily").
- **Site deploy folder:** `Desktop\SIGNAL SITE DEPLOY` (drag onto Netlify). nba.html tabs: TODAY, COVERS, PLAYERS, TEAMS, PAPER CARD.
- **Jarvis:** `C:\Users\harol\Jarvis` — props-desk agent (`core/nba_props.py`, `agents/props_desk/`), record in signal_picks,
  lessons in `memory/learned.md`, hand-logged picks in `data/manual_picks/<date>.json`.

## Data files (data/nba/)
| File | What |
|---|---|
| team_games.json / player_games.json | every game row, every box stat, closing total + spread per game |
| nba_team_stats.json | per team: records, quarter/half splits, every stat for/against with league rank, ATS + O/U vs closing lines |
| nba_hit_rates.json | per player x market: season average (proj), sd, hit rates, minutes, role, splits |
| projections.json | today: projected score, total, margin, win %, rest/travel, gap to the posted line |
| grades.json | today: every player x market graded (probability + letter), out list, possible returns, matchup edges |
| accuracy.json | SIGNAL grading itself vs the book; measured matchup and context effects |
| injuries.json / refs.json / lines/ | ESPN injury report; referee table; posted lines and line history |

## How picks are graded
- Player projection = season average of 15+ minute games, adjusted by **measured** matchup effects (assists, rebounds,
  steals, turnovers, FT, pace) and **measured** context (teammate out, new starter, back-to-back, 3-in-4, blowout risk).
- Probability vs a line -> grade: A+ 70%, A 65%, B 60%, C 55%, D 52%, F below. Break-even at -110 is 52.4%.
- Team spreads/totals: SIGNAL's model margin vs the book, counted at half strength.

## Rules (from what went wrong)
1. Tally yesterday's picks honestly from box scores before analysing today.
2. Check the injury report AND who is coming back (Coby White, 11/12) before any player pick.
3. A player prop graded only against SIGNAL's own baseline is not a bet — give the line at which it would grade B.
4. No team totals; SIGNAL has no edge on them (32-31). Spreads only as weak leans, stated as such.
5. Max 2 legs, different games. Parlays mostly miss by exactly one leg — that is the math, not bad luck.
6. If nothing clears, the answer is nothing.
7. Grade on stats/matchups/injuries/rest only, never on price.
