"""Comparable three-trip classroom analysis, preserving incomplete registrations."""
from core import ranking,scorable,metrics

def analyse(rows,weights,course='Alle',vehicle='Alle'):
 selected=[d for d in rows if d['trip'] in (1,2,3) and (course=='Alle' or d['course']==course)]
 # One common score scale across all three optimal trips, within course and vehicle.
 pooled=[dict(d,trip=1) for d in selected]
 scores={d['id']:d['score'] for d in ranking(pooled,weights)}
 groups={}
 for d in selected:groups.setdefault((d['course'],d['driver']),{}).setdefault(d['trip'],[]).append(d)
 result=[]
 for key,bytrip in groups.items():
  history={};ambiguous=False
  for t,items in bytrip.items():
   ambiguous|=len(items)>1
   history[t]=max(items,key=lambda d:(d.get('updated',''),d.get('date',''),d['id']))
  cars={d['vehicle'] for items in bytrip.values() for d in items}
  if vehicle!='Alle' and vehicle not in cars:continue
  changed=len(cars)>1;points={t:scores.get(d['id']) for t,d in history.items()}
  delta=None if changed or ambiguous or points.get(1) is None or points.get(3) is None else points[3]-points[1]
  result.append(dict(key=key,driver=key[1],course=key[0],history=history,cars=sorted(cars),points=points,delta=delta,changed=changed,ambiguous=ambiguous))
 return sorted(result,key=lambda d:(d['driver'].casefold(),d['course'].casefold()))

def value(d,key):
 if not d:return None
 try:
  if key=='fuel':v=10*float(d['liters'])/float(d['km'])
  elif key=='stops':v=10*float(d['stops'])/float(d['km'])
  else:v=float(d['minutes'])
  import math
  return v if math.isfinite(v) else None
 except (KeyError,ValueError,TypeError,ZeroDivisionError):return None

def percent(a,b):return None if a is None or b is None or a==0 else 100*(b-a)/a
