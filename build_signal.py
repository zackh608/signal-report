#!/usr/bin/env python3
"""
build_signal.py - builds mlb_team_profiles.md for MLB, NBA and WNBA
and pushes it to a gist. Runs on GitHub Actions. No AI needed.

Each league is fetched independently. If one fails or is out of season,
the others still publish and the dashboard shows that tab as empty.

Env:
  GIST_TOKEN   GitHub PAT with "gist" scope
  GIST_ID      target gist
"""

import os, json, datetime, urllib.request, urllib.error, collections, traceback

GIST_ID = os.environ.get("GIST_ID", "a7ebd591bd69d8a1bd777a60ab7ce089")
TOKEN = os.environ.get("GIST_TOKEN")
FILENAME = "mlb_team_profiles.md"

MLB_API = "https://statsapi.mlb.com/api/v1"
MLB_SEASON_START = "2026-03-25"


def get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "signal-report"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def sep(n):
    """Markdown table separator, built rather than written literally."""
    return "|" + (" --- |" * n)


def pct(n, d):
    return f"{n}/{d} ({(100.0 * n / d if d else 0):.1f}%)"


# ==================== MLB ====================
def mlb_schedule(start, end, hydrate=None):
    url = f"{MLB_API}/schedule?sportId=1&startDate={start}&endDate={end}"
    if hydrate:
        url += f"&hydrate={hydrate}"
    out = []
    for day in get(url).get("dates", []):
        for g in day.get("games", []):
            g["_date"] = day["date"]
            out.append(g)
    return out


def mlb_standings(season):
    recs = {}
    for lg in (103, 104):
        d = get(f"{MLB_API}/standings?leagueId={lg}&season={season}&standingsTypes=regularSeason")
        for div in d.get("records", []):
            for t in div.get("teamRecords", []):
                recs[t["team"]["name"]] = {
                    "w": t["wins"], "l": t["losses"],
                    "streak": (t.get("streak") or {}).get("streakCode", "-"),
                    "pf": t.get("runsScored", 0), "pa": t.get("runsAllowed", 0),
                    "gp": t["wins"] + t["losses"],
                }
    return recs


def mlb_fetch(today, yest):
    return {
        "recs": mlb_standings(today.year),
        "done": mlb_schedule(yest.isoformat(), yest.isoformat()),
        "slate": mlb_schedule(today.isoformat(), today.isoformat()),
        "history": mlb_schedule(MLB_SEASON_START, yest.isoformat(), hydrate="linescore"),
    }


def mlb_games_norm(games):
    out = []
    for g in games:
        t = g["teams"]
        an, hn = t["away"]["team"]["name"], t["home"]["team"]["name"]
        final = g.get("status", {}).get("abstractGameState") == "Final"
        try:
            tm = datetime.datetime.fromisoformat(
                g["gameDate"].replace("Z", "+00:00")).astimezone().strftime("%-I:%M %p")
        except Exception:
            tm = "TBD"
        out.append((an, hn, t["away"].get("score", 0), t["home"].get("score", 0), tm, final))
    return out


# ==================== NBA / WNBA ====================
# ESPN public JSON. stats.nba.com hangs on cloud IPs; ESPN does not.
ESPN_PATH = {"NBA": "basketball/nba", "WNBA": "basketball/wnba"}


def _stat(entry, *names):
    for s in entry.get("stats", []):
        if s.get("name") in names or s.get("abbreviation") in names:
            v = s.get("value")
            if v is None:
                v = s.get("displayValue")
            return v
    return None


def nba_standings(league, season):
    season = str(datetime.date.today().year)
    path = ESPN_PATH[league]
    url = (f"https://site.api.espn.com/apis/v2/sports/{path}/standings"
           f"?season={season}&level=3")
    d = get(url, timeout=25)
    recs = {}

    def walk(node):
        for e in (node.get("standings") or {}).get("entries", []):
            name = e.get("team", {}).get("displayName")
            if not name:
                continue
            w = _stat(e, "wins") or 0
            l = _stat(e, "losses") or 0
            gp = int(w) + int(l)
            pf = _stat(e, "pointsFor", "avgPointsFor")
            pa = _stat(e, "pointsAgainst", "avgPointsAgainst")
            # ESPN sometimes gives per-game averages instead of totals
            if pf is not None and gp and 200 > float(pf):
                pf = float(pf) * gp
            if pa is not None and gp and 200 > float(pa):
                pa = float(pa) * gp
            st = _stat(e, "streak")
            if isinstance(st, (int, float)):
                st = ("W" if st > 0 else "L") + str(abs(int(st)))
            recs[name] = {"w": int(w), "l": int(l), "gp": gp,
                          "streak": st or "-",
                          "pf": float(pf or 0), "pa": float(pa or 0)}
        for child in node.get("children", []):
            walk(child)

    walk(d)
    return recs
