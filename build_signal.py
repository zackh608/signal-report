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

# stats.nba.com rejects plain requests; these headers are required.
NBA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}
NBA_LEAGUE_ID = {"NBA": "00", "WNBA": "10"}


def get(url, headers=None, timeout=60):
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
                    "streak": (t.get("streak") or {}).get("streakCode", "—"),
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
def nba_standings(league, season):
    """season like '2025-26' for NBA, '2026' for WNBA."""
    lid = NBA_LEAGUE_ID[league]
    url = (f"https://stats.nba.com/stats/leaguestandingsv3"
           f"?LeagueID={lid}&Season={season}&SeasonType=Regular%20Season")
    d = get(url, headers=NBA_HEADERS)
    rs = d["resultSets"][0]
    cols = rs["headers"]
    idx = {c: i for i, c in enumerate(cols)}
    recs = {}
    for row in rs["rowSet"]:
        name = f"{row[idx['TeamCity']]} {row[idx['TeamName']]}".strip()
        w, l = row[idx["WINS"]], row[idx["LOSSES"]]
        streak = row[idx["strCurrentStreak"]] if "strCurrentStreak" in idx else "—"
        streak = str(streak).replace(" ", "").replace("W", "W").replace("L", "L")
        recs[name] = {"w": w, "l": l, "streak": streak, "gp": w + l,
                      "pf": row[idx["PointsPG"]] * (w + l) if "PointsPG" in idx else 0,
                      "pa": row[idx["OppPointsPG"]] * (w + l) if "OppPointsPG" in idx else 0}
    return recs


def nba_scoreboard(league, date):
    lid = NBA_LEAGUE_ID[league]
    url = (f"https://stats.nba.com/stats/scoreboardv2"
           f"?GameDate={date:%m/%d/%Y}&LeagueID={lid}&DayOffset=0")
    d = get(url, headers=NBA_HEADERS)
    sets = {s["name"]: s for s in d["resultSets"]}
    hdr, ls = sets.get("GameHeader"), sets.get("LineScore")
    if not hdr:
        return []
    hi = {c: i for i, c in enumerate(hdr["headers"])}
    scores = {}
    if ls:
        li = {c: i for i, c in enumerate(ls["headers"])}
        for row in ls["rowSet"]:
            scores.setdefault(row[li["GAME_ID"]], {})[row[li["TEAM_ID"]]] = (
                f"{row[li['TEAM_CITY_NAME']]} {row[li['TEAM_NAME']]}".strip(),
                row[li["PTS"]] or 0)
    out = []
    for row in hdr["rowSet"]:
        gid = row[hi["GAME_ID"]]
        home_id, away_id = row[hi["HOME_TEAM_ID"]], row[hi["VISITOR_TEAM_ID"]]
        s = scores.get(gid, {})
        hn, hp = s.get(home_id, ("Home", 0))
        an, ap = s.get(away_id, ("Away", 0))
        status = str(row[hi["GAME_STATUS_TEXT"]]).strip()
        final = status.lower().startswith("final")
        out.append((an, hn, ap, hp, status, final))
    return out


def nba_fetch(league, today, yest):
    season = f"{today.year-1}-{str(today.year)[2:]}" if league == "NBA" else str(today.year)
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

    def rec(n): return f"{recs[n]['w']}-{recs[n]['l']}" if n in recs else "—"
    def wpct(n): return recs[n]["w"] / recs[n]["gp"] if recs.get(n, {}).get("gp") else 0
    def streak(n): return recs.get(n, {}).get("streak", "—")
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
        if wpct(t) >= .560: st.append("Winning profile — top group")
        if wpct(t) <= .440: wk.append("Losing profile — bottom group")
        if ppg(t) - papg(t) >= 0.5: st.append(f"Outscores opponents by {ppg(t)-papg(t):.2f}/game")
        if ppg(t) - papg(t) <= -0.5: wk.append(f"Outscored by {abs(ppg(t)-papg(t)):.2f}/game")
        s = tally.get(t) if lg == "MLB" else None
        if s and s["t6"] >= 15 and s["t6p"] / s["t6"] >= .30:
            st.append(f"Comes back — {100*s['t6p']/s['t6']:.0f}% pressure trailing after 6")
        if s and s["l6"] >= 15 and s["l6p"] / s["l6"] >= .30:
            wk.append(f"Leaks leads — {100*s['l6p']/s['l6']:.0f}% pressure allowed after 6")
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
            w(f"> Not included — {e}")
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
        best = teams[0] if teams else "—"
        w(f"| {lg} | {len(recs)} | {len(d['slate_n'])} scheduled | {len(d['done_n'])} final | "
          f"{best} ({recs[best]['w']}-{recs[best]['l']}) | {hot[0] if hot else '—'} |")
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
            w(f"- {an} {a_s} at {hn} {h_s} — {win} win")
        w("")
        w(f"### {lg} today")
        w("")
        if not d["slate_n"]:
            w("- No games")
        for an, hn, a_s, h_s, tm, final in d["slate_n"]:
            r = d["recs"]
            ar = f"{r[an]['w']}-{r[an]['l']}" if an in r else "—"
            hr = f"{r[hn]['w']}-{r[hn]['l']}" if hn in r else "—"
            w(f"- {an} ({ar}) at {hn} ({hr}) — {tm}")
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
                  "| --- | --- | --- | --- | --- | --- |"]
            for t in sorted(tally, key=lambda x: -(tally[x][lpk] / tally[x][lk] if tally[x][lk] else 0)):
                s = tally[t]
                if s[lk]:
                    C.append(f"| {t} | {s[lk]} | {pct(s[lpk], s[lk])} | {pct(s[llk], s[lk])} | "
                             f"{pct(s[lpk]-s[llk], s[lk])} | {pct(s[llk], s[lk])} |")
            C.append("")
    else:
        C.append("No MLB history available this run.")
    C += ["## Late-Game Context Notes", "",
          "1. Rates describe games already played. Small denominators carry wide error bars.",
          "2. Confirm starter, bullpen workload and lineup before drawing conclusions."]

    # ---------- totals ----------
    T = ["# Scoring Pace and Matchup Report", "", f"Generated: `{stamp}`", "",
         "## Best Scoring Pace Context", ""]
    paced = []
    for lg, d in leagues.items():
        recs = d["recs"]
        def pg(n, k):
            r = recs.get(n) or {}
            return (r.get(k, 0) / r["gp"]) if r.get("gp") else 0
        for an, hn, *_ in d["slate_n"]:
            if an not in recs or hn not in recs:
                continue
            exp = (pg(an, "pf") + pg(hn, "pa")) / 2 + (pg(hn, "pf") + pg(an, "pa")) / 2
            paced.append((exp, an, hn, lg, recs))
    paced.sort(reverse=True, key=lambda x: x[0])

    def lean_for(lg, exp):
        hi, lo = (9.3, 8.0) if lg == "MLB" else (228, 218) if lg == "NBA" else (166, 156)
        return "lean over" if exp >= hi else "lean under" if exp <= lo else "no strong lean"

    for exp, an, hn, lg, recs in paced[:5]:
        T.append(f"- **{an} @ {hn}** ({lg}): {lean_for(lg, exp)} | pressure {exp:.1f}")
    T.append("")
    for exp, an, hn, lg, recs in paced:
        def pg(n, k):
            r = recs.get(n) or {}
            return (r.get(k, 0) / r["gp"]) if r.get("gp") else 0
        T += [f"## {an} @ {hn} ({lg})", "",
              f"Venue: {hn} home | Status: scheduled",
              f"Lean: **{lean_for(lg, exp)}** | pressure score: `{exp:.1f}`", ""]
        for n in (an, hn):
            extra = ""
            s = tally.get(n) if lg == "MLB" else None
            if s and s["l6"]:
                extra = f", leaks leads {100*s['l6p']/s['l6']:.0f}% after 6"
            T.append(f"- {n}: {recs[n]['w']}-{recs[n]['l']}, streak {recs[n].get('streak','—')}, "
                     f"{pg(n,'pf'):.2f} for / {pg(n,'pa'):.2f} against{extra}")
        T.append("")

    return ("<!--SIGNAL:prediction-->\n" + "\n".join(P) +
            "\n\n<!--SIGNAL:comeback-->\n" + "\n".join(C) +
            "\n\n<!--SIGNAL:totals-->\n" + "\n".join(T) + "\n")


def push(content):
    body = json.dumps({"files": {FILENAME: {"content": content}}}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/gists/{GIST_ID}", data=body, method="PATCH",
        headers={"Authorization": "token " + TOKEN,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "signal-report"})
    with urllib.request.urlopen(req, timeout=60) as r:
        json.loads(r.read().decode())
    print(f"Pushed {len(content)} bytes to gist {GIST_ID}")


if __name__ == "__main__":
    md = build()
    with open(FILENAME, "w") as f:
        f.write(md)
    print(f"Built {FILENAME}: {len(md)} bytes")
    if TOKEN:
        push(md)
    else:
        print("No GIST_TOKEN — wrote file locally only.")
