import sqlite3, json, math, uuid, datetime, contextlib
from pathlib import Path
QUAL = ['trafikksikkerhet','avpassing','økning','komfort']
WEIGHTS = {'tid':10,'forbruk':30,'stopp':10,'trafikksikkerhet':25,'avpassing':10,'økning':5,'komfort':10}
class Store:
 def __init__(self,path):
  self.path=str(path); Path(path).parent.mkdir(parents=True,exist_ok=True)
  with self.conn() as c:
   c.execute('CREATE TABLE IF NOT EXISTS trips (id TEXT PRIMARY KEY, driver TEXT NOT NULL, course TEXT NOT NULL, vehicle TEXT NOT NULL, trip INTEGER NOT NULL, payload TEXT NOT NULL, UNIQUE(driver,course,vehicle,trip))')
   c.execute('CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, payload TEXT)')
 @contextlib.contextmanager
 def conn(self):
  c=sqlite3.connect(self.path,timeout=10)
  try:
   c.execute('PRAGMA journal_mode=WAL')
   with c:yield c
  finally:c.close()
 def settings(self):
  with self.conn() as c: r=c.execute('SELECT payload FROM settings WHERE id=1').fetchone()
  return json.loads(r[0]) if r else dict(WEIGHTS)
 def set_settings(self,w):
  w={k:float(w[k]) for k in WEIGHTS}
  if any(not math.isfinite(v) or v<0 for v in w.values()) or sum(w.values())<=0: raise ValueError('Vektene må være positive eller null, og summen større enn null.')
  with self.conn() as c:c.execute('INSERT OR REPLACE INTO settings VALUES (1,?)',(json.dumps(w),))
 def save(self,d,connection=None):
  d=dict(d)
  for k in ['driver','course','vehicle']:
   d[k]=str(d.get(k,'')).strip()
   if not d[k] or len(d[k])>100: raise ValueError('Fyll inn sjåfør, kurs og kjøretøy (maks 100 tegn).')
  for k in QUAL:
   if d.get(k)=='Middels':d[k]='Middel'
  if ':' in str(d.get('minutes','')):
   parts=[float(v) for v in str(d['minutes']).split(':')]
   if len(parts) not in (2,3) or any(v<0 for v in parts) or any(v>=60 for v in parts[1:]):raise ValueError('Tid: minutter eller mm:ss / tt:mm:ss.')
   d['minutes']=sum(v*60**i for i,v in enumerate(reversed(parts)))/60
  for k in ['date','start_time','teacher']:
   d[k]=str(d.get(k,'')).strip()
  if d['date']:datetime.date.fromisoformat(d['date'])
  if d['start_time']:datetime.datetime.strptime(d['start_time'],'%H:%M')
  if len(d['teacher'])>100:raise ValueError('Lærer/signatur: maks 100 tegn.')
  if str(d.get('average_speed','')).strip():
   d['average_speed']=float(str(d['average_speed']).replace(',','.'))
   if not math.isfinite(d['average_speed']) or d['average_speed']<0:raise ValueError('Gjennomsnittsfart må være minst null.')
  else:d.pop('average_speed',None)
  trip=float(d['trip'])
  if not math.isfinite(trip) or not trip.is_integer(): raise ValueError('Tur må være et heltall.')
  d['trip']=int(trip)
  if d['trip'] not in range(1,6): raise ValueError('Tur må være 1–5.')
  for k in ['minutes','km','liters','stops']:
   d[k]=float(str(d[k]).replace(',','.'))
   if not math.isfinite(d[k]) or d[k]<0: raise ValueError('Tall må være endelige og minst null.')
  if d['minutes']<=0 or d['km']<=0: raise ValueError('Tid og km må være større enn null.')
  if not d['stops'].is_integer(): raise ValueError('Stopp må være et heltall.')
  for k in QUAL:
   if d.get(k) not in ['Bra','Middel','Svak']:raise ValueError('Velg Bra, Middel eller Svak.')
  d['notes']=str(d.get('notes',''))[:2000]
  d['updated']=datetime.datetime.now().isoformat(timespec='seconds')
  d['id']=str(d.get('id') or uuid.uuid4())
  with (self.conn() if connection is None else contextlib.nullcontext(connection)) as c:
   old=c.execute('SELECT id FROM trips WHERE driver=? AND course=? AND vehicle=? AND trip=?',(d['driver'],d['course'],d['vehicle'],d['trip'])).fetchone()
   if old and old[0]!=d['id']:raise ValueError('Denne turen finnes allerede. Åpne den for å endre.')
   c.execute('INSERT INTO trips VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET driver=excluded.driver,course=excluded.course,vehicle=excluded.vehicle,trip=excluded.trip,payload=excluded.payload',(d['id'],d['driver'],d['course'],d['vehicle'],d['trip'],json.dumps(d,ensure_ascii=False)))
  return d
 def all(self):
  with self.conn() as c:return [json.loads(r[0]) for r in c.execute('SELECT payload FROM trips ORDER BY course,vehicle,driver,trip')]
 def delete(self,id):
  with self.conn() as c:c.execute('DELETE FROM trips WHERE id=?',(id,))
 def backup(self,path):
  with self.conn() as src,contextlib.closing(sqlite3.connect(path)) as dst:
   with dst:src.backup(dst)
def metrics(d):return {'tid':d['minutes']/d['km'],'forbruk':d['liters']/d['km'],'stopp':d['stops']/d['km'],'forbruk10':10*d['liters']/d['km'],'fart':d.get('average_speed',60*d['km']/d['minutes'])}
def ranking(rows,w):
 # Compute comparison ranges once per course / vehicle / trip.
 groups={};measured=[]
 for d in rows:
  m=metrics(d);group=(d['course'],d['vehicle'],d['trip']);measured.append((d,m,group))
  ranges=groups.setdefault(group,{k:[m[k],m[k]] for k in ['tid','forbruk','stopp']})
  for k in ranges:ranges[k][0]=min(ranges[k][0],m[k]);ranges[k][1]=max(ranges[k][1],m[k])
 result=[];total=sum(w.values())
 for d,m,group in measured:
  scores={k:{'Bra':100,'Middel':50,'Svak':0}[d[k]] for k in QUAL}
  for k,(lo,hi) in groups[group].items():scores[k]=100 if hi==lo else 100*(hi-m[k])/(hi-lo)
  result.append(dict(d,score=round(sum(scores[k]*w[k] for k in w)/total,1),**m))
 return sorted(result,key=lambda d:(d['course'],d['vehicle'],d['trip'],-d['score'],d['driver']))
def changes(rows):
 groups={}
 for d in rows:groups.setdefault((d['course'],d['vehicle'],d['driver']),[]).append(d)
 out=[]
 for key,ds in groups.items():
  ds=sorted(ds,key=lambda d:d['trip']); a=ds[0]; b=ds[-1]; ma,mb=metrics(a),metrics(b)
  delta={k:mb[k]-ma[k] for k in ma}
  percent={k:None if ma[k]==0 else 100*delta[k]/ma[k] for k in ma}
  out.append({'group':key,'first':a,'last':b,'delta':delta,'percent':percent,'ratings':{k:f'{a[k]} → {b[k]}' for k in QUAL}})
 return out
