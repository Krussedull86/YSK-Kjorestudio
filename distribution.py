"""Delivery milestones; elapsed time includes loading, waiting and breaks."""
import math

def number(value,minimum=0,maximum=43200):
 if isinstance(value,bool):raise ValueError('Ugyldig tid.')
 try:value=float(str(value).replace(',','.'))
 except (ValueError,TypeError):raise ValueError('Skriv et gyldig antall minutter.') from None
 if not math.isfinite(value) or not minimum<=value<=maximum:raise ValueError('Tiden er utenfor tillatt område.')
 return value

def plan(stop_count=0,expected_minutes=0,deadlines=None):
 count=number(stop_count,0,30)
 if not count.is_integer():raise ValueError('Antall distribusjonsstopp må være et heltall (0–30).')
 count=int(count);total=number(expected_minutes,0,1440)
 if count==0:
  if total or deadlines:raise ValueError('Angi antall stopp før tidsplanen.')
  return {'stop_count':0,'expected_minutes':0,'deadlines':[]}
 if not total:raise ValueError('Angi forventet gjennomføringstid (1–1440 minutter).')
 if isinstance(deadlines,str):deadlines=[x.strip() for x in deadlines.split(';') if x.strip()]
 values=[number(x,0,1440) for x in deadlines] if deadlines else [total*(i+1)/count for i in range(count)]
 if len(values)!=count or any(v<=0 or v>total or i and v<=values[i-1] for i,v in enumerate(values)):
  raise ValueError('Angi én stigende frist per stopp, i minutter fra start, innen totaltiden.')
 return {'stop_count':count,'expected_minutes':total,'deadlines':values}

def validate_run(data):
 if not isinstance(data,dict):raise ValueError('Ugyldig distribusjonslogg.')
 if data.get('version')!=1:raise ValueError('Ukjent distribusjonslogg.')
 if not isinstance(data.get('deadlines'),list):raise ValueError('Ugyldige stoppfrister.')
 p=plan(len(data.get('deadlines',[])),data.get('expected_minutes',0),data.get('deadlines'))
 if not p['stop_count']:raise ValueError('Distribusjonsloggen mangler stopp.')
 started=number(data.get('started_at'),1,1e15)
 if not started.is_integer():raise ValueError('Ugyldig starttid.')
 events=data.get('events')
 if not isinstance(events,list) or len(events)>p['stop_count']:raise ValueError('Ugyldig stopplogg.')
 checked=[];last=0
 for i,e in enumerate(events,1):
  if not isinstance(e,dict) or e.get('stop')!=i or e.get('status') not in ('ramp','aborted'):raise ValueError('Stopp må registreres én gang og i rekkefølge.')
  elapsed=number(e.get('elapsed_minutes'))
  if elapsed<last:raise ValueError('Stopptidene må være stigende.')
  reason=e.get('reason','')
  if not isinstance(reason,str) or len(reason)>300:raise ValueError('Kommentar: maks 300 tegn.')
  checked.append({'stop':i,'status':e['status'],'elapsed_minutes':elapsed,'reason':reason});last=elapsed
 finished=data.get('finished_minutes')
 if finished is not None:
  finished=number(finished)
  if len(checked)!=p['stop_count'] or finished<last:raise ValueError('Merk alle stopp før oppdraget avsluttes.')
 return {'version':1,'expected_minutes':p['expected_minutes'],'deadlines':p['deadlines'],'started_at':int(started),'events':checked,'finished_minutes':finished}

def rows(data):
 data=validate_run(data);result=[];previous=0
 for e in data['events']:
  total=e['elapsed_minutes']
  result.append(e|{'segment_minutes':total-previous});previous=total
 return result

def summary(data):
 data=validate_run(data);completed=sum(e['status']=='ramp' for e in data['events']);aborted=sum(e['status']=='aborted' for e in data['events']);finished=data['finished_minutes']
 state='Pågår' if finished is None else 'Avsluttet'
 return f"{completed}/{len(data['deadlines'])} til rampe · {aborted} avbrutt · {state}"

def return_minutes(data):
 data=validate_run(data)
 if data['finished_minutes'] is None or len(data['events'])!=len(data['deadlines']):return None
 return data['finished_minutes']-data['events'][-1]['elapsed_minutes']
