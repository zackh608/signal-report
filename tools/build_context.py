"""Writes compact summaries of SIGNAL's NBA data to context/ for Claude project sessions (run from repo root).
Raw game logs are ~5 MB; these files are ~70 KB and carry what a pick session needs. Runs in the daily workflow."""
import csv, json, os

D, O = "data/nba/", "context/"
os.makedirs(O, exist_ok=True)
T = json.load(open(D + "nba_team_stats.json"))["teams"]
H = json.load(open(D + "nba_hit_rates.json"))["players"]
A = json.load(open(D + "accuracy.json"))
thru = json.load(open(D + "ingested_days.json"))[-1]

KEY = ["pts", "rating", "pace", "efg_pct", "fg3m", "fg3a", "fg3_pct", "fta", "ft_rate", "reb", "oreb", "oreb_pct", "dreb",
       "ast", "tov", "tov_pct", "stl", "blk", "pitp", "fb", "q1", "h1", "h2"]
with open(O + "team_board.csv", "w", newline="") as f:
    w = csv.writer(f)
    hdr = ["team", "W", "L", "ATS_W", "ATS_L", "ATS_P", "ATS_avg_cover", "ATS_home", "ATS_away", "ATS_fav", "ATS_dog",
           "ATS_streak", "OU_over", "OU_under", "total_vs_line"]
    for k in KEY:
        hdr += [f"{k}_for", f"{k}_for_rank", f"{k}_against", f"{k}_against_rank"]
    w.writerow(hdr)
    for t in sorted(T, key=lambda t: t["team"]):
        c = (t.get("book") or {}).get("COVER") or {}
        o = (t.get("book") or {}).get("TOTALS") or {}
        S = t.get("stats") or {}
        wl = lambda x: f"{x['w']}-{x['l']}" if x else ""
        row = [t["team"], t["records"]["overall"]["w"], t["records"]["overall"]["l"], c.get("cover_season"),
               (c["n_season"] - c["cover_season"] - c["push_season"]) if c else "", c.get("push_season"), c.get("avg_margin"),
               wl(c.get("home")), wl(c.get("away")), wl(c.get("favorite")), wl(c.get("underdog")), c.get("streak"),
               o.get("over"), o.get("under"), o.get("avg_vs_line")]
        for k in KEY:
            s = S.get(k, {})
            row += [s.get("for"), s.get("for_rank"), s.get("against"), s.get("against_rank")]
        w.writerow(row)

MK = ["PTS", "REB", "AST", "3PM", "PRA", "PR", "PA", "RA", "STL", "BLK", "TOV"]
with open(O + "player_baselines.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["player", "team", "pos", "games_15min", "min_season", "min_last5", "starts_last5", "last_game"]
               + [f"{m}_avg" for m in MK] + [f"{m}_sd" for m in MK])
    for p in sorted(H, key=lambda p: (p["team"], -(p.get("min_season") or 0))):
        if p["eligible_gp"] < 3:
            continue
        m = p["markets"]
        w.writerow([p["player"], p["team"], p.get("pos", ""), p["eligible_gp"], p.get("min_season"), p.get("min_l5"),
                    p.get("starts_l5"), p.get("last_game")] + [m.get(k, {}).get("proj") for k in MK]
                   + [m.get(k, {}).get("proj_sd") for k in MK])

mae, vb = A["mae"], A["vs_book"]
ce, me = A.get("context_effects", {}), A.get("matchup_effects", {})
lines = [f"# SIGNAL model accuracy (data through {thru}, {A['games_scored']} games scored walk-forward)", "",
         "| Method | Total miss | Margin miss | Team pts miss | Winner % |", "|---|---|---|---|---|"]
for k, name in (("signal_model", "SIGNAL model"), ("book_close", "Book closing line"), ("league_avg", "League average"),
                ("own_median", "Old own-median line")):
    lines.append(f"| {name} | {mae[k]['total']} | {mae[k]['margin']} | {mae[k]['team_pts']} | {A['winner_pct'].get(k, '-')} |")
lines += ["", f"SIGNAL vs the book when they disagree by 3+: totals {vb['ou_record_when_3pt_disagreement'][0]}-"
          f"{vb['ou_record_when_3pt_disagreement'][1]}, spreads {vb['ats_record_when_3pt_disagreement'][0]}-"
          f"{vb['ats_record_when_3pt_disagreement'][1]}.", "", "## Situations that move player output (% vs own average)"]
for k, v in ce.items():
    used = {g: e for g, e in v.items() if e["used"]}
    if used:
        lines.append(f"- **{k}**: " + ", ".join(f"{g} {e['effect_pct']:+}% (n={e['n']})" for g, e in used.items()))
lines += ["", "## Matchup signals that tested real"]
for mk, d in me.items():
    used = [s for s, e in d.items() if e["used"]]
    if used:
        lines.append(f"- {mk}: " + ", ".join(used))
lines += ["", "Grade bands: A+ 70%, A 65%, B 60%, C 55%, D 52%, F below. Break-even at -110 is 52.4%."]
open(O + "model_accuracy.md", "w").write("\n".join(lines) + "\n")

for f in ("projections.json", "grades.json"):
    if os.path.exists(D + f):
        d = json.load(open(D + f))
        open(O + "today.txt", "a" if f == "grades.json" else "w").write(
            f"{f}: slate date {d.get('date')}, generated {d.get('generated')}\n")
print(f"context: team_board, player_baselines, model_accuracy written (data through {thru})")
