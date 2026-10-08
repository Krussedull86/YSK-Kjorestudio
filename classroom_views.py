from classroom import board
from course_setup import trip_number
from core import QUAL,metrics
MODES=['Samlet poeng','Forbedring','Forbruk','Tid per km','Stopp per km','Trafikksikkerhet','Fartsavpassing','Fartsøkning','Komfort','Vurderinger','Siste turer']
LABELS={'trafikksikkerhet':'Trafikksikkerhet','avpassing':'Fartsavpassing','økning':'Fartsøkning','komfort':'Komfort'}
RATING={'Bra':100,'Middel':50,'Svak':0}
def projection(rows,weights,mode='Samlet poeng',baseline='Første tur',**filters):
 baseline=trip_number(baseline)
 out=board(rows,weights,**filters)
 for d in out:
  history=d['history'];start=history[0] if baseline=='Første tur' else next((r for r in history if str(r['trip'])==str(baseline)),None)
  current=metrics(d);initial=metrics(start) if start else None;d['baseline']=start
  d['improvement']=None if not initial or start['trip']==d['trip'] or initial['forbruk10']==0 else 100*(initial['forbruk10']-current['forbruk10'])/initial['forbruk10']
  d['quality']=sum(RATING[d[q]] for q in QUAL)/4
  d['view_value']={'Samlet poeng':d['score'],'Forbedring':d['improvement'],'Forbruk':d['forbruk10'],'Tid per km':d['tid'],'Stopp per km':d['stopp'],'Trafikksikkerhet':RATING[d['trafikksikkerhet']],'Fartsavpassing':RATING[d['avpassing']],'Fartsøkning':RATING[d['økning']],'Komfort':RATING[d['komfort']],'Vurderinger':d['quality'],'Siste turer':d.get('date','')+' '+d.get('start_time','')+' '+d.get('updated','')}[mode]
 groups={}
 for d in out:groups.setdefault((d['course'],d['vehicle'],d['trip']),[]).append(d)
 low=mode in ['Forbruk','Tid per km','Stopp per km']
 for peers in groups.values():
  available=[d for d in peers if d['view_value'] is not None];available.sort(key=lambda d:d['view_value'],reverse=not low)
  score=None;place=0
  for n,d in enumerate(available,1):
   if d['view_value']!=score:score=d['view_value'];place=n
   d['view_place']=place
  for d in peers:
   if d['view_value'] is None:d['view_place']=None
 if mode=='Siste turer':return sorted(out,key=lambda d:d['view_value'],reverse=True)
 return sorted(out,key=lambda d:(d['course'],d['vehicle'],d['trip'],d['view_place'] is None,d['view_place'] or 0,d['driver'].casefold()))
def value_text(d,mode):
 value=d['view_value']
 if value is None:return '—'
 return {'Samlet poeng':lambda:f'{value:.1f} poeng','Forbedring':lambda:f'{value:+.1f}%','Forbruk':lambda:f'{value:.2f} L/10 km','Tid per km':lambda:f'{value:.2f} min/km','Stopp per km':lambda:f'{value:.2f} stopp/km','Trafikksikkerhet':lambda:'Middels' if d['trafikksikkerhet']=='Middel' else d['trafikksikkerhet'],'Fartsavpassing':lambda:'Middels' if d['avpassing']=='Middel' else d['avpassing'],'Fartsøkning':lambda:'Middels' if d['økning']=='Middel' else d['økning'],'Komfort':lambda:'Middels' if d['komfort']=='Middel' else d['komfort'],'Vurderinger':lambda:f'{value:.0f}/100','Siste turer':lambda:d.get('date','')+' '+d.get('start_time','')}[mode]()
def statistics(rows):
 avg=lambda values:sum(values)/len(values) if values else None
 improvements=[d['improvement'] for d in rows if d['improvement'] is not None]
 return {'students':len(rows),'trips':sum(len(d['completed']) for d in rows),'complete':sum(5 in d['completed'] for d in rows),'fuel':avg([d['forbruk10'] for d in rows]),'improvement':avg(improvements),'stops':sum(d['stops'] for d in rows)}
