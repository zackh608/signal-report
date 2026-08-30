#!/usr/bin/env python3
"""
build_signal.py — builds mlb_team_profiles.md for MLB, NBA and WNBA
and pushes it to a gist. Runs on GitHub Actions. No AI needed.

Each league is fetched independently. If one fails or is out of season,
the others still publish and the dashboard simply shows that tab as empty.

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


def pct(n, d):
    return f"{n}/{d} ({(100.0 * n / d if d else 0):.1f}%)"


# ══════════════════════════════════════════════════════════ MLB
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
    """(away, home, away_score, home_score, time_str, final?)"""
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


# ══════════════════════════════════════════════════════ NBA / WNBA
# ESPN public JSON. stats.nba.com hangs on cloud IPs; ESPN does not.
ESPN_PATH = {"NBA": "basketball/nba", "WNBA": "basketball/wnba"}


def _stat(entry, *names):
    """Pull the first matching stat value from an ESPN standings entry."""
    for s in entry.get("stats", []):
        if s.get("name") in names or s.get("abbreviation") in names:
            v = s.get("value")
            if v is None:
                v = s.get("displayValue")
            return v
    return None


def nba_standings(league, season):
    season = str(datetime.date.today().year)   # ESPN uses a plain year for both
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
            if pf is not None and gp and float(pf) < 200:
                pf = float(pf) * gp
            if pa is not None and gp and float(pa) < 200:
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


def nba_scoreboard(league, date):
    path = ESPN_PATH[league]
    url = (f"https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard"
           f"?dates={date:%Y%m%d}")
    d = get(url, timeout=25)
    out = []
    for ev in d.get("events", []):
        for comp in ev.get("competitions", []):
            home = away = None
            for c in comp.get("competitors", []):
                nm = c.get("team", {}).get("displayName", "")
                sc = int(c.get("score") or 0)
                if c.get("homeAway") == "home":
                    home = (nm, sc)
                else:
                    away = (nm, sc)
            if not home or not away:
                continue
            status = comp.get("status", {}).get("type", {})
            final = bool(status.get("completed"))
            label = status.get("shortDetail") or status.get("detail") or "TBD"
            out.append((away[0], home[0], away[1], home[1], label, final))
    return out


def nba_fetch(league, today, yest):
    season = str(today.year)
    return {
        "recs": nba_standings(league, season),
        "done": nba_scoreboard(league, yest),
        "slate": nba_scoreboard(league, today),
        "history": [],
    }


# ══════════════════════════════════════════ comeback tally (MLB only)
def comeback_tally(games):
    Z = lambda: {"t6": 0, "t6p": 0, "t6w": 0, "t7": 0, "t7p": 0, "t7w": 0,
                 "l6": 0, "l6p": 0, "l6l": 0, "l7": 0, "l7p": 0, "l7l": 0}
    S = collections.defaultdict(Z)
    for g in games:
        if g.get("status", {}).get("abstractGameState") != "Final":
            continue
        innings = (g.get("linescore") or {}).get("innings") or []
        if len(innings) < 7:
            continue
        home = g["teams"]["home"]["team"]["name"]
        away = g["teams"]["away"]["team"]["name"]
        h = a = 0
        cum = []
        for inn in innings:
            h += (inn.get("home") or {}).get("runs", 0) or 0
            a += (inn.get("away") or {}).get("runs", 0) or 0
            cum.append((a, h))
        fa, fh = cum[-1]
        for cp, tk, pk, wk, lk, lpk, llk in (
            (6, "t6", "t6p", "t6w", "l6", "l6p", "l6l"),
            (7, "t7", "t7p", "t7w", "l7", "l7p", "l7l"),
        ):
            if len(cum) < cp:
                continue
            ca, ch = cum[cp - 1]
            if ca == ch:
                continue
            trail, lead = (away, home) if ca < ch else (home, away)
            pressure = any(((xh - xa) if trail == away else (xa - xh)) <= 1
                           for xa, xh in cum[cp:])
            S[trail][tk] += 1
            S[lead][lk] += 1
            if pressure:
                S[trail][pk] += 1
                S[lead][lpk] += 1
            if (fa > fh and trail == away) or (fh > fa and trail == home):
                S[trail][wk] += 1
                S[lead][llk] += 1
    return S


# ══════════════════════════════════════════════════════ report writing
def league_block(lg, data, tally):
    """Returns the '### LEAGUE' body for Team Strengths and Weaknesses."""
    recs = data["recs"]
    L = []
    w = L.append

    def rec(n): return f"{recs[n]['w']}-{recs[n]['l']}" if n in recs else "-"
    def wpct(n): return recs[n]["w"] / recs[n]["gp"] if recs.get(n, {}).get("gp") else 0
    def streak(n): return recs.get(n, {}).get("streak", "-")
    def ppg(n):
        r = recs.get(n) or {}
        return (r.get("pf", 0) / r["gp"]) if r.get("gp") else 0
    def papg(n):
        r = recs.get(n) or {}
        return (r.get("pa", 0) / r["gp"]) if r.get("gp") else 0

    teams = sorted(recs, key=wpct, reverse=True)
    w("Team trend radar:")
    for t in [x for x in teams if str(streak(x)).startswith("W")][:5]:
        w(f"- Hot: {t} ({rec(t)}), streak {streak(t)}")
    for t in [x for x in teams if str(streak(x)).startswith("L")][-5:]:
        w(f"- Cold: {t} ({rec(t)}), streak {streak(t)}")
    w("")

    def table(label, order, valfn):
        w(f"Top {label}:")
        w("| Team | Record | Streak | Value |")
        w("| --- | --- | --- | --- |")
        for t in order[:8]:
            w(f"| {t} | {rec(t)} | {streak(t)} | {valfn(t)} |")
        w("")

    unit = "Runs" if lg == "MLB" else "Points"
    table("Win Percentage", teams, lambda t: f"{wpct(t):.3f}")
    table(f"{unit} per Game", sorted(recs, key=ppg, reverse=True), lambda t: f"{ppg(t):.2f}")
    table(f"{unit} Allowed per Game", sorted(recs, key=papg), lambda t: f"{papg(t):.2f}")
    table("Point Differential", sorted(recs, key=lambda t: ppg(t) - papg(t), reverse=True),
          lambda t: f"{ppg(t)-papg(t):+.2f}")

    w("Top profiles to scan first:")
    for t in teams[:6] + teams[-4:]:
        st, wk = [], []
        if wpct(t) >= .560: st.append("Winning profile - top group")
        if wpct(t) <= .440: wk.append("Losing profile - bottom group")
        if ppg(t) - papg(t) >= 0.5: st.append(f"Outscores opponents by {ppg(t)-papg(t):.2f}/game")
        if ppg(t) - papg(t) <= -0.5: wk.append(f"Outscored by {abs(ppg(t)-papg(t)):.2f}/game")
        s = tally.get(t) if lg == "MLB" else None
        if s and s["t6"] >= 15 and s["t6p"] / s["t6"] >= .30:
            st.append(f"Comes back - {100*s['t6p']/s['t6']:.0f}% pressure trailing after 6")
        if s and s["l6"] >= 15 and s["l6p"] / s["l6"] >= .30:
            wk.append(f"Leaks leads - {100*s['l6p']/s['l6']:.0f}% pressure allowed after 6")
        w(f"- **{t}** ({rec(t)}, streak {streak(t)}): "
          f"Strengths: {'; '.join(st) if st else 'No ranked strengths flagged'}. "
          f"Weaknesses: {'; '.join(wk) if wk else 'No ranked weaknesses flagged'}")
    w("")
    return "\n".join(L)


def build():
    today = datetime.date.today()
    yest = today - datetime.timedelta(days=1)
    stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

    leagues = {}
    errors = []
    for lg, fn in (("MLB", lambda: mlb_fetch(today, yest)),
                   ("NBA", lambda: nba_fetch("NBA", today, yest)),
                   ("WNBA", lambda: nba_fetch("WNBA", today, yest))):
        try:
            d = fn()
            if lg == "MLB":
                d["done_n"] = mlb_games_norm(d["done"])
                d["slate_n"] = mlb_games_norm(d["slate"])
            else:
                d["done_n"] = d["done"]
                d["slate_n"] = d["slate"]
            if not d["recs"]:
                errors.append(f"{lg}: no standings returned (out of season?)")
                continue
            leagues[lg] = d
            print(f"{lg}: {len(d['recs'])} teams, {len(d['slate_n'])} today, {len(d['done_n'])} yesterday")
        except Exception as e:
            errors.append(f"{lg}: {type(e).__name__}: {e}")
            print(f"{lg} FAILED: {e}")
            traceback.print_exc()

    if not leagues:
        raise SystemExit("No league data fetched. " + " | ".join(errors))

    tally = comeback_tally(leagues["MLB"]["history"]) if "MLB" in leagues else {}

    # ---------- prediction ----------
    P = []
    w = P.append
    w("# SIGNAL Team Report")
    w("")
    w(f"Generated: `{stamp}`")
    if errors:
        w("")
        for e in errors:
            w(f"> Not included - {e}")
    w("")
    w("## At a Glance")
    w("")
    w("| League | Teams | Today | Yesterday | Best record | Hottest |")
    w("| --- | --- | --- | --- | --- | --- |")
    for lg, d in leagues.items():
        recs = d["recs"]
        teams = sorted(recs, key=lambda n: recs[n]["w"] / recs[n]["gp"] if recs[n]["gp"] else 0,
                       reverse=True)
        hot = [t for t in teams if str(recs[t].get("streak", "")).startswith("W")]
        best = teams[0] if teams else "-"
        w(f"| {lg} | {len(recs)} | {len(d['slate_n'])} scheduled | {len(d['done_n'])} final | "
          f"{best} ({recs[best]['w']}-{recs[best]['l']}) | {hot[0] if hot else '-'} |")
    w("")
    w("## Scores and Slate")
    w("")
    for lg, d in leagues.items():
        w(f"### {lg} yesterday")
        w("")
        if not d["done_n"]:
            w("- No games")
        for an, hn, a_s, h_s, tm, final in d["done_n"]:
            win = an if a_s > h_s else hn
            w(f"- {an} {a_s} at {hn} {h_s} - {win} win")
        w("")
        w(f"### {lg} today")
        w("")
        if not d["slate_n"]:
            w("- No games")
        for an, hn, a_s, h_s, tm, final in d["slate_n"]:
            r = d["recs"]
            ar = f"{r[an]['w']}-{r[an]['l']}" if an in r else "-"
            hr = f"{r[hn]['w']}-{r[hn]['l']}" if hn in r else "-"
            w(f"- {an} ({ar}) at {hn} ({hr}) - {tm}")
        w("")
    w("## Team Strengths and Weaknesses")
    w("")
    for lg, d in leagues.items():
        w(f"### {lg}")
        w("")
        w(league_block(lg, d, tally))
    w("## Notes")
    w("")
    w("Standings and per-game rates are season-to-date. Comeback metrics are MLB only.")

    # ---------- comeback ----------
    C = ["# Late Comeback and Cash-Out Pressure Tally", "", f"Generated: `{stamp}`", ""]
    if tally:
        finals = sum(1 for g in leagues["MLB"]["history"]
                     if g.get("status", {}).get("abstractGameState") == "Final")
        C += [f"Window: `{MLB_SEASON_START}` through `{yest}`",
              f"Completed games parsed: `{finals}`", ""]
        for cp, tk, pk, wk_ in ((6, "t6", "t6p", "t6w"), (7, "t7", "t7p", "t7w")):
            C += [f"## Late-Game Pressure After {cp}", "",
                  "| Team | Opps | Pressure rate | Comeback wins | Big pressure |",
                  "| --- | --- | --- | --- | --- |"]
            for t in sorted(tally, key=lambda x: -(tally[x][pk] / tally[x][tk] if tally[x][tk] else 0)):
                s = tally[t]
                if s[tk]:
                    C.append(f"| {t} | {s[tk]} | {pct(s[pk], s[tk])} | {pct(s[wk_], s[tk])} | {pct(0, s[tk])} |")
            C.append("")
        for cp, lk, lpk, llk in ((6, "l6", "l6p", "l6l"), (7, "l7", "l7p", "l7l")):
            C += [f"## Fade These Teams When They Lead After {cp}", "",
                  "| Team | Lead opps | Pressure allowed | Lead erased | 1-run escapes | Final losses |",
                  "| --- | --- |
