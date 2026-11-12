"""Walk-forward model comparison (run from repo root: python tools/model_experiments.py).
Team scoring models first, then player projection methods. Change a constant in nba_tracker.py only if it wins here."""
import json, statistics as st, collections, math, itertools
tg=json.load(open('data/nba/team_games.json'))
games=[]  # (date, home_row, away_row)
for gid,R in tg.items():
    if len(R)!=2: continue
    h=R[0] if R[0]['home'] else R[1]; a=R[1] if R[0]['home'] else R[0]; games.append((h['date'],h,a))
games.sort(key=lambda g:g[0])
poss=lambda r:(r['fga']+0.44*r['fta']-r['oreb']+r['tov'] + r['opp_fga']+0.44*r['opp_fta']-r['opp_oreb']+r['opp_tov'])/2
hist=collections.defaultdict(list)  # team -> prior rows
def shrink(vals,prior,k,w=None):
    if not vals: return prior
    if w is None: w=[1]*len(vals)
    return (sum(v*x for v,x in zip(vals,w))+k*prior)/(sum(w)+k)
def wts(n,decay):  # newest last
    return [decay**(n-1-i) for i in range(n)]
def last_date(t): return hist[t][-1]['date'] if hist[t] else None
import datetime
def rest(t,d):
    ld=last_date(t)
    return 3 if not ld else (datetime.date.fromisoformat(d)-datetime.date.fromisoformat(ld)).days
res=collections.defaultdict(lambda: collections.defaultdict(list))
allrows=[]
MIN=3
for d,h,a in games:
    H,A=hist[h['team']],hist[a['team']]
    if len(H)>=MIN and len(A)>=MIN and len(allrows)>=40:
        lg_pts=st.fmean(r['pts'] for r in allrows); lg_pos=st.fmean(poss(r) for r in allrows); lg_eff=lg_pts/lg_pos
        hca=st.fmean((r['pts']-r['opp_pts']) for r in allrows if r['home'])/2
        act_h,act_a=h['pts'],a['pts']
        def rec(name,ph,pa):
            res[name]['tot'].append(abs(ph+pa-(act_h+act_a))); res[name]['mar'].append(abs((ph-pa)-(act_h-act_a)))
            res[name]['tp'].append(abs(ph-act_h)); res[name]['tp'].append(abs(pa-act_a))
            res[name]['side'].append(((ph-pa)>0)==((act_h-act_a)>0))
        # baselines
        rec('league-avg', lg_pts+hca, lg_pts-hca)
        rec('own-median', st.median(r['pts'] for r in H[-20:]), st.median(r['pts'] for r in A[-20:]))
        m=lambda X,k:st.fmean(r[k] for r in X)
        rec('matchup-avg (current)', (m(H,'pts')+m(A,'opp_pts'))/2, (m(A,'pts')+m(H,'opp_pts'))/2)
        # additive shrunk ratings
        for k in (4,8,12):
            for dec in (1.0,0.93):
                oh=shrink([r['pts'] for r in H],lg_pts,k,wts(len(H),dec)); dh=shrink([r['opp_pts'] for r in H],lg_pts,k,wts(len(H),dec))
                oa=shrink([r['pts'] for r in A],lg_pts,k,wts(len(A),dec)); da=shrink([r['opp_pts'] for r in A],lg_pts,k,wts(len(A),dec))
                rec(f'additive k={k} decay={dec}', oh+da-lg_pts+hca, oa+dh-lg_pts-hca)
        # possession model: pace x efficiency, shrunk
        for k in (4,8,12):
            ph_=shrink([poss(r) for r in H],lg_pos,k); pa_=shrink([poss(r) for r in A],lg_pos,k)
            pace=ph_*pa_/lg_pos
            eo=lambda X:shrink([r['pts']/poss(r) for r in X],lg_eff,k); ed=lambda X:shrink([r['opp_pts']/poss(r) for r in X],lg_eff,k)
            eh=eo(H)*ed(A)/lg_eff; ea=eo(A)*ed(H)/lg_eff
            hp=hca/ 1
            rec(f'pace x eff k={k}', pace*eh+hca, pace*ea-hca)
            # + rest adj: b2b -1.5 pts
            rh,ra=rest(h['team'],d),rest(a['team'],d)
            adj=lambda r:-1.5 if r==1 else 0
            rec(f'pace x eff k={k} +b2b', pace*eh+hca+adj(rh), pace*ea-hca+adj(ra))
    hist[h['team']].append(h); hist[a['team']].append(a); allrows+= [h,a]
n=len(res['league-avg']['tot']); print("games scored:",n)
print(f"{'model':30s}{'total MAE':>10s}{'margin MAE':>11s}{'team pts MAE':>13s}{'winner %':>9s}")
for name,r in sorted(res.items(), key=lambda kv: st.fmean(kv[1]['tot'])+st.fmean(kv[1]['mar'])):
    print(f"{name:30s}{st.fmean(r['tot']):10.2f}{st.fmean(r['mar']):11.2f}{st.fmean(r['tp']):13.2f}{100*st.fmean(r['side']):9.1f}")


# ======================= players =======================
import json, statistics as st, collections
pg=json.load(open('data/nba/player_games.json')); tg=json.load(open('data/nba/team_games.json'))
rows=sorted([r for g in pg.values() for r in g], key=lambda r:r['date'])
trow={ (r['game_id'],r['team']):r for g in tg.values() for r in g}
poss=lambda r:(r['fga']+0.44*r['fta']-r['oreb']+r['tov'] + r['opp_fga']+0.44*r['opp_fta']-r['opp_oreb']+r['opp_tov'])/2
STATS={'PTS':lambda r:r['pts'],'REB':lambda r:r['reb'],'AST':lambda r:r['ast'],'3PM':lambda r:r['fg3m'],'PRA':lambda r:r['pts']+r['reb']+r['ast']}
hist=collections.defaultdict(list); thist=collections.defaultdict(list)   # team rows prior
# opponent allowed per-game totals by stat (team level) prior to date
def opp_factor(opp, stat, date, lg):
    R=[r for r in thist[opp] if r['date']<date]
    if len(R)<4: return 1.0
    key={'PTS':'opp_pts','REB':'opp_reb','AST':'opp_ast','3PM':'opp_fg3m'}.get(stat)
    if not key: 
        v=st.fmean(r['opp_pts']+r['opp_reb']+r['opp_ast'] for r in R); l=lg['PRA']
    else: v=st.fmean(r[key] for r in R); l=lg[stat]
    n=len(R); f=v/l
    return 1+(f-1)*n/(n+8)       # shrink toward 1
res=collections.defaultdict(lambda: collections.defaultdict(list))
teamrows_sorted=sorted([r for g in tg.values() for r in g], key=lambda r:r['date'])
ti=0; seen=[]
for r in rows:
    while ti<len(teamrows_sorted) and teamrows_sorted[ti]['date']<r['date']:
        x=teamrows_sorted[ti]; thist[x['team']].append(x); seen.append(x); ti+=1
    H=hist[r['player_id']]
    elig=[h for h in H if h['min']>=15]
    if len(elig)>=5 and r['min']>=15 and len(seen)>=60:
        lg={'PTS':st.fmean(x['pts'] for x in seen),'REB':st.fmean(x['reb'] for x in seen),'AST':st.fmean(x['ast'] for x in seen),'3PM':st.fmean(x['fg3m'] for x in seen)}
        lg['PRA']=lg['PTS']+lg['REB']+lg['AST']
        mins=[h['min'] for h in elig]
        exp_min=0.5*st.fmean(mins[-3:])+0.3*st.fmean(mins[-8:])+0.2*st.fmean(mins)
        for s,fn in STATS.items():
            v=[fn(h) for h in elig]; act=fn(r)
            P={}
            P['median L20 (current line)']=st.median(v[-20:])
            P['season mean']=st.fmean(v)
            P['L5 mean']=st.fmean(v[-5:])
            P['blend .6 season/.4 L5']=.6*st.fmean(v)+.4*st.fmean(v[-5:])
            rate=sum(v)/sum(mins)                      # per-minute, whole sample
            P['per-min x exp minutes']=rate*exp_min
            rate_rec=.6*rate+.4*(sum(v[-5:])/sum(mins[-5:]))
            P['per-min(blend) x exp min']=rate_rec*exp_min
            of=opp_factor(r['opp'],s,r['date'],lg)
            P['per-min x exp min x opp']=rate*exp_min*of
            P['per-min(blend) x exp min x opp']=rate_rec*exp_min*of
            for k,p in P.items(): res[s][k].append(abs(p-act))
    hist[r['player_id']].append(r)
for s in STATS:
    print(f"== {s}  (n={len(res[s]['season mean'])})")
    for k,v in sorted(res[s].items(), key=lambda kv: st.fmean(kv[1])): print(f"   {k:34s} MAE {st.fmean(v):.3f}")
