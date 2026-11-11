"""Walk-forward backtest of SIGNAL player/team legs. Run from repo root: python tools/backtest.py
Answers: does an 80%% L10 rate vs the player's own median ever exist (no), does recent form (L5 avg vs L20 median,
in sd units) predict the next game (yes, ~59%% when |gap| >= 0.5 sd), and which total-projection method has the lowest error."""
import json, statistics, collections, sys, math
import os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import nba_tracker as T
pg=json.load(open('data/nba/player_games.json')); tg=json.load(open('data/nba/team_games.json'))
prow=[r for g in pg.values() for r in g]; trow=[r for g in tg.values() for r in g]
by_pl=collections.defaultdict(list)
for r in sorted(prow,key=lambda r:r['date']): by_pl[r['player_id']].append(r)
def synth(vals): s=vals[:20]; return T.half_round(statistics.median(s), statistics.fmean(s))
# Q1: against the player's own L20-median line, how often does the NEXT game go over? (should be ~50%)
# Q2: does recent form (L5 avg vs line, L10 median vs line) predict the next game's side?  bucket by form gap in sd units
rows=[]
for pid,R in by_pl.items():
    for i,t in enumerate(R):
        hist=[h for h in R[:i] if h['min']>=T.MIN_MINUTES][::-1]
        if len(hist)<6 or t["min"]<T.MIN_MINUTES: continue
        for mk,fn in T.PLAYER_MARKETS.items():
            vals=[fn(h) for h in hist]; line=synth(vals)
            if line<5: continue
            sd=statistics.pstdev(vals[:20]) or 1
            if len(vals)<6: continue
            gap5=(statistics.fmean(vals[:5])-line)/sd; gap10=(statistics.median(vals[:10])-line)/sd
            act=fn(t)
            if act==line: continue
            rows.append(dict(mk=mk,line=line,sd=sd,gap5=gap5,gap10=gap10,over=act>line,margin=abs(act-line)/sd,hi=(line>=15)))
print("player-games graded:",len(rows))
print("base over-rate vs own L20 median: %.1f%%"%(100*sum(r['over'] for r in rows)/len(rows)))
def tab(key,buckets,label):
    print("--",label)
    for lo,hi in buckets:
        S=[r for r in rows if lo<=r[key]<hi]
        if not S: continue
        ov=sum(r['over'] for r in S); print(f"   {lo:+.2f}..{hi:+.2f}  n={len(S):4d}  over {100*ov/len(S):5.1f}%  (follow-the-form hits {100*(ov if lo>=0 else len(S)-ov)/len(S):5.1f}%)")
B=[(-9,-1),(-1,-.5),(-.5,-.25),(-.25,.25),(.25,.5),(.5,1),(1,9)]
tab('gap5',B,"L5 average vs line, in sd units  (momentum test)")
tab('gap10',B,"L10 median vs line, in sd units")
print("-- by market: does following L5 form (gap5 beyond +/-0.5sd) work?")
for mk in T.PLAYER_MARKETS:
    S=[r for r in rows if r['mk']==mk and abs(r['gap5'])>=.5]
    if len(S)<15: continue
    hit=sum((r['over']==(r['gap5']>0)) for r in S); print(f"   {mk:4s} n={len(S):4d} follow-form {100*hit/len(S):5.1f}%   fade-form {100-100*hit/len(S):5.1f}%")
# how big is a typical miss?  if margin <= 1 unit, a book line one notch different flips it
m=[r for r in rows]; small=sum(abs(1)>=0 and (r['margin']*r['sd'])<=1 for r in m)
print(f"-- share of player-games landing within 1 unit of the line: {100*small/len(m):.1f}%")
# TEAM: naive median vs matchup-avg projection, MAE head to head
by_t=collections.defaultdict(list)
for r in sorted(trow,key=lambda r:r['date']): by_t[r['team']].append(r)
segs={'1Q':lambda r:(r['q1'],r['oq1']),'1H':lambda r:(r['q1']+r['q2'],r['oq1']+r['oq2']),'2H':lambda r:(r['q3']+r['q4']+r['ot'],r['oq3']+r['oq4']+r['oot']),'FULL':lambda r:(r['pts'],r['opp_pts'])}
print("-- team totals: MAE of home-team own-median line vs matchup-average projection vs league-average (walk-forward, both >=8 games)")
for seg,fn in segs.items():
    e1=[];e2=[];e3=[]
    for gid,R in tg.items():
        if len(R)!=2: continue
        a,b=R; ha=[h for h in by_t[a['team']] if h['date']<a['date']]; hb=[h for h in by_t[b['team']] if h['date']<b['date']]
        if len(ha)<8 or len(hb)<8: continue
        fa=[fn(h) for h in ha]; fb=[fn(h) for h in hb]; act=sum(fn(a))
        proj=(statistics.fmean(x[0] for x in fa)+statistics.fmean(x[1] for x in fb))/2+(statistics.fmean(x[0] for x in fb)+statistics.fmean(x[1] for x in fa))/2
        home=a if a['home'] else b; hh=[sum(fn(h)) for h in (ha if a['home'] else hb)]
        lg=[sum(fn(h)) for t in by_t.values() for h in t if h['date']<a['date']]
        e1.append(abs(statistics.median(hh[-20:])-act)); e2.append(abs(proj-act)); e3.append(abs(statistics.fmean(lg)-act))
    print(f"   {seg:5s} own-median {statistics.fmean(e1):5.1f}   matchup-avg {statistics.fmean(e2):5.1f}   league-avg {statistics.fmean(e3):5.1f}   n={len(e1)}")
