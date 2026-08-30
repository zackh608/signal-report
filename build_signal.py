#!/usr/bin/env python3
"""Builds mlb_team_profiles.md for MLB/NBA/WNBA and pushes it to a gist."""
import os, json, datetime, urllib.request, collections, traceback

GIST = os.environ.get("GIST_ID", "a7ebd591bd69d8a1bd777a60ab7ce089")
TOKEN = os.environ.get("GIST_TOKEN")
FILE = "mlb_team_profiles.md"
MLB = "https://statsapi.mlb.com/api/v1"
START = "2026-03-25"
ESPN = {"NBA": "basketball/nba", "WNBA": "basketball/wnba"}
TODAY = datetime.date.today()
YEST = TODAY - datetime.timedelta(days=1)
STAMP = datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def get(url, timeout=30):
    r = urllib.request.Request(url, headers={"User-Agent": "signal"})
    with urllib.request.urlopen(r, timeout=timeout) as f:
        return json.loads(f.read().decode())


def sep(n):
    return "|" + (" --- |" * n)


def mlb_games(start, end, hydrate=""):
    u = f"{MLB}/schedule?sportId=1&startDate={start}&endDate={end}"
    if hydrate:
        u += "&hydrate=" + hydrate
    return [g for d in get(u).get("dates", []) for g in d.get("games", [])]


def norm_mlb(games):
    out = []
    for g in games:
        t = g["teams"]
        try:
            tm = datetime.datetime.fromisoformat(
                g["gameDate"].replace("Z", "+00:00")).astimezone().strftime("%I:%M %p")
        except Exception:
            tm = "TBD"
        out.append((t["away"]["team"]["name"], t["home"]["team"]["name"],
                    t["away"].get("score", 0), t["home"].get("score", 0), tm))
    return out


def fetch_mlb():
    recs = {}
    for lg in (103, 104):
        for div in get(f"{MLB}/standings?leagueId={lg}&season={TODAY.year}"
                       "&standingsTypes=regularSeason").get("records", []):
            for t in div.get("teamRecords", []):
                w, l = t["wins"], t["losses"]
                recs[t["team"]["name"]] = {
                    "w": w, "l": l, "gp": w + l,
                    "streak": (t.get("streak") or {}).get("streakCode", "-"),
                    "pf": t.get("runsScored", 0), "pa": t.get("runsAllowed", 0)}
    return {"recs": recs,
            "done": norm_mlb(mlb_games(YEST, YEST)),
            "slate": norm_mlb(mlb_games(TODAY, TODAY)),
            "hist": mlb_games(START, YEST, "linescore")}


def stat(e, *names):
    for s in e.get("stats", []):
        if s.get("name") in names:
            return s.get("value")
    return None


def fetch_espn(league):
    recs = {}

    def walk(n):
        for e in (n.get("standings") or {}).get("entries", []):
            nm = e.get("team", {}).get("displayName")
            if not nm:
                continue
            w, l = int(stat(e, "wins") or 0), int(stat(e, "losses") or 0)
            gp = w + l
            pf, pa = stat(e, "pointsFor"), stat(e, "pointsAgainst")
            if pf and gp and 200 > float(pf):
                pf = float(pf) * gp
            if pa and gp and 200 > float(pa):
                pa = float(pa) * gp
            st = stat(e, "streak")
            if isinstance(st, (int, float)):
                st = ("W" if st > 0 else "L") + str(abs(int(st)))
            recs[nm] = {"w": w, "l": l, "gp": gp, "streak": st or "-",
                        "pf": float(pf or 0), "pa": float(pa or 0)}
        for c in n.get("children", []):
            walk(c)

        walk(get(f"https://site.web.api.espn.com/apis/v2/sports/{ESPN[league]}"
             f"/standings?region=us&lang=en&contentorigin=espn"
             f"&season={TODAY.year}&type=0&level=1", 25))

    def board(day):
        u = (f"https://site.api.espn.com/apis/site/v2/sports/{ESPN[league]}"
             f"/scoreboard?dates={day:%Y%m%d}")
        out = []
        for ev in get(u, 25).get("events", []):
            for c in ev.get("competitions", []):
                s = {x.get("homeAway"): (x.get("team", {}).get("displayName", ""),
                                         int(x.get("score") or 0))
                     for x in c.get("competitors", [])}
                if "home" in s and "away" in s:
                    lbl = c.get("status", {}).get("type", {}).get("shortDetail", "TBD")
                    out.append((s["away"][0], s["home"][0], s["away"][1], s["home"][1], lbl))
        return out

    return {"recs": recs, "done": board(YEST), "slate": board(TODAY), "hist": []}


def tally_comebacks(games):
    Z = lambda: {"t6": 0, "p6": 0, "w6": 0, "t7": 0, "p7": 0, "w7": 0}
    S = collections.defaultdict(Z)
    for g in games:
        if g.get("status", {}).get("abstractGameState") != "Final":
            continue
        inn = (g.get("linescore") or {}).get("innings") or []
        if len(inn) < 7:
            continue
        home = g["teams"]["home"]["team"]["name"]
        away = g["teams"]["away"]["team"]["name"]
        a = h = 0
        cum = []
        for i in inn:
            a += (i.get("away") or {}).get("runs", 0) or 0
            h += (i.get("home") or {}).get("runs", 0) or 0
            cum.append((a, h))
        fa, fh = cum[-1]
        for cp, tk, pk, wk in ((6, "t6", "p6", "w6"), (7, "t7", "p7", "w7")):
            if len(cum) < cp:
                continue
            ca, ch = cum[cp - 1]
            if ca == ch:
                continue
            trail = away if ca < ch else home
            S[trail][tk] += 1
            if any(((y - x) if trail == away else (x - y)) <= 1 for x, y in cum[cp:]):
                S[trail][pk] += 1
            if (fa > fh and trail == away) or (fh > fa and trail == home):
                S[trail][wk] += 1
    return S


def build():
    data, errs = {}, []
    for lg, fn in (("MLB", fetch_mlb), ("NBA", lambda: fetch_espn("NBA")),
                   ("WNBA", lambda: fetch_espn("WNBA"))):
        try:
            d = fn()
            if d["recs"]:
                data[lg] = d
                print(lg, len(d["recs"]), "teams,", len(d["slate"]), "today")
            else:
                errs.append(lg + ": no standings (out of season?)")
        except Exception as e:
            errs.append(f"{lg}: {type(e).__name__}: {e}")
            print(lg, "FAILED:", e)
            traceback.print_exc()
    if not data:
        raise SystemExit("nothing fetched: " + " | ".join(errs))

    cb = tally_comebacks(data["MLB"]["hist"]) if "MLB" in data else {}
    P = ["# SIGNAL Team Report", "", f"Generated: `{STAMP}`", ""]
    for e in errs:
        P.append("> Not included - " + e)
    P += ["", "## At a Glance", "",
          "| League | Teams | Today | Yesterday | Best record | Hottest |", sep(6)]
    order = {}
    for lg, d in data.items():
        r = d["recs"]
        order[lg] = sorted(r, key=lambda n: r[n]["w"] / (r[n]["gp"] or 1), reverse=True)
        hot = [t for t in order[lg] if str(r[t]["streak"]).startswith("W")]
        b = order[lg][0]
        P.append(f"| {lg} | {len(r)} | {len(d['slate'])} scheduled | {len(d['done'])} final "
                 f"| {b} ({r[b]['w']}-{r[b]['l']}) | {hot[0] if hot else '-'} |")
    P += ["", "## Scores and Slate", ""]
    for lg, d in data.items():
        P += [f"### {lg} yesterday", ""]
        P += [f"- {a} {x} at {h} {y} - {a if x > y else h} win"
              for a, h, x, y, _ in d["done"]] or ["- No games"]
        P += ["", f"### {lg} today", ""]
        r = d["recs"]
        P += [f"- {a} ({r[a]['w']}-{r[a]['l']}) at {h} ({r[h]['w']}-{r[h]['l']}) - {t}"
              for a, h, _, _, t in d["slate"] if a in r and h in r] or ["- No games"]
        P.append("")
    P += ["## Team Strengths and Weaknesses", ""]
    for lg, d in data.items():
        r = d["recs"]
        ts = order[lg]
        pg = lambda n, k: r[n][k] / (r[n]["gp"] or 1)
        P += [f"### {lg}", "", "Team trend radar:"]
        P += [f"- Hot: {t} ({r[t]['w']}-{r[t]['l']}), streak {r[t]['streak']}"
              for t in ts if str(r[t]["streak"]).startswith("W")][:5]
        P += [f"- Cold: {t} ({r[t]['w']}-{r[t]['l']}), streak {r[t]['streak']}"
              for t in ts if str(r[t]["streak"]).startswith("L")][:5]
        P.append("")
        unit = "Runs" if lg == "MLB" else "Points"
        for label, key, rev in (("Win Percentage", None, True),
                                (unit + " per Game", "pf", True),
                                (unit + " Allowed per Game", "pa", False)):
            if key:
                seq = sorted(r, key=lambda n: pg(n, key), reverse=rev)
                val = lambda n: f"{pg(n, key):.2f}"
            else:
                seq, val = ts, lambda n: f"{r[n]['w']/(r[n]['gp'] or 1):.3f}"
            P += [f"Top {label}:", "| Team | Record | Streak | Value |", sep(4)]
            P += [f"| {t} | {r[t]['w']}-{r[t]['l']} | {r[t]['streak']} | {val(t)} |"
                  for t in seq[:8]]
            P.append("")
        P.append("Top profiles to scan first:")
        for t in ts[:6] + ts[-4:]:
            s, k = [], []
            wp = r[t]["w"] / (r[t]["gp"] or 1)
            if wp >= .56:
                s.append("Winning profile - top group")
            if wp <= .44:
                k.append("Losing profile - bottom group")
            diff = pg(t, "pf") - pg(t, "pa")
            (s if diff >= 0 else k).append(f"Scoring margin {diff:+.2f} per game")
            c = cb.get(t)
            if c and c["t6"] >= 15:
                pctv = 100 * c["p6"] / c["t6"]
                (s if pctv >= 30 else k).append(
                    f"Pressure trailing after 6: {pctv:.0f}%")
            P.append(f"- **{t}** ({r[t]['w']}-{r[t]['l']}, streak {r[t]['streak']}): "
                     f"Strengths: {'; '.join(s) or 'None flagged'}. "
                     f"Weaknesses: {'; '.join(k) or 'None flagged'}")
        P.append("")
    P += ["## Notes", "", "Season-to-date figures. Comeback metrics are MLB only."]

    C = ["# Late Comeback and Cash-Out Pressure Tally", "", f"Generated: `{STAMP}`", ""]
    if cb:
        C += [f"Window: `{START}` through `{YEST}`", ""]
        for cp, tk, pk, wk in ((6, "t6", "p6", "w6"), (7, "t7", "p7", "w7")):
            C += [f"## Late-Game Pressure After {cp}", "",
                  "| Team | Opps | Pressure rate | Comeback wins | Big pressure |", sep(5)]
            for t in sorted(cb, key=lambda x: -cb[x][pk] / (cb[x][tk] or 1)):
                n = cb[t]
                if n[tk]:
                    C.append(f"| {t} | {n[tk]} | {n[pk]}/{n[tk]} ({100*n[pk]/n[tk]:.1f}%) "
                             f"| {n[wk]}/{n[tk]} ({100*n[wk]/n[tk]:.1f}%) | 0/{n[tk]} (0.0%) |")
            C.append("")
    C += ["## Late-Game Context Notes", "",
          "1. Rates describe games already played; small samples have wide error bars.",
          "2. Confirm starter, bullpen workload and lineup before drawing conclusions."]

    T = ["# Scoring Pace and Matchup Report", "", f"Generated: `{STAMP}`", "",
         "## Best Scoring Pace Context", ""]
    rows = []
    for lg, d in data.items():
        r = d["recs"]
        pg = lambda n, k: r[n][k] / (r[n]["gp"] or 1)
        for a, h, *_ in d["slate"]:
            if a in r and h in r:
                v = (pg(a, "pf") + pg(h, "pa") + pg(h, "pf") + pg(a, "pa")) / 2
                rows.append((v, a, h, lg, r))
    rows.sort(key=lambda x: -x[0])

    def lean(lg, v):
        hi, lo = (9.3, 8.0) if lg == "MLB" else (228, 218) if lg == "NBA" else (166, 156)
        return "lean over" if v >= hi else "lean under" if v <= lo else "no strong lean"

    for v, a, h, lg, r in rows[:5]:
        T.append(f"- **{a} @ {h}** ({lg}): {lean(lg, v)} | pressure {v:.1f}")
    T.append("")
    for v, a, h, lg, r in rows:
        pg = lambda n, k: r[n][k] / (r[n]["gp"] or 1)
        T += [f"## {a} @ {h} ({lg})", "", f"Venue: {h} home | Status: scheduled",
              f"Lean: **{lean(lg, v)}** | pressure score: `{v:.1f}`", ""]
        for n in (a, h):
            T.append(f"- {n}: {r[n]['w']}-{r[n]['l']}, streak {r[n]['streak']}, "
                     f"{pg(n,'pf'):.2f} for / {pg(n,'pa'):.2f} against")
        T.append("")

    return ("<!--SIGNAL:prediction-->\n" + "\n".join(P) +
            "\n\n<!--SIGNAL:comeback-->\n" + "\n".join(C) +
            "\n\n<!--SIGNAL:totals-->\n" + "\n".join(T) + "\n")


md = build()
open(FILE, "w").write(md)
print("Built", FILE, len(md), "bytes")
if TOKEN:
    req = urllib.request.Request(
        "https://api.github.com/gists/" + GIST,
        data=json.dumps({"files": {FILE: {"content": md}}}).encode(), method="PATCH",
        headers={"Authorization": "token " + TOKEN, "User-Agent": "signal",
                 "Accept": "application/vnd.github+json"})
    urllib.request.urlopen(req, timeout=60).read()
    print("Pushed to gist", GIST)
else:
    print("No GIST_TOKEN - local only")
