"""Does a defensive weakness actually lift opposing players? Walk-forward, by tercile. Run from repo root."""
import json, statistics as st, collections
pg=json.load(open('data/nba/player_games.json')); tg=json.load(open('data/nba/team_games.json'))
prow=sorted([r for g in pg.values() for r in g], key=lambda r:r['date'])
trows=sorted([r for g in tg.values() for r in g], key=lambda r:r['date'])
# defensive metric per team from prior games; each = (label, fn over list of team rows) ; higher = weaker defense
D={
 'PTS allowed':   lambda R: st.fmean(r['opp_pts'] for r in R),
 'DRtg':          lambda R: sum(r['opp_pts'] for r in R)/sum(r['opp_fga']+.44*r['opp_fta']-r['opp_oreb']+r['opp_tov'] for r in R),
 'REB allowed':   lambda R: st.fmean(r['opp_reb'] for r in R),
 'opp REB% (allowed share)': lambda R: sum(r['opp_reb'] for r in R)/sum(r['opp_reb']+r['reb'] for r in R),
 'AST allowed':   lambda R: st.fmean(r['opp_ast'] for r in R),
 '3PM allowed':   lambda R: st.fmean(r['opp_fg3m'] for r in R),
 '3P% allowed':   lambda R: sum(r['opp_fg3m'] for r in R)/sum(r['opp_fg3a'] for r in R),
 '3PA allowed':   lambda R: st.fmean(r['opp_fg3a'] for r in R),
 'STL allowed':   lambda R: st.fmean(r['opp_stl'] for r in R),
 'own TOV (gives steals)': lambda R: st.fmean(r['tov'] for r in R),
 'BLK allowed':   lambda R: st.fmean(r['opp_blk'] for r in R),
 'TOV forced':    lambda R: st.fmean(r['opp_tov'] for r in R),
 'pace':          lambda R: st.fmean((r['fga']+.44*r['fta']-r['oreb']+r['tov']+r['opp_fga']+.44*r['opp_fta']-r['opp_oreb']+r['opp_tov'])/2 for r in R),
 'FTA allowed':   lambda R: st.fmean(r['opp_fta'] for r in R),
 'paint pts allowed': lambda R: st.fmean(r.get('opp_pitp',0) for r in R),
}
PAIRS=[('PTS','PTS allowed'),('PTS','DRtg'),('PTS','pace'),('PTS','FTA allowed'),('PTS','paint pts allowed'),
       ('REB','REB allowed'),('REB','opp REB% (allowed share)'),('REB','pace'),
       ('AST','AST allowed'),('AST','DRtg'),('AST','pace'),
       ('3PM','3PM allowed'),('3PM','3P% allowed'),('3PM','3PA allowed'),
       ('STL','STL allowed'),('STL','own TOV (gives steals)'),('BLK','BLK allowed'),('TOV','TOV forced'),
       ('PRA','PTS allowed'),('PRA','DRtg'),('PRA','pace')]
S={'PTS':lambda r:r['pts'],'REB':lambda r:r['reb'],'AST':lambda r:r['ast'],'3PM':lambda r:r['fg3m'],'STL':lambda r:r['stl'],'BLK':lambda r:r['blk'],'TOV':lambda r:r['tov'],'PRA':lambda r:r['pts']+r['reb']+r['ast']}
thist=collections.defaultdict(list); hist=collections.defaultdict(list); ti=0
out=collections.defaultdict(lambda: {'weak':[], 'mid':[], 'strong':[]})
for r in prow:
    while ti<len(trows) and trows[ti]['date']<r['date']:
        thist[trows[ti]['team']].append(trows[ti]); ti+=1
    H=[h for h in hist[r['player_id']] if h['min']>=15]
    if len(H)>=5 and r['min']>=15 and len(thist[r['opp']])>=5 and sum(len(v)>=5 for v in thist.values())>=24:
        ranks={}
        for stat,dm in PAIRS:
            if dm not in ranks:
                vals={t:D[dm](R) for t,R in thist.items() if len(R)>=5}
                order=sorted(vals,key=vals.get); n=len(order); pos=order.index(r['opp'])
                ranks[dm]='strong' if pos<n/3 else ('weak' if pos>=2*n/3 else 'mid')
            mean=st.fmean(S[stat](h) for h in H)
            if mean>= (1.0 if stat in('STL','BLK','3PM','TOV') else 3): 
                out[(stat,dm)][ranks[dm]].append((S[stat](r)-mean, S[stat](r)>mean, mean))
    hist[r['player_id']].append(r)
print(f"{'player stat':6s} {'vs defense metric':28s} {'weak D: diff%  over%   n':>26s} {'strong D: diff%  over%   n':>28s}  spread")
for (stat,dm),b in out.items():
    def f(x):
        if not x: return (0,0,0)
        return (100*sum(d for d,_,_ in x)/sum(m for _,_,m in x), 100*st.fmean(o for _,o,_ in x), len(x))
    w,s_=f(b['weak']),f(b['strong'])
    print(f"{stat:6s} {dm:28s} {w[0]:+10.1f}% {w[1]:6.1f}% {w[2]:5d}   {s_[0]:+10.1f}% {s_[1]:6.1f}% {s_[2]:5d}   {w[0]-s_[0]:+6.1f}")
