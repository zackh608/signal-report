"""Rest/travel, teammate-out, minutes trend, role change and game-script effects, measured on stored games. Run from repo root."""
import json, statistics as st, collections, datetime, sys
sys.path.insert(0,'.'); import nba_tracker as T
tg=json.load(open('data/nba/team_games.json')); pg=json.load(open('data/nba/player_games.json'))
TZ={'BOS':-5,'BKN':-5,'NY':-5,'PHI':-5,'TOR':-5,'CHI':-6,'CLE':-5,'DET':-5,'IND':-5,'MIL':-6,'ATL':-5,'CHA':-5,'MIA':-5,'ORL':-5,'WSH':-5,
    'DEN':-7,'MIN':-6,'OKC':-6,'POR':-8,'UTAH':-7,'GS':-8,'LAC':-8,'LAL':-8,'PHX':-7,'SAC':-8,'DAL':-6,'HOU':-6,'MEM':-6,'NO':-6,'SA':-6}
games=[]
for R in tg.values():
    if len(R)==2:
        h,a=(R[0],R[1]) if R[0]['home'] else (R[1],R[0]); games.append((h['date'],h,a))
games.sort(key=lambda g:g[0])
hist=collections.defaultdict(list); seen=[]
B=collections.defaultdict(list)
D=lambda s: datetime.date.fromisoformat(s)
save=T.B2B_PENALTY; T.B2B_PENALTY=0
for d,h,a in games:
    H,A=hist[h['team']],hist[a['team']]; lg=T.league_context(seen); p=T.predict_game(H,A,lg)
    if p:
        for row,pred,R in ((h,p[0],H),(a,p[1],A)):
            res=row['pts']-pred; dates=[D(x['date']) for x in R]; today=D(d)
            rest=(today-max(dates)).days
            n4=sum((today-x).days<=3 for x in dates); n6=sum((today-x).days<=5 for x in dates)
            # consecutive away games before this one
            trip=0
            for x in reversed(R):
                if not x['home']: trip+=1
                else: break
            if row['home']: trip=0
            loc_prev = TZ[R[-1]['team']] if R[-1]['home'] else TZ.get(R[-1]['opp'],-6)
            loc_now = TZ[row['team']] if row['home'] else TZ.get(row['opp'],-6)
            B['all'].append(res)
            B['b2b' if rest==1 else ('1 day rest' if rest==2 else '2+ days rest')].append(res)
            if n4>=2: B['3rd game in 4 nights'].append(res)
            if n6>=3: B['4th game in 6 nights'].append(res)
            if trip>=2: B['3rd+ straight road game'].append(res)
            if abs(loc_now-loc_prev)>=2: B['2+ time zones since last game'].append(res)
            if loc_now-loc_prev>=2: B['  travelled east 2+ zones'].append(res)
            if loc_now-loc_prev<=-2: B['  travelled west 2+ zones'].append(res)
            B['home' if row['home'] else 'away'].append(res)
    hist[h['team']].append(h); hist[a['team']].append(a); seen+=[h,a]
T.B2B_PENALTY=save
print("== REST / TRAVEL: team points vs model (no rest adj). negative = scored less than projected")
for k,v in B.items(): print(f"  {k:32s} n={len(v):4d}  avg {st.fmean(v):+5.2f}  (se {st.pstdev(v)/len(v)**.5:.2f})")

# ---------- player context
prow=sorted([r for g in pg.values() for r in g], key=lambda r:r['date'])
margin={(r['game_id'],r['team']):r['pts']-r['opp_pts'] for g in tg.values() for r in g}
by_game_team=collections.defaultdict(dict)
for r in prow: by_game_team[(r['game_id'],r['team'])][r['player_id']]=r
phist=collections.defaultdict(list); team_games=collections.defaultdict(list)  # team -> list of game_ids in order
order=sorted({(r['date'],r['game_id'],r['team']) for r in prow})
S={'PTS':lambda r:r['pts'],'REB':lambda r:r['reb'],'AST':lambda r:r['ast'],'MIN':lambda r:r['min']}
WO=collections.defaultdict(lambda: collections.defaultdict(list)); TR=collections.defaultdict(lambda: collections.defaultdict(list)); BL=collections.defaultdict(lambda: collections.defaultdict(list)); ST=collections.defaultdict(lambda: collections.defaultdict(list))
split_err=collections.defaultdict(lambda:[0,0,0])
for d,gid,tm in order:
    roster=by_game_team[(gid,tm)]
    # team's top-3 by prior avg minutes (>=5 games played for this team)
    prior={pid:[h for h in phist[pid] if h['team']==tm] for pid in {p for g in team_games[tm] for p in by_game_team[(g,tm)]}}
    top=sorted([pid for pid,H in prior.items() if len(H)>=5], key=lambda pid:-st.fmean(h['min'] for h in prior[pid]))[:3]
    absent=[pid for pid in top if pid not in roster or roster[pid]['min']<1]
    for pid,r in roster.items():
        H=[h for h in phist[pid] if h['min']>=15]
        if len(H)>=5 and r['min']>=15:
            m={k:st.fmean(f(h) for h in H) for k,f in S.items()}
            others_absent=[x for x in absent if x!=pid]
            tier='32+ min' if m['MIN']>=32 else ('24-32 min' if m['MIN']>=24 else '15-24 min')
            for k,f in S.items():
                if m[k] >= (3 if k!='MIN' else 1):
                    WO[k]['top-3 teammate OUT' if others_absent else 'all top-3 playing'].append((f(r)-m[k],m[k]))
                    l3=st.fmean(h['min'] for h in phist[pid][-3:]); dm=l3-m['MIN']
                    TR[k]['minutes L3 up 4+' if dm>=4 else ('minutes L3 down 4+' if dm<=-4 else 'steady')].append((f(r)-m[k],m[k]))
                    mg=margin.get((gid,tm),0)
                    BL[k][tier+(' | won by 15+' if mg>=15 else (' | lost by 15+' if mg<=-15 else ' | close'))].append((f(r)-m[k],m[k]))
                    was=st.fmean(h['starter'] for h in H[-5:])
                    if r['starter'] and was<=.2: ST[k]['new starter (bench L5)'].append((f(r)-m[k],m[k]))
                    elif (not r['starter']) and was>=.8: ST[k]['moved to bench (starter L5)'].append((f(r)-m[k],m[k]))
            # specific without-split test: player's own prior games when this absent teammate was out
            for x in others_absent[:1]:
                gw=[h for h in H if x not in by_game_team[(h['game_id'],tm)] or by_game_team[(h['game_id'],tm)][x]['min']<1]
                if len(gw)>=2:
                    for k in ('PTS','REB','AST'):
                        f=S[k]; base=m[k]; wo=st.fmean(f(h) for h in gw); n=len(gw)
                        e=split_err[k]; e[0]+=abs(base-f(r)); e[2]+=1
                        e[1]+=abs(base+(wo-base)*n/(n+4)-f(r))
    for pid,r in roster.items(): phist[pid].append(r)
    team_games[tm].append(gid)
def show(title,Dd,keys=('PTS','REB','AST','MIN')):
    print("==",title)
    for k in keys:
        for name,v in sorted(Dd[k].items()):
            if len(v)>=15: print(f"  {k:4s} {name:34s} n={len(v):5d}  {100*sum(d for d,_ in v)/sum(m for _,m in v):+6.1f}% vs own average")
show("TEAMMATE OUT (one of the team's top-3 minutes players absent)",WO)
show("MINUTES TREND",TR,('PTS','MIN'))
show("ROLE CHANGE",ST,('PTS','MIN'))
show("GAME SCRIPT (by final margin)",BL,('MIN','PTS'))
print("== player's own WITHOUT-teammate split as a predictor (shrunk n/(n+4)) vs season mean, MAE:")
for k,e in split_err.items(): print(f"  {k}: season mean {e[0]/e[2]:.3f}  with split {e[1]/e[2]:.3f}  n={e[2]}")
