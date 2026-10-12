"""School/course/vehicle comparisons with missing data kept visible."""
import math
from core import ranking

def analyse(rows,weights,course='Alle',vehicle='Alle',selected_trips=None):
 trips=tuple(t for t in (1,2,3) if selected_trips is None or t in selected_trips)
 selected=[d for d in rows if course=='Alle' or d['course']==course]
 optimal=[d for d in selected if d['trip'] in (1,2,3)]
 scores={d['id']:d['score'] for d in ranking([dict(d,trip=1) for d in optimal],weights)}
 groups={}
 for d in selected:groups.setdefault((d['course'],d['driver']),[]).append(d)
 result=[]
 for key,records in groups.items():
  if vehicle!='Alle' and not any(d['vehicle']==vehicle for d in records):continue
  bytrip={}
  for d in records:
   if d['trip'] in (1,2,3):bytrip.setdefault(d['trip'],[]).append(d)
  history={t:max(items,key=lambda d:(d.get('updated',''),d.get('date',''),d['id'])) for t,items in bytrip.items()}
  chosen=[d for t,items in bytrip.items() if t in trips for d in items]
  cars=sorted({d['vehicle'] for d in chosen} or {d['vehicle'] for d in records})
  changed=len({d['vehicle'] for d in chosen})>1;ambiguous=any(len(items)>1 for t,items in bytrip.items() if t in trips)
  points={t:scores.get(d['id']) for t,d in history.items()};a,b=(trips[0],trips[-1]) if len(trips)>=2 else (None,None)
  comparable=not changed and not ambiguous
  delta=points[b]-points[a] if comparable and a is not None and points.get(a) is not None and points.get(b) is not None else None
  available=[points[t] for t in trips if points.get(t) is not None]
  average=sum(available)/len(available) if available and comparable else None
  changes={metric:percent(value(history.get(a),metric),value(history.get(b),metric)) if comparable and a is not None else None for metric in ('fuel','stops','time','speed')}
  result.append(dict(key=key,driver=key[1],course=key[0],history=history,cars=cars,points=points,delta=delta,changed=changed,ambiguous=ambiguous,average=average,changes=changes,trips=trips,teachers=sorted({d.get('teacher','') for d in chosen if d.get('teacher')}),records=records))
 return sorted(result,key=lambda d:(d['driver'].casefold(),d['course'].casefold()))

def value(d,key):
 if not d:return None
 try:
  if key=='fuel':v=float(d['fuel_per_100'])/10 if d.get('fuel_per_100') is not None else 10*float(d['liters'])/float(d['km'])
  elif key=='stops':v=10*float(d['stops'])/float(d['km'])
  elif key=='speed':v=float(d['average_speed']) if str(d.get('average_speed','')).strip() else 60*float(d['km'])/float(d['minutes'])
  elif key=='time_per_km':v=float(d['minutes'])/float(d['km'])
  else:v=float(d['minutes'])
  return v if math.isfinite(v) and v>=0 else None
 except (KeyError,ValueError,TypeError,ZeroDivisionError):return None

def percent(a,b):return None if a is None or b is None or a==0 else 100*(b-a)/a

def summary(data,trips=(1,2,3)):
 return {'students':len(data),'complete':sum(all(d['points'].get(t) is not None for t in trips) and not d['ambiguous'] and not d['changed'] for d in data),'registered':sum(t in d['history'] for d in data for t in trips),'comparable':sum(d['delta'] is not None for d in data)}
