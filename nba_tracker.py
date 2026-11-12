#!/usr/bin/env python3
"""SIGNAL NBA tracker: every team + every player game log, plus Over/Under hit rates.

Free data only (ESPN public JSON). State lives in data/nba/*.json and is committed back
to the repo by the workflow, so a missed day is backfilled on the next run instead of skipped.

Run modes
  python nba_tracker.py                 # pull every missing date from SEASON_START..yesterday, rebuild rates
  python nba_tracker.py --from 2026-10-20 --to 2026-11-01   # explicit window
  python nba_tracker.py --rates-only    # recompute hit rates from stored logs (no network)

Lines
  Drop a CSV at data/nba/lines/YYYY-MM-DD.csv with columns  player,market,line[,book]
  and that day's props are graded against the real posted line. With no CSV, SIGNAL grades
  against a synthetic line = median of the last 20 eligible games rounded to .5 and labels it
  "signal-median" (a season baseline, so L5/L10 rates against it show a real recent trend).
"""
import os, sys, json, csv, datetime, statistics, urllib.request, urllib.error, time, argparse

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "nba")
LINES_DIR = os.path.join(DATA, "lines")
PLAYER_LOG = os.path.join(DATA, "player_games.json")
TEAM_LOG = os.path.join(DATA, "team_games.json")
RATES_JSON = os.path.join(DATA, "nba_hit_rates.json")
TEAM_JSON = os.path.join(DATA, "nba_team_stats.json")
REPORT_MD = os.path.join(ROOT, "nba_player_props.md")

SEASON_START = datetime.date(2026, 10, 20)   # adjust if the opener moves
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
MIN_MINUTES = 15          # filter DNP / garbage-time cameos out of hit-rate samples
WINDOWS = (5, 10, 20)
PLAYER_MARKETS = {        # market -> function(row) -> value
    "PTS": lambda r: r["pts"], "REB": lambda r: r["reb"], "AST": lambda r: r["ast"],
    "3PM": lambda r: r["fg3m"], "STL": lambda r: r["stl"], "BLK": lambda r: r["blk"],
    "PRA": lambda r: r["pts"] + r["reb"] + r["ast"], "PR": lambda r: r["pts"] + r["reb"],
    "PA": lambda r: r["pts"] + r["ast"], "RA": lambda r: r["reb"] + r["ast"],
    "S+B": lambda r: r["stl"] + r["blk"],
}
def _seg(r, keys, opp=False):
    return sum(r[("o" if opp else "") + k] for k in keys)

TEAM_MARKETS = {  # every scoring segment, own / opp / combined, plus margin and team threes
    "TEAM_PTS": lambda r: r["pts"], "OPP_PTS": lambda r: r["opp_pts"],
    "GAME_TOTAL": lambda r: r["pts"] + r["opp_pts"], "MARGIN": lambda r: r["pts"] - r["opp_pts"],
    "1Q_PTS": lambda r: r["q1"], "1Q_OPP": lambda r: r["oq1"], "1Q_TOTAL": lambda r: r["q1"] + r["oq1"],
    "2Q_PTS": lambda r: r["q2"], "2Q_TOTAL": lambda r: r["q2"] + r["oq2"],
    "3Q_PTS": lambda r: r["q3"], "3Q_TOTAL": lambda r: r["q3"] + r["oq3"],
    "4Q_PTS": lambda r: r["q4"], "4Q_TOTAL": lambda r: r["q4"] + r["oq4"],
    "1H_PTS": lambda r: _seg(r, ("q1", "q2")), "1H_OPP": lambda r: _seg(r, ("q1", "q2"), True),
    "1H_TOTAL": lambda r: _seg(r, ("q1", "q2")) + _seg(r, ("q1", "q2"), True),
    "1H_MARGIN": lambda r: _seg(r, ("q1", "q2")) - _seg(r, ("q1", "q2"), True),
    "2H_PTS": lambda r: _seg(r, ("q3", "q4")) + r["ot"], "2H_OPP": lambda r: _seg(r, ("q3", "q4"), True) + r["oot"],
    "2H_TOTAL": lambda r: _seg(r, ("q3", "q4")) + r["ot"] + _seg(r, ("q3", "q4"), True) + r["oot"],
    "TEAM_3PM": lambda r: r.get("fg3m", 0), "TEAM_REB": lambda r: r.get("reb", 0),
    "TEAM_AST": lambda r: r.get("ast", 0), "TEAM_TOV": lambda r: r.get("tov", 0),
}
# ESPN boxscore.teams statistic names -> our keys ("a-b" strings are split made/att)
ESPN_TEAM_STATS = {
    "fieldGoalsMade-fieldGoalsAttempted": ("fgm", "fga"),
    "threePointFieldGoalsMade-threePointFieldGoalsAttempted": ("fg3m", "fg3a"),
    "freeThrowsMade-freeThrowsAttempted": ("ftm", "fta"),
    "totalRebounds": "reb", "offensiveRebounds": "oreb", "defensiveRebounds": "dreb",
    "assists": "ast", "steals": "stl", "blocks": "blk", "totalTurnovers": "tov",
    "turnovers": "tov_", "pointsInPaint": "pitp", "fastBreakPoints": "fb",
    "turnoverPoints": "pot", "largestLead": "lead_max", "fouls": "pf",
}
NBA_TEAM_STATS = {
    "fieldGoalsMade": "fgm", "fieldGoalsAttempted": "fga", "threePointersMade": "fg3m",
    "threePointersAttempted": "fg3a", "freeThrowsMade": "ftm", "freeThrowsAttempted": "fta",
    "reboundsTotal": "reb", "reboundsOffensive": "oreb", "reboundsDefensive": "dreb",
    "assists": "ast", "steals": "stl", "blocks": "blk", "turnoversTotal": "tov",
    "pointsInThePaint": "pitp", "pointsFastBreak": "fb", "pointsFromTurnovers": "pot",
    "pointsSecondChance": "p2c", "benchPoints": "bench", "biggestLead": "lead_max",
    "foulsPersonal": "pf",
}
TEAM_BOX_KEYS = ("fgm", "fga", "fg3m", "fg3a", "ftm", "fta", "reb", "oreb", "dreb", "ast", "stl",
                 "blk", "tov", "pitp", "fb", "pot", "p2c", "bench", "lead_max", "pf")
GIST = os.environ.get("GIST_ID", "a7ebd591bd69d8a1bd777a60ab7ce089")
TOKEN = os.environ.get("GIST_TOKEN")
STAMP = datetime.datetime.now().astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------- io helpers
def get(url, tries=3, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
        "Accept": "application/json"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as f:
                return json.loads(f.read().decode())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def load(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, separators=(",", ":"), ensure_ascii=False)


def num(s):
    try:
        return float(str(s).replace("+", ""))
    except (TypeError, ValueError):
        return 0.0


def made(s):
    """ESPN gives '7-15' for FG/3PT/FT; return made."""
    return num(str(s).split("-")[0])


def minutes(s):
    s = str(s or "0")
    if ":" in s:
        m, sec = s.split(":")
        return num(m) + num(sec) / 60
    return num(s)


# ---------------------------------------------------------------- fetch
def final_event_ids(day):
    board = get(f"{ESPN}/scoreboard?dates={day:%Y%m%d}")
    ids = []
    for ev in board.get("events", []):
        st = ev.get("status", {}).get("type", {})
        if st.get("completed") or st.get("name") == "STATUS_FINAL":
            ids.append(ev["id"])
    return ids


def team_row(gid, day, sides, ha, opp):
    """One team's game row from a sides dict {home/away: {abbr,name,pts,q,ot,box}}."""
    s, o = sides[ha], sides[opp]
    row = {"game_id": gid, "date": day.isoformat(), "team": s["abbr"], "team_name": s["name"],
           "opp": o["abbr"], "home": ha == "home", "pts": s["pts"], "opp_pts": o["pts"],
           "q1": s["q"][0], "q2": s["q"][1], "q3": s["q"][2], "q4": s["q"][3], "ot": s["ot"],
           "oq1": o["q"][0], "oq2": o["q"][1], "oq3": o["q"][2], "oq4": o["q"][3], "oot": o["ot"],
           "win": s["pts"] > o["pts"]}
    for k in TEAM_BOX_KEYS:
        if k in s["box"]:
            row[k] = s["box"][k]
        if k in o["box"]:
            row["opp_" + k] = o["box"][k]
    return row


def parse_odds(g):
    """Closing/pregame market from an ESPN summary or scoreboard competition: {total, home_spread, book} or {}.
    home_spread is the number added to the HOME score (favorite negative). ESPN exposes this as `pickcenter`
    on the summary and `odds` on the scoreboard; both carry overUnder + spread + provider. Free, no key."""
    cands = (g.get("pickcenter") or []) + ((g.get("header", {}).get("competitions") or [{}])[0].get("odds") or []) \
            + (g.get("odds") or [])
    for o in cands:
        try:
            total = o.get("overUnder")
            spread = o.get("spread")
            if total in (None, "") and spread in (None, ""):
                continue
            out = {"book": (o.get("provider") or {}).get("name") or "ESPN"}
            if total not in (None, ""):
                out["total"] = float(total)
            if spread not in (None, ""):
                sp = float(spread)
                # ESPN's `spread` is from the favorite's side; `details` says who ("BOS -5.5"). Normalise to home.
                home_fav = (o.get("homeTeamOdds") or {}).get("favorite")
                away_fav = (o.get("awayTeamOdds") or {}).get("favorite")
                if home_fav is None and away_fav is None:
                    det = str(o.get("details", ""))
                    home_abbr = (o.get("_home_abbr") or "")
                    home_fav = det.startswith(home_abbr + " ") if home_abbr else None
                if home_fav is False or away_fav is True:
                    out["home_spread"] = abs(sp)
                elif home_fav is True or away_fav is False:
                    out["home_spread"] = -abs(sp)
                else:
                    out["home_spread"] = sp   # already home-relative (scoreboard style)
            return out
        except (TypeError, ValueError):
            continue
    return {}


def attach_odds(team_rows, odds):
    """Write book fields onto both team rows: line_total, line_spread (added to THIS team's score), line_book."""
    if not odds:
        return
    for r in team_rows:
        if "total" in odds:
            r["line_total"] = odds["total"]
        if "home_spread" in odds:
            r["line_spread"] = odds["home_spread"] if r["home"] else -odds["home_spread"]
        r["line_book"] = odds.get("book", "ESPN")


def parse_game(event_id, day):
    """Return (team_rows, player_rows) for one final game."""
    g = get(f"{ESPN}/summary?event={event_id}")
    comp = g["header"]["competitions"][0]
    sides = {}
    for c in comp["competitors"]:
        t = c["team"]
        # ESPN gives each period as {"value": 28} on the scoreboard but {"displayValue": "28"} on the
        # summary endpoint; take whichever is present or every quarter silently becomes 0.
        lines = [num(x.get("value") if x.get("value") not in (None, "") else x.get("displayValue"))
                 for x in c.get("linescores", [])]
        sides[c["homeAway"]] = {
            "abbr": t.get("abbreviation"), "name": t.get("displayName"),
            "pts": num(c.get("score")), "q": (lines + [0, 0, 0, 0])[:4],
            "ot": sum(lines[4:]), "box": {},
        }
    # team box-score stats
    for tb in g.get("boxscore", {}).get("teams", []):
        abbr = tb.get("team", {}).get("abbreviation")
        side = next((s for s in sides.values() if s["abbr"] == abbr), None)
        if not side:
            continue
        for st in tb.get("statistics", []):
            key = ESPN_TEAM_STATS.get(st.get("name"))
            if not key:
                continue
            dv = str(st.get("displayValue", "0"))
            if isinstance(key, tuple):
                parts = dv.split("-")
                side["box"][key[0]] = num(parts[0])
                side["box"][key[1]] = num(parts[1]) if len(parts) > 1 else 0
            else:
                side["box"][key] = num(dv)
        if "tov" not in side["box"] and "tov_" in side["box"]:
            side["box"]["tov"] = side["box"]["tov_"]
        side["box"].pop("tov_", None)
    if "home" not in sides or "away" not in sides:
        return [], []
    team_rows = [team_row(event_id, day, sides, ha, opp)
                 for ha, opp in (("home", "away"), ("away", "home"))]
    attach_odds(team_rows, parse_odds(g))

    player_rows = []
    for tb in g.get("boxscore", {}).get("players", []):
        abbr = tb.get("team", {}).get("abbreviation")
        opp = next((r["opp"] for r in team_rows if r["team"] == abbr), None)
        for block in tb.get("statistics", []):
            labels = block.get("labels") or block.get("names") or []
            idx = {l: i for i, l in enumerate(labels)}
            for a in block.get("athletes", []):
                st = a.get("stats") or []
                if a.get("didNotPlay") or not st or len(st) < len(labels):
                    continue
                v = lambda k: st[idx[k]] if k in idx else 0
                row = {
                    "game_id": event_id, "date": day.isoformat(), "team": abbr, "opp": opp,
                    "player_id": a["athlete"]["id"], "player": a["athlete"]["displayName"],
                    "starter": bool(a.get("starter")), "min": round(minutes(v("MIN")), 1),
                    "pts": num(v("PTS")), "reb": num(v("REB")), "ast": num(v("AST")),
                    "fg3m": made(v("3PT")), "fgm": made(v("FG")), "ftm": made(v("FT")),
                    "stl": num(v("STL")), "blk": num(v("BLK")), "tov": num(v("TO")),
                    "oreb": num(v("OREB")), "dreb": num(v("DREB")), "pf": num(v("PF")),
                }
                player_rows.append(row)
    return team_rows, player_rows


# ---- NBA.com fallback (cdn.nba.com static JSON; no key, no Referer games) -------------
NBA_SCHED = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"
NBA_BOX = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{gid}.json"
_sched_cache = {}


def nba_final_game_ids(day):
    """gameIds of final games on `day` from the NBA.com season schedule."""
    if not _sched_cache:
        for gd in get(NBA_SCHED)["leagueSchedule"]["gameDates"]:
            d = gd["gameDate"].split(" ")[0]           # "10/21/2026 00:00:00"
            m, dd, y = d.split("/")
            key = f"{y}-{int(m):02d}-{int(dd):02d}"
            _sched_cache[key] = gd.get("games", [])
    return [g["gameId"] for g in _sched_cache.get(day.isoformat(), [])
            if g.get("gameStatus") == 3 and str(g["gameId"]).startswith("002")]  # 002 = regular season


def iso_minutes(s):
    """'PT34M12.00S' -> 34.2"""
    s = str(s or "")
    try:
        m = float(s.split("PT")[1].split("M")[0]) if "M" in s else 0
        sec = float(s.split("M")[1].rstrip("S")) if "M" in s and s.endswith("S") else 0
        return m + sec / 60
    except (IndexError, ValueError):
        return 0.0


def parse_nba_game(gid, day):
    g = get(NBA_BOX.format(gid=gid))["game"]
    raw = {"home": g["homeTeam"], "away": g["awayTeam"]}
    sides = {}
    for ha, t in raw.items():
        q = [num(p.get("score")) for p in t.get("periods", [])]
        box = {NBA_TEAM_STATS[k]: num(v) for k, v in (t.get("statistics") or {}).items()
               if k in NBA_TEAM_STATS}
        sides[ha] = {"abbr": t["teamTricode"],
                     "name": f"{t.get('teamCity','')} {t.get('teamName','')}".strip(),
                     "pts": num(t["score"]), "q": (q + [0, 0, 0, 0])[:4], "ot": sum(q[4:]), "box": box}
    team_rows = [team_row(gid, day, sides, ha, opp) for ha, opp in (("home", "away"), ("away", "home"))]
    player_rows = []
    for ha, opp in (("home", "away"), ("away", "home")):
        s, o = raw[ha], raw[opp]
        for p in s.get("players", []):
            st = p.get("statistics") or {}
            if p.get("status") != "ACTIVE" and not st.get("minutes"):
                continue
            mins = iso_minutes(st.get("minutes"))
            if mins == 0 and not st.get("points"):
                continue
            player_rows.append({
                "game_id": gid, "date": day.isoformat(), "team": s["teamTricode"],
                "opp": o["teamTricode"], "player_id": str(p["personId"]), "player": p["name"],
                "starter": str(p.get("starter")) == "1", "min": round(mins, 1),
                "pts": num(st.get("points")), "reb": num(st.get("reboundsTotal")),
                "ast": num(st.get("assists")), "fg3m": num(st.get("threePointersMade")),
                "fgm": num(st.get("fieldGoalsMade")), "ftm": num(st.get("freeThrowsMade")),
                "stl": num(st.get("steals")), "blk": num(st.get("blocks")),
                "tov": num(st.get("turnovers")), "oreb": num(st.get("reboundsOffensive")),
                "dreb": num(st.get("reboundsDefensive")), "pf": num(st.get("foulsPersonal")),
            })
    return team_rows, player_rows


def fetch_day(day):
    """Try ESPN first, NBA.com second. Returns list of (game_id, team_rows, player_rows) and a source tag."""
    errors = []
    try:
        out = []
        for eid in final_event_ids(day):
            t, p = parse_game(eid, day)
            if t:
                out.append((eid, t, p))
            time.sleep(0.4)
        return out, "espn"
    except Exception as e:
        errors.append(f"espn: {type(e).__name__}: {e}")
    try:
        out = []
        for gid in nba_final_game_ids(day):
            t, p = parse_nba_game(gid, day)
            if t:
                out.append((gid, t, p))
            time.sleep(0.4)
        return out, "nba.com"
    except Exception as e:
        errors.append(f"nba.com: {type(e).__name__}: {e}")
    raise RuntimeError(" | ".join(errors))


def ingest(start, end):
    team_log = load(TEAM_LOG, {})      # game_id -> [team_rows]
    player_log = load(PLAYER_LOG, {})  # game_id -> [player_rows]
    done_days = load(os.path.join(DATA, "ingested_days.json"), [])
    day = start
    new_games = 0
    while day <= end:
        key = day.isoformat()
        if key in done_days:
            day += datetime.timedelta(days=1)
            continue
        try:
            games, src = fetch_day(day)
        except Exception as e:
            print(f"{key}: both sources failed ({e}); will retry next run")
            day += datetime.timedelta(days=1)
            continue
        # games already stored for this date, keyed by matchup so ESPN/NBA.com ids never duplicate
        have = {(r[0]["date"], frozenset(x["team"] for x in r)) for r in team_log.values()}
        added = 0
        for gid, t, p in games:
            sig = (key, frozenset(x["team"] for x in t))
            if sig in have:
                continue
            team_log[gid], player_log[gid] = t, p
            have.add(sig)
            added += 1
        new_games += added
        # mark complete when finals were found, or the day is old enough to be a true off-day
        if games or day < datetime.date.today() - datetime.timedelta(days=2):
            done_days.append(key)
        print(f"{key}: {len(games)} finals via {src}, {added} new")
        day += datetime.timedelta(days=1)
    save(TEAM_LOG, team_log)
    save(PLAYER_LOG, player_log)
    save(os.path.join(DATA, "ingested_days.json"), sorted(set(done_days)))
    return team_log, player_log, new_games


# ---------------------------------------------------------------- lines
def backfill_lines(team_log):
    """Fetch the closing total/spread for every stored ESPN game that lacks one. One summary call per game;
    NBA.com-sourced games (non-numeric ids) are skipped. Returns the number of games patched."""
    n = 0
    for gid, rows in team_log.items():
        if not str(gid).isdigit() or any("line_total" in r or "line_spread" in r for r in rows):
            continue
        try:
            odds = parse_odds(get(f"{ESPN}/summary?event={gid}"))
        except Exception as e:
            print(f"lines: {gid} failed ({e})")
            continue
        if odds:
            attach_odds(rows, odds)
            n += 1
        time.sleep(0.2)
    if n:
        save(TEAM_LOG, team_log)
    print(f"lines: backfilled {n} games")
    return n


def slate(day):
    """Today's games from the ESPN scoreboard: [{home, away, odds:{total,home_spread,book}}]. [] on failure."""
    try:
        sb = get(f"{ESPN}/scoreboard?dates={day:%Y%m%d}")
    except Exception as e:
        print(f"slate: scoreboard for {day} failed ({e})")
        return []
    games = []
    for ev in sb.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        side = {c.get("homeAway"): c["team"]["abbreviation"] for c in comp.get("competitors", []) if c.get("team")}
        if "home" not in side or "away" not in side:
            continue
        for o in comp.get("odds") or []:
            o["_home_abbr"] = side["home"]
        games.append({"home": side["home"], "away": side["away"], "odds": parse_odds({"odds": comp.get("odds") or []})})
    return games


def capture_today_lines(day, games=None):
    """Write today's pregame total/spread from the ESPN scoreboard to data/nba/lines/team-<day>.csv
    (home,segment,line,book) so Jarvis and the site grade against a posted number, not a median."""
    games = slate(day) if games is None else games
    out = []
    for g in games:
        home, odds = g["home"], g["odds"]
        if "total" in odds:
            out.append((home, "FULL", odds["total"], odds["book"]))
        if "home_spread" in odds:
            out.append((home, "SPREAD", odds["home_spread"], odds["book"]))
    if out:
        os.makedirs(LINES_DIR, exist_ok=True)
        with open(os.path.join(LINES_DIR, f"team-{day.isoformat()}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["home", "segment", "line", "book"])
            w.writerows(out)
    print(f"lines: captured {len(out)} posted numbers for {day}")
    return len(out)


def book_block(rows, val_fn, line_key):
    """Hit rate against each game's OWN posted line (rows newest first). None if no lines stored."""
    g = [(val_fn(r), r[line_key]) for r in rows if line_key in r]
    if not g:
        return None
    out = {"n_season": len(g), "over_season": sum(v > l for v, l in g), "push_season": sum(v == l for v, l in g)}
    for w in WINDOWS:
        s = g[:w]
        out[f"over_l{w}"] = sum(v > l for v, l in s)
        out[f"n_l{w}"] = len(s)
    out["avg_margin"] = round(statistics.fmean(v - l for v, l in g), 1)   # + = beats the number on average
    out["last_line"] = g[0][1]
    out["line_source"] = rows[0].get("line_book", "book") if rows else "book"
    return out


def cover_block(rows):
    """Against-the-spread record from stored closing spreads (rows newest first)."""
    g = [r["pts"] - r["opp_pts"] + r["line_spread"] for r in rows if "line_spread" in r]
    if not g:
        return None
    out = {"n_season": len(g), "cover_season": sum(x > 0 for x in g), "push_season": sum(x == 0 for x in g),
           "avg_margin": round(statistics.fmean(g), 1), "last_spread": [r["line_spread"] for r in rows if "line_spread" in r][0],
           "line_source": next(r.get("line_book", "book") for r in rows if "line_spread" in r)}
    for w in WINDOWS:
        s = g[:w]
        out[f"cover_l{w}"] = sum(x > 0 for x in s)
        out[f"n_l{w}"] = len(s)
    return out


def load_lines():
    """{(player_lower, MARKET): (line, book, date)} from the newest CSV per player/market."""
    out = {}
    if not os.path.isdir(LINES_DIR):
        return out
    for fn in sorted(os.listdir(LINES_DIR)):
        if not fn.endswith(".csv"):
            continue
        with open(os.path.join(LINES_DIR, fn), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    out[(r["player"].strip().lower(), r["market"].strip().upper())] = (
                        float(r["line"]), (r.get("book") or "book").strip(), fn[:-4])
                except (KeyError, ValueError):
                    pass
    return out


def half_round(x, mean=None):
    """Snap a median to a .5 line. A whole-number median can go either way, so pick the side the
    mean sits on (23.0 with mean 23.8 -> 23.5; with mean 22.4 -> 22.5). Low-count markets (steals,
    blocks) are where this matters most; the old +0.5 default made every UNDER look like a lock."""
    if x % 1:
        return round(x * 2) / 2
    if mean is not None and mean < x:
        return x - 0.5
    return x + 0.5


# ---------------------------------------------------------------- rates
def rate_block(vals, line):
    """vals newest-first."""
    out = {}
    for w in WINDOWS:
        s = vals[:w]
        if s:
            out[f"over_l{w}"] = sum(v > line for v in s)
            out[f"n_l{w}"] = len(s)
    out["over_season"] = sum(v > line for v in vals)
    out["n_season"] = len(vals)
    streak = 0
    if vals:
        side = vals[0] > line
        for v in vals:
            if (v > line) == side and v != line:
                streak += 1
            else:
                break
        out["streak"] = f"{'O' if side else 'U'}{streak}"
    out["avg_l5"] = round(statistics.fmean(vals[:5]), 1) if vals else None
    out["avg_l10"] = round(statistics.fmean(vals[:10]), 1) if vals else None
    out["median_l10"] = statistics.median(vals[:10]) if vals else None
    return out


def compute(team_log, player_log):
    lines = load_lines()
    # --- players
    by_player = {}
    for rows in player_log.values():
        for r in rows:
            by_player.setdefault(r["player_id"], []).append(r)
    players = []
    for pid, rows in by_player.items():
        rows.sort(key=lambda r: r["date"], reverse=True)
        eligible = [r for r in rows if r["min"] >= MIN_MINUTES]
        if len(eligible) < 3:
            continue
        head = rows[0]
        rec = {"player_id": pid, "player": head["player"], "team": head["team"],
               "gp": len(rows), "eligible_gp": len(eligible),
               "min_l5": round(statistics.fmean(r["min"] for r in rows[:5]), 1),
               "markets": {}}
        for mk, fn in PLAYER_MARKETS.items():
            vals = [fn(r) for r in eligible]
            lk = lines.get((head["player"].lower(), mk))
            if lk:
                line, src = lk[0], f"{lk[1]} ({lk[2]})"
            else:
                # baseline = median of the last 20 eligible games (season-ish), so an L5/L10 rate against it
                # measures a real recent trend. An L10 median would split L10 ~50/50 by construction.
                base = vals[:20]
                line, src = half_round(statistics.median(base), statistics.fmean(base)), "signal-median"
            blk = rate_block(vals, line)
            # proj: season mean of eligible games. Walk-forward on 1,081 player-games (2026-11-12) it beat the
            # L20 median, per-minute x minutes, opponent-adjusted and every recency blend; L5 average was WORST.
            proj = statistics.fmean(vals)
            blk.update({"line": line, "line_source": src,
                        "cushion": round((blk["median_l10"] or 0) - line, 1),
                        "proj": round(proj, 1), "proj_sd": round(statistics.pstdev(vals), 1) if len(vals) > 2 else None,
                        "proj_edge": round(proj - line, 1) if src != "signal-median" else None})
            # trap flag: recent window diverges hard from the longer sample
            if blk.get("n_l20", 0) >= 12 and blk.get("n_l5", 0) == 5:
                l5 = blk["over_l5"] / 5
                l20 = blk["over_l20"] / blk["n_l20"]
                blk["trap_flag"] = "HOT-STREAK-PRICED" if l5 - l20 >= .3 else \
                                   "COLD-STREAK-PRICED" if l20 - l5 >= .3 else ""
            rec["markets"][mk] = blk
        players.append(rec)
    players.sort(key=lambda p: (p["team"], p["player"]))

    # --- teams
    by_team = {}
    for rows in team_log.values():
        for r in rows:
            by_team.setdefault(r["team"], []).append(r)
    teams = [team_profile(abbr, rows) for abbr, rows in by_team.items()]
    winners = {t["team"] for t in teams if t["gp"] and t["w"] / t["gp"] > .5}
    for t in teams:
        t["records"]["vs_winning_teams"] = record(by_team[t["team"]], lambda r: r["opp"] in winners)
    teams.sort(key=lambda t: -(t["w"] / (t["gp"] or 1)))
    return players, teams


def avg(rows, fn, nd=1):
    vals = [fn(r) for r in rows]
    return round(statistics.fmean(vals), nd) if vals else None


def record(rows, cond):
    sub = [r for r in rows if cond(r)]
    return {"w": sum(r["win"] for r in sub), "l": sum(not r["win"] for r in sub), "gp": len(sub)}


def segments(rows):
    """Scoring profile for a set of games: own / opp / total per quarter, half, OT."""
    out = {}
    for name, own, opp in (("1Q", lambda r: r["q1"], lambda r: r["oq1"]),
                           ("2Q", lambda r: r["q2"], lambda r: r["oq2"]),
                           ("3Q", lambda r: r["q3"], lambda r: r["oq3"]),
                           ("4Q", lambda r: r["q4"], lambda r: r["oq4"]),
                           ("1H", lambda r: r["q1"] + r["q2"], lambda r: r["oq1"] + r["oq2"]),
                           ("2H", lambda r: r["q3"] + r["q4"] + r["ot"], lambda r: r["oq3"] + r["oq4"] + r["oot"]),
                           ("FULL", lambda r: r["pts"], lambda r: r["opp_pts"])):
        o, d = avg(rows, own), avg(rows, opp)
        out[name] = {"pts": o, "opp": d, "total": round(o + d, 1) if o is not None else None,
                     "margin": round(o - d, 1) if o is not None else None,
                     "won_pct": round(100 * sum(own(r) > opp(r) for r in rows) / len(rows)) if rows else None}
    return out


def four_factors(rows, prefix=""):
    """eFG%, TOV%, OREB%, FT rate, 3PA rate, pace estimate, rating. prefix 'opp_' = opponent side."""
    p = prefix
    need = (p + "fga", p + "fgm", p + "fg3m", p + "fta", p + "tov", p + "oreb")
    rows = [r for r in rows if all(k in r for k in need)]
    if not rows:
        return {}
    S = lambda k: sum(r[k] for r in rows)
    fga, fgm, fg3m, fg3a, fta, ftm = S(p + "fga"), S(p + "fgm"), S(p + "fg3m"), S(p + "fg3a"), S(p + "fta"), S(p + "ftm")
    tov, oreb = S(p + "tov"), S(p + "oreb")
    other = "" if p else "opp_"
    opp_dreb = S(other + "dreb") if all(other + "dreb" in r for r in rows) else 0
    pts = S("opp_pts" if p else "pts")
    poss = fga + 0.44 * fta - oreb + tov
    return {
        "efg_pct": round(100 * (fgm + 0.5 * fg3m) / fga, 1) if fga else None,
        "fg_pct": round(100 * fgm / fga, 1) if fga else None,
        "fg3_pct": round(100 * fg3m / fg3a, 1) if fg3a else None,
        "ft_pct": round(100 * ftm / fta, 1) if fta else None,
        "fg3a_rate": round(100 * fg3a / fga, 1) if fga else None,
        "ft_rate": round(100 * fta / fga, 1) if fga else None,
        "tov_pct": round(100 * tov / poss, 1) if poss else None,
        "oreb_pct": round(100 * oreb / (oreb + opp_dreb), 1) if (oreb + opp_dreb) else None,
        "pace": round(poss / len(rows), 1),
        "rating": round(100 * pts / poss, 1) if poss else None,   # ORtg (own) or DRtg (opp side)
        "fg3m_pg": round(fg3m / len(rows), 1), "fg3a_pg": round(fg3a / len(rows), 1),
        "fta_pg": round(fta / len(rows), 1), "tov_pg": round(tov / len(rows), 1),
    }


def team_profile(abbr, rows):
    rows.sort(key=lambda r: r["date"], reverse=True)
    gp = len(rows)
    w = sum(r["win"] for r in rows)
    home, away = [r for r in rows if r["home"]], [r for r in rows if not r["home"]]
    h1 = lambda r: r["q1"] + r["q2"]
    oh1 = lambda r: r["oq1"] + r["oq2"]
    rec = {
        "team": abbr, "team_name": rows[0]["team_name"], "gp": gp, "w": w, "l": gp - w,
        "last_game": rows[0]["date"],
        "records": {
            "overall": {"w": w, "l": gp - w, "gp": gp},
            "home": record(rows, lambda r: r["home"]), "away": record(rows, lambda r: not r["home"]),
            "last5": record(rows[:5], lambda r: True), "last10": record(rows[:10], lambda r: True),
            "won_1q": record(rows, lambda r: r["q1"] > r["oq1"]),
            "lost_1q": record(rows, lambda r: r["q1"] < r["oq1"]),
            "led_at_half": record(rows, lambda r: h1(r) > oh1(r)),
            "trailed_at_half": record(rows, lambda r: h1(r) < oh1(r)),
            "won_3q": record(rows, lambda r: r["q3"] > r["oq3"]),
            "won_4q": record(rows, lambda r: r["q4"] > r["oq4"]),
            "close_games_5": record(rows, lambda r: abs(r["pts"] - r["opp_pts"]) <= 5),
            "blowouts_15": record(rows, lambda r: abs(r["pts"] - r["opp_pts"]) >= 15),
            "overtime": record(rows, lambda r: r["ot"] > 0 or r["oot"] > 0),
            "vs_winning_teams": None,  # filled after all profiles exist
        },
        "scoring": {
            "season": segments(rows), "last5": segments(rows[:5]), "last10": segments(rows[:10]),
            "home": segments(home), "away": segments(away),
        },
        "quarters_won": {q: sum(r[q] > r["o" + q] for r in rows) for q in ("q1", "q2", "q3", "q4")},
        "comebacks": {
            "wins_after_trailing_half": sum(r["win"] and h1(r) < oh1(r) for r in rows),
            "losses_after_leading_half": sum((not r["win"]) and h1(r) > oh1(r) for r in rows),
            "wins_after_trailing_3q": sum(r["win"] and (h1(r) + r["q3"]) < (oh1(r) + r["oq3"]) for r in rows),
            "avg_largest_lead": avg(rows, lambda r: r.get("lead_max", 0)),
        },
        "four_factors": {"offense": four_factors(rows), "defense": four_factors(rows, "opp_"),
                         "offense_l10": four_factors(rows[:10]), "defense_l10": four_factors(rows[:10], "opp_")},
        "box_per_game": {k: avg(rows, lambda r, k=k: r.get(k, 0)) for k in TEAM_BOX_KEYS if any(k in r for r in rows)},
        "opp_box_per_game": {k: avg(rows, lambda r, k=k: r.get("opp_" + k, 0)) for k in TEAM_BOX_KEYS if any("opp_" + k in r for r in rows)},
        "game_log": [{**{k: r[k] for k in ("date", "opp", "home", "pts", "opp_pts", "q1", "q2", "q3", "q4", "ot",
                                           "oq1", "oq2", "oq3", "oq4", "oot", "win")},
                      **{k: r[k] for k in ("line_total", "line_spread", "line_book") if k in r}} for r in rows],
        "markets": {},
    }
    # graded against the POSTED number for each game (closing total / spread) - the only hit rate that means anything
    rec["book"] = {
        "GAME_TOTAL": book_block(rows, lambda r: r["pts"] + r["opp_pts"], "line_total"),
        "COVER": cover_block(rows),
    }
    # back-compat fields used by the report
    rec["ppg"], rec["opp_ppg"] = rec["scoring"]["season"]["FULL"]["pts"], rec["scoring"]["season"]["FULL"]["opp"]
    rec["ppg_l5"], rec["opp_ppg_l5"] = rec["scoring"]["last5"]["FULL"]["pts"], rec["scoring"]["last5"]["FULL"]["opp"]
    for mk, fn in TEAM_MARKETS.items():
        vals = [fn(r) for r in rows]
        if not any(vals) and mk.startswith("TEAM_"):
            continue  # box stat missing from source
        line = half_round(statistics.median(vals[:20]), statistics.fmean(vals[:20]))  # L20 baseline
        blk = rate_block(vals, line)
        blk.update({"line": line, "line_source": "signal-median",
                    "cushion": round((blk["median_l10"] or 0) - line, 1),
                    "home_over": sum(fn(r) > line for r in home), "home_n": len(home),
                    "away_over": sum(fn(r) > line for r in away), "away_n": len(away)})
        rec["markets"][mk] = blk
    return rec


# ---------------------------------------------------------------- projection model
# Chosen by walk-forward test on 2026-11-12 (112 games): pace x efficiency with every rating shrunk toward the
# league average (K pseudo-games) beat the old own-median line by ~1.8 pts on totals and margins, and nothing
# tested (recency weighting, heavier/lighter shrinkage) beat it reliably. Totals are barely predictable beyond the
# league average; margins carry real signal. Re-run tools/backtest.py before changing any constant here.
SHRINK_K = 8            # pseudo-games of league-average mixed into every team rating
B2B_PENALTY = 1.5       # points off a team playing the second night of a back-to-back
MODEL_MIN_GAMES = 3     # both teams need this many games or no projection is made
SEG_SHARE = {"1Q": 0.25, "1H": 0.5, "2H": 0.5}   # replaced by league shares when computed


def _poss(r):
    try:
        return (r["fga"] + 0.44 * r["fta"] - r["oreb"] + r["tov"]
                + r["opp_fga"] + 0.44 * r["opp_fta"] - r["opp_oreb"] + r["opp_tov"]) / 2
    except KeyError:
        return None


def _shrunk(vals, prior, k=SHRINK_K):
    return (sum(vals) + k * prior) / (len(vals) + k) if vals else prior


def league_context(rows):
    """League averages from a list of team rows (all before the game being predicted)."""
    rows = [r for r in rows if _poss(r)]
    if len(rows) < 40:
        return None
    pts = statistics.fmean(r["pts"] for r in rows)
    pos = statistics.fmean(_poss(r) for r in rows)
    home = [r for r in rows if r["home"]]
    hca = statistics.fmean(r["pts"] - r["opp_pts"] for r in home) / 2 if home else 1.5
    full = sum(r["pts"] for r in rows) or 1
    return {"pts": pts, "pos": pos, "eff": pts / pos, "hca": hca,
            "share": {"1Q": sum(r["q1"] for r in rows) / full,
                      "1H": sum(r["q1"] + r["q2"] for r in rows) / full,
                      "2H": sum(r["q3"] + r["q4"] + r["ot"] for r in rows) / full},
            "margin_sd": statistics.pstdev([r["pts"] - r["opp_pts"] for r in home]) if len(home) > 5 else 14.0}


def predict_game(H, A, lg, rest_h=3, rest_a=3):
    """H, A = each team's prior rows (any order). Returns projected home/away points or None."""
    H, A = [r for r in H if _poss(r)], [r for r in A if _poss(r)]
    if lg is None or len(H) < MODEL_MIN_GAMES or len(A) < MODEL_MIN_GAMES:
        return None
    pace = _shrunk([_poss(r) for r in H], lg["pos"]) * _shrunk([_poss(r) for r in A], lg["pos"]) / lg["pos"]
    off = lambda X: _shrunk([r["pts"] / _poss(r) for r in X], lg["eff"])
    dfn = lambda X: _shrunk([r["opp_pts"] / _poss(r) for r in X], lg["eff"])
    ph = pace * off(H) * dfn(A) / lg["eff"] + lg["hca"] - (B2B_PENALTY if rest_h == 1 else 0)
    pa = pace * off(A) * dfn(H) / lg["eff"] - lg["hca"] - (B2B_PENALTY if rest_a == 1 else 0)
    return ph, pa


def _rest_days(rows, date):
    prior = [r["date"] for r in rows if r["date"] < date]
    if not prior:
        return 3
    return (datetime.date.fromisoformat(date) - datetime.date.fromisoformat(max(prior))).days


def _win_prob(margin, sd):
    """P(home wins) from projected margin, normal error with the model's own walk-forward sd."""
    import math
    return round(0.5 * (1 + math.erf(margin / (sd * math.sqrt(2)))), 3)


def walk_forward_accuracy(team_log):
    """Predict every stored game from prior games only and score it. This is SIGNAL grading itself:
    model vs the old own-median line vs league average vs (when stored) the book's closing number."""
    games = []
    for rows in team_log.values():
        if len(rows) == 2:
            h, a = (rows[0], rows[1]) if rows[0]["home"] else (rows[1], rows[0])
            games.append((h["date"], h, a))
    games.sort(key=lambda g: g[0])
    hist, seen = {}, []
    err = {k: {"total": [], "margin": [], "team_pts": []} for k in ("signal_model", "own_median", "league_avg", "book_close")}
    winner = {"signal_model": [], "book_close": []}
    vs_book = {"total_closer": [], "margin_closer": [], "ou_side": [], "ats_side": []}
    resid = []
    for date, h, a in games:
        H, A = hist.get(h["team"], []), hist.get(a["team"], [])
        lg = league_context(seen)
        p = predict_game(H, A, lg, _rest_days(H, date), _rest_days(A, date))
        if p:
            ph, pa = p
            at, am = h["pts"] + a["pts"], h["pts"] - a["pts"]
            def put(k, xh, xa):
                err[k]["total"].append(abs(xh + xa - at)); err[k]["margin"].append(abs(xh - xa - am))
                err[k]["team_pts"] += [abs(xh - h["pts"]), abs(xa - a["pts"])]
            put("signal_model", ph, pa)
            put("own_median", statistics.median(r["pts"] for r in H[-20:]), statistics.median(r["pts"] for r in A[-20:]))
            put("league_avg", lg["pts"] + lg["hca"], lg["pts"] - lg["hca"])
            winner["signal_model"].append((ph - pa > 0) == (am > 0))
            resid.append(ph - pa - am)
            if "line_total" in h and "line_spread" in h:
                bt, bm = h["line_total"], -h["line_spread"]          # book's implied total and home margin
                err["book_close"]["total"].append(abs(bt - at)); err["book_close"]["margin"].append(abs(bm - am))
                err["book_close"]["team_pts"] += [abs((bt + bm) / 2 - h["pts"]), abs((bt - bm) / 2 - a["pts"])]
                winner["book_close"].append((bm > 0) == (am > 0))
                vs_book["total_closer"].append(abs(ph + pa - at) < abs(bt - at))
                vs_book["margin_closer"].append(abs(ph - pa - am) < abs(bm - am))
                if at != bt and abs(ph + pa - bt) >= 3:               # model disagrees with the total by 3+
                    vs_book["ou_side"].append((ph + pa > bt) == (at > bt))
                if am != bm and abs(ph - pa - bm) >= 3:               # model disagrees with the spread by 3+
                    vs_book["ats_side"].append((ph - pa > bm) == (am > bm))
        hist.setdefault(h["team"], []).append(h); hist.setdefault(a["team"], []).append(a); seen += [h, a]
    m = lambda v: round(statistics.fmean(v), 2) if v else None
    pc = lambda v: round(100 * statistics.fmean(v), 1) if v else None
    out = {"generated": STAMP, "games_scored": len(err["signal_model"]["total"]),
           "method": f"pace x efficiency, ratings shrunk {SHRINK_K} games toward league avg, home court from data, "
                     f"-{B2B_PENALTY} on back-to-backs; every game predicted from prior games only",
           "mae": {k: {s: m(v) for s, v in d.items()} for k, d in err.items()},
           "winner_pct": {k: pc(v) for k, v in winner.items()},
           "margin_sd": round(statistics.pstdev(resid), 1) if len(resid) > 10 else 14.0,
           "vs_book": {"games_with_lines": len(vs_book["total_closer"]),
                       "model_closer_on_total_pct": pc(vs_book["total_closer"]),
                       "model_closer_on_margin_pct": pc(vs_book["margin_closer"]),
                       "ou_record_when_3pt_disagreement": [sum(vs_book["ou_side"]), len(vs_book["ou_side"]) - sum(vs_book["ou_side"])],
                       "ats_record_when_3pt_disagreement": [sum(vs_book["ats_side"]), len(vs_book["ats_side"]) - sum(vs_book["ats_side"])]}}
    return out


def project_slate(team_log, games, day, acc):
    """Projection for each of today's games, with the posted line and the gap to it when one exists."""
    by_team, allrows = {}, []
    for rows in team_log.values():
        for r in rows:
            by_team.setdefault(r["team"], []).append(r); allrows.append(r)
    lg = league_context(allrows)
    sd = (acc or {}).get("margin_sd") or 14.0
    out = []
    for g in games:
        H, A = by_team.get(g["home"], []), by_team.get(g["away"], [])
        d = day.isoformat()
        p = predict_game(H, A, lg, _rest_days(H, d), _rest_days(A, d))
        rec = {"home": g["home"], "away": g["away"], "book": g.get("odds") or {}}
        if not p:
            rec["ok"], rec["why"] = False, f"need {MODEL_MIN_GAMES}+ games for both teams"
        else:
            ph, pa = p
            rec.update({"ok": True, "home_pts": round(ph, 1), "away_pts": round(pa, 1), "total": round(ph + pa, 1),
                        "home_margin": round(ph - pa, 1), "home_win_prob": _win_prob(ph - pa, sd),
                        "segments": {k: round((ph + pa) * v, 1) for k, v in lg["share"].items()},
                        "home_b2b": _rest_days(H, d) == 1, "away_b2b": _rest_days(A, d) == 1})
            bk = rec["book"]
            if "total" in bk:
                rec["total_vs_book"] = round(ph + pa - bk["total"], 1)
            if "home_spread" in bk:
                rec["margin_vs_book"] = round(ph - pa + bk["home_spread"], 1)   # + = model likes home vs the spread
        out.append(rec)
    return out


# ---------------------------------------------------------------- report
def pct(o, n):
    return f"{o}/{n} ({100*o/n:.0f}%)" if n else "-"


def report(players, teams, days):
    P = ["# SIGNAL NBA Tracker", "", f"Generated: `{STAMP}` | games through `{days[-1] if days else '-'}` "
         f"| {len(teams)} teams | {len(players)} players with 3+ eligible games", "",
         f"Hit rates use games with {MIN_MINUTES}+ minutes. Line source `signal-median` = median of the last 20 "
         "eligible games (the player's season baseline; no posted line captured); book lines come from "
         "data/nba/lines/*.csv.", ""]
    wl = lambda r: f"{r['w']}-{r['l']}" if r and r["gp"] else "-"
    P += ["## Team Board", "",
          "| Team | W-L | Home | Away | L10 | PPG | Opp | Net | Pace | ORtg | DRtg | 1Q | 1H | 2H | Led@half W-L | Trailed@half W-L |",
          "|" + " --- |" * 16]
    for t in teams:
        R, S, ff = t["records"], t["scoring"]["season"], t["four_factors"]
        P.append(f"| {t['team']} | {t['w']}-{t['l']} | {wl(R['home'])} | {wl(R['away'])} | {wl(R['last10'])} "
                 f"| {S['FULL']['pts']} | {S['FULL']['opp']} | {S['FULL']['margin']:+} "
                 f"| {ff['offense'].get('pace','-')} | {ff['offense'].get('rating','-')} | {ff['defense'].get('rating','-')} "
                 f"| {S['1Q']['pts']}-{S['1Q']['opp']} | {S['1H']['pts']}-{S['1H']['opp']} | {S['2H']['pts']}-{S['2H']['opp']} "
                 f"| {wl(R['led_at_half'])} | {wl(R['trailed_at_half'])} |")
    P.append("")

    P += ["## Team Segment Lines (signal-median) and L10 Over rates", "",
          "| Team | Total | 1Q tot | 1H tot | 2H tot | Team pts | 1Q pts | 1H pts | 2H pts | Margin | 1H margin |",
          "|" + " --- |" * 11]
    cell = lambda t, mk: (f"{t['markets'][mk]['line']} · {pct(t['markets'][mk].get('over_l10',0), t['markets'][mk].get('n_l10',0))}"
                          if mk in t["markets"] else "-")
    for t in teams:
        P.append(f"| {t['team']} | " + " | ".join(cell(t, mk) for mk in
                 ("GAME_TOTAL", "1Q_TOTAL", "1H_TOTAL", "2H_TOTAL", "TEAM_PTS", "1Q_PTS", "1H_PTS", "2H_PTS", "MARGIN", "1H_MARGIN")) + " |")
    P.append("")

    P += ["## Team Deep Dives", ""]
    for t in teams:
        R, Sc, ff, cb, qw = t["records"], t["scoring"], t["four_factors"], t["comebacks"], t["quarters_won"]
        P += [f"### {t['team_name']} ({t['w']}-{t['l']})", "",
              f"Home {wl(R['home'])} · Away {wl(R['away'])} · L5 {wl(R['last5'])} · L10 {wl(R['last10'])} · "
              f"vs .500+ teams {wl(R['vs_winning_teams'])} · Close (≤5) {wl(R['close_games_5'])} · "
              f"Blowouts (15+) {wl(R['blowouts_15'])} · OT {wl(R['overtime'])}", "",
              f"Won 1Q → {wl(R['won_1q'])} · Lost 1Q → {wl(R['lost_1q'])} · Led at half → {wl(R['led_at_half'])} · "
              f"Trailed at half → {wl(R['trailed_at_half'])} · Won 3Q → {wl(R['won_3q'])} · Won 4Q → {wl(R['won_4q'])}", "",
              f"Comebacks: {cb['wins_after_trailing_half']} wins after trailing at half, "
              f"{cb['losses_after_leading_half']} losses after leading at half, "
              f"{cb['wins_after_trailing_3q']} wins after trailing through 3. "
              f"Quarters won: 1Q {qw['q1']} · 2Q {qw['q2']} · 3Q {qw['q3']} · 4Q {qw['q4']} of {t['gp']}.", "",
              "| Segment | Season pts-opp (tot) | L5 pts-opp (tot) | L10 pts-opp (tot) | Home pts-opp | Away pts-opp | Won % |",
              "|" + " --- |" * 7]
        for seg in ("1Q", "2Q", "3Q", "4Q", "1H", "2H", "FULL"):
            s, l5, l10, h, a = (Sc["season"][seg], Sc["last5"][seg], Sc["last10"][seg], Sc["home"][seg], Sc["away"][seg])
            f = lambda x: f"{x['pts']}-{x['opp']} ({x['total']})" if x["pts"] is not None else "-"
            g = lambda x: f"{x['pts']}-{x['opp']}" if x["pts"] is not None else "-"
            P.append(f"| {seg} | {f(s)} | {f(l5)} | {f(l10)} | {g(h)} | {g(a)} | {s['won_pct']}% |")
        o, d = ff["offense"], ff["defense"]
        if o:
            P += ["", "| Four factors | Offense | Defense (opp) |", "| --- | --- | --- |",
                  f"| eFG% | {o.get('efg_pct')} | {d.get('efg_pct')} |",
                  f"| TOV% | {o.get('tov_pct')} | {d.get('tov_pct')} |",
                  f"| OREB% | {o.get('oreb_pct')} | {d.get('oreb_pct')} |",
                  f"| FT rate | {o.get('ft_rate')} | {d.get('ft_rate')} |",
                  f"| 3PA rate | {o.get('fg3a_rate')} | {d.get('fg3a_rate')} |",
                  f"| 3P% | {o.get('fg3_pct')} | {d.get('fg3_pct')} |",
                  f"| Rating | {o.get('rating')} | {d.get('rating')} |",
                  f"| Pace | {o.get('pace')} | |"]
            bx = t["box_per_game"]
            P += ["", "Per game: " + " · ".join(f"{k} {bx[k]}" for k in
                  ("fgm", "fga", "fg3m", "fg3a", "ftm", "fta", "reb", "oreb", "ast", "stl", "blk", "tov", "pitp", "fb", "pot", "bench")
                  if k in bx)]
        P.append("")

    # strongest trends: >=80% one side over L10 with n>=8, sorted by cushion magnitude
    trends = []
    for p in players:
        for mk, b in p["markets"].items():
            n = b.get("n_l10", 0)
            if n >= 8:
                o = b["over_l10"]
                # synthetic lines sit on the median, so demand a real gap between avg and line
                if b["line_source"] == "signal-median" and (abs((b["avg_l10"] or 0) - b["line"]) < 1 or b["line"] < 5):
                    continue  # synthetic lines: need a real gap, and no low-count markets (STL/BLK/S+B/low 3PM)
                if o / n >= .8 or o / n <= .2:
                    side = "OVER" if o / n >= .8 else "UNDER"
                    trends.append((abs(b["cushion"]), side, p, mk, b))
    trends.sort(key=lambda x: -x[0])
    P += ["## Strongest L10 Trends (80%+ one side)", "",
          "| Player | Team | Market | Line | Side | L5 | L10 | L20 | Streak | Avg L10 | Cushion | Source | Flag |",
          "|" + " --- |" * 13]
    for _, side, p, mk, b in trends[:60]:
        P.append(f"| {p['player']} | {p['team']} | {mk} | {b['line']} | {side} "
                 f"| {pct(b.get('over_l5',0), b.get('n_l5',0))} | {pct(b['over_l10'], b['n_l10'])} "
                 f"| {pct(b.get('over_l20',0), b.get('n_l20',0))} | {b.get('streak','-')} | {b['avg_l10']} "
                 f"| {b['cushion']:+} | {b['line_source']} | {b.get('trap_flag','')} |")
    P.append("")

    P += ["## Every Player (PTS / REB / AST / 3PM / PRA)", "",
          "| Player | Team | GP | Min L5 | PTS line · O L10 | REB line · O L10 | AST line · O L10 | 3PM line · O L10 | PRA line · O L10 |",
          "|" + " --- |" * 9]
    for p in players:
        cells = []
        for mk in ("PTS", "REB", "AST", "3PM", "PRA"):
            b = p["markets"][mk]
            cells.append(f"{b['line']} · {pct(b.get('over_l10',0), b.get('n_l10',0))}")
        P.append(f"| {p['player']} | {p['team']} | {p['gp']} | {p['min_l5']} | " + " | ".join(cells) + " |")
    P += ["", "Full per-market detail (all 11 player markets, L5/L10/L20/season, streaks, flags) is in "
          "`data/nba/nba_hit_rates.json`; team markets in `data/nba/nba_team_stats.json`."]
    return "\n".join(P) + "\n"


def push_gist(md):
    if not TOKEN:
        print("No GIST_TOKEN - local only")
        return
    req = urllib.request.Request(
        "https://api.github.com/gists/" + GIST,
        data=json.dumps({"files": {os.path.basename(REPORT_MD): {"content": md}}}).encode(),
        method="PATCH",
        headers={"Authorization": "token " + TOKEN, "User-Agent": "signal",
                 "Accept": "application/vnd.github+json"})
    urllib.request.urlopen(req, timeout=60).read()
    print("Pushed", os.path.basename(REPORT_MD), "to gist", GIST)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", default=None)
    ap.add_argument("--to", dest="end", default=None)
    ap.add_argument("--rates-only", action="store_true")
    ap.add_argument("--rebuild", action="store_true", help="discard stored game logs and re-pull every date")
    ap.add_argument("--no-gist", action="store_true")
    ap.add_argument("--backfill-lines", action="store_true", help="fetch closing total/spread for stored games missing them")
    ap.add_argument("--no-lines", action="store_true", help="skip capturing today's posted lines")
    a = ap.parse_args()
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    start = datetime.date.fromisoformat(a.start) if a.start else SEASON_START
    end = datetime.date.fromisoformat(a.end) if a.end else yesterday

    if a.rebuild:
        for f in (TEAM_LOG, PLAYER_LOG, os.path.join(DATA, "ingested_days.json")):
            if os.path.exists(f):
                os.remove(f)
        print("rebuild: cleared stored game logs; re-pulling from", start)
    if a.rates_only:
        team_log, player_log = load(TEAM_LOG, {}), load(PLAYER_LOG, {})
    else:
        team_log, player_log, n = ingest(start, end)
        print("ingested", n, "new games;", len(player_log), "total")
    if a.backfill_lines:
        backfill_lines(team_log)
    today = datetime.date.today()
    games = [] if (a.rates_only or a.no_lines) else slate(today)
    if games:
        capture_today_lines(today, games)
    acc = walk_forward_accuracy(team_log)
    save(os.path.join(DATA, "accuracy.json"), acc)
    if games:
        save(os.path.join(DATA, "projections.json"),
             {"generated": STAMP, "date": today.isoformat(), "margin_sd": acc["margin_sd"],
              "games": project_slate(team_log, games, today, acc)})
    print("accuracy:", acc["games_scored"], "games scored; model MAE", acc["mae"]["signal_model"],
          "| old own-median", acc["mae"]["own_median"], "| book", acc["mae"]["book_close"])
    players, teams = compute(team_log, player_log)
    days = load(os.path.join(DATA, "ingested_days.json"), [])
    save(RATES_JSON, {"generated": STAMP, "through": days[-1] if days else None,
                      "min_minutes": MIN_MINUTES, "players": players})
    save(TEAM_JSON, {"generated": STAMP, "through": days[-1] if days else None, "teams": teams})
    md = report(players, teams, days)
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print("Built", REPORT_MD, len(md), "bytes;", len(players), "players,", len(teams), "teams")
    if not a.no_gist:
        push_gist(md)


if __name__ == "__main__":
    main()
