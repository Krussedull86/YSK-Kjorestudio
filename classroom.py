"""Classroom projections: one row per student, comparable ranks and first/latest change."""
from core import metrics,ranking,QUAL

def key(d):return d['course'],d['vehicle'],d['driver']
def board(rows,weights,course='Alle',vehicle='Alle',trip='Alle'):
 selected=[d for d in rows if (course=='Alle' or d['course']==course) and (vehicle=='Alle' or d['vehicle']==vehicle)]
 ranked=ranking(selected,weights);groups={};positions={}
 for d in ranked:
  group=(d['course'],d['vehicle'],d['trip']);state=positions.setdefault(group,{'count':0,'score':None,'place':0});state['count']+=1
  if state['score']!=d['score']:state['score']=d['score'];state['place']=state['count']
  d['place']=state['place']
  groups.setdefault(key(d),[]).append(d)
 out=[]
 for k,ds in groups.items():
  ds.sort(key=lambda d:d['trip']);eligible=ds if trip=='Alle' else [d for d in ds if str(d['trip'])==str(trip)]
  if not eligible:continue
  d=dict(eligible[-1]);first=ds[0];current=d
  # Progress ends at displayed trip, never a later trip hidden by the filter.
  history=[p for p in ds if p['trip']<=d['trip']];a,b=metrics(first),metrics(current)
  pct=None if len(history)<2 or a['forbruk10']==0 else 100*(a['forbruk10']-b['forbruk10'])/a['forbruk10']
  d.update(history=history,first_trip=first['trip'],fuel_improvement=pct,fuel_saved=a['forbruk10']-b['forbruk10'],time_change=b['tid']-a['tid'],stops_change=current['stops']-first['stops'],completed={p['trip'] for p in ds},rating_change=sum({'Bra':2,'Middel':1,'Svak':0}[current[q]]-{'Bra':2,'Middel':1,'Svak':0}[first[q]] for q in QUAL))
  out.append(d)
 return sorted(out,key=lambda d:(d['course'],d['vehicle'],d['trip'],d['place'],d['driver'].casefold()))

def improvement_rows(rows):return sorted(rows,key=lambda d:(d['fuel_improvement'] is None,-(d['fuel_improvement'] or 0),d['driver'].casefold()))
