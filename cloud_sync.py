"""Cloud sync and authenticated trip management. Local edits are protected from overwrite."""
import uuid,base64,ctypes,hashlib,json,os,queue,threading,time,urllib.request,urllib.error,urllib.parse
from pathlib import Path
from tkinter import ttk,messagebox
import tkinter as tk

DEFAULT_URL='https://otuemdgmymgognzghmnu.supabase.co'
DEFAULT_API='sb_publishable_9-BPAUPJ5gv_MJ1hz6ah0g_yoz3npSu'

FIELDS=['driver','course','vehicle','trip','minutes','km','liters','stops','trafikksikkerhet','avpassing','økning','komfort','notes','date','start_time','teacher','average_speed','fuel_per_100','distribution','end_time','duration_source']
def fingerprint(d):
 values={k:d.get(k,'') for k in FIELDS}
 for k in ('end_time','duration_source'):
  if not values[k]:values.pop(k)
 if values.get('fuel_per_100') is None or not str(values.get('fuel_per_100','')).strip():values.pop('fuel_per_100',None)
 if str(values.get('average_speed','')).strip() not in ['', '-']:values['average_speed']=float(values['average_speed'])
 for k in ['trip','minutes','km','liters','stops','fuel_per_100']:
  if k in values and str(values[k]).strip() not in ['', '-']:values[k]=float(values[k])
 return hashlib.sha256(json.dumps(values,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def endpoint(url):
 p=urllib.parse.urlsplit(url.strip())
 if p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment or p.path not in ['', '/']:raise ValueError('Bruk Supabase Project URL med HTTPS og uten sti.')
 return 'https://'+p.netloc

def protect(text,decrypt=False):
 if os.name!='nt':raise RuntimeError('Lagring av skykonto krever Windows (DPAPI).')
 from ctypes import wintypes
 class Blob(ctypes.Structure):_fields_=[('cbData',wintypes.DWORD),('pbData',ctypes.POINTER(ctypes.c_byte))]
 raw=base64.b64decode(text) if decrypt else text.encode();buf=ctypes.create_string_buffer(raw);source=Blob(len(raw),ctypes.cast(buf,ctypes.POINTER(ctypes.c_byte)));dest=Blob()
 crypt=ctypes.WinDLL('crypt32',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree.restype=ctypes.c_void_p
 if decrypt:
  fn=crypt.CryptUnprotectData;fn.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
  ok=fn(ctypes.byref(source),None,None,None,None,1,ctypes.byref(dest))
 else:
  fn=crypt.CryptProtectData;fn.argtypes=[ctypes.POINTER(Blob),wintypes.LPCWSTR,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
  ok=fn(ctypes.byref(source),'YSK cloud session',None,None,None,1,ctypes.byref(dest))
 if not ok:raise ctypes.WinError(ctypes.get_last_error())
 try:
  result=ctypes.string_at(dest.pbData,dest.cbData);return result.decode() if decrypt else base64.b64encode(result).decode()
 finally:kernel.LocalFree(ctypes.cast(dest.pbData,ctypes.c_void_p))

def request(url,api,token=None,body=None):
 headers={'apikey':api,'Content-Type':'application/json'}
 if token:headers['Authorization']='Bearer '+token
 req=urllib.request.Request(url,data=None if body is None else json.dumps(body).encode(),headers=headers)
 try:
  with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)
 except urllib.error.HTTPError as e:
  error={}
  try:
   error=json.load(e);msg=error.get('msg') or error.get('message') or error.get('error_description') or f'HTTP {e.code}'
  except Exception:msg=f'HTTP {e.code}'
  raise APIError(msg,e.code,error.get('code','') if isinstance(error,dict) else '') from None

class LoginRequired(ValueError):pass

class APIError(ValueError):
 def __init__(self,message,status,code=''):
  super().__init__(message);self.status=status;self.code=code

class Receiver:
 def __init__(self,store,path):
  self.store=store;self.path=Path(path);self.lock=threading.RLock()
  with store.conn() as c:
   c.execute("CREATE TABLE IF NOT EXISTS cloud_outbox (id TEXT PRIMARY KEY, owner TEXT NOT NULL, payload TEXT NOT NULL, revision TEXT NOT NULL, expected TEXT NOT NULL, error TEXT NOT NULL DEFAULT '')")
   c.execute('CREATE TABLE IF NOT EXISTS cloud_ack (id TEXT, base TEXT, revision TEXT, PRIMARY KEY(id,base))')
   c.execute('CREATE TABLE IF NOT EXISTS cloud_flights (id TEXT PRIMARY KEY, owner TEXT NOT NULL, payload TEXT NOT NULL, revision TEXT NOT NULL, expected TEXT NOT NULL)')
   c.execute('CREATE TABLE IF NOT EXISTS cloud_seen (id TEXT PRIMARY KEY, remote_hash TEXT, local_hash TEXT)')
   c.execute('CREATE TABLE IF NOT EXISTS cloud_binding (id INTEGER PRIMARY KEY, account TEXT)')
   c.execute('CREATE TABLE IF NOT EXISTS cloud_conflicts (id TEXT PRIMARY KEY, message TEXT)')
   c.execute('CREATE TABLE IF NOT EXISTS cloud_versions (id TEXT PRIMARY KEY, row TEXT)')
   c.execute('CREATE TABLE IF NOT EXISTS cloud_deleted_local (id TEXT PRIMARY KEY, payload TEXT)')
 def load(self):
  if not self.path.exists():return None
  return json.loads(protect(self.path.read_text(),True))
 def save(self,cfg):
  self.path.parent.mkdir(parents=True,exist_ok=True);temp=self.path.with_suffix('.tmp');temp.write_text(protect(json.dumps(cfg)),encoding='utf-8');os.replace(temp,self.path)
 def bind(self,identity,legacy=None):
  with self.store.conn() as c:
   old=c.execute('SELECT account FROM cloud_binding WHERE id=1').fetchone()
   if old and old[0] not in [identity,legacy]:raise ValueError('Databasen er allerede knyttet til en annen skole/skykonto.')
   c.execute('INSERT OR REPLACE INTO cloud_binding VALUES(1,?)',(identity,))
 def connect(self,url,api,email,password):
  with self.lock:
   url=endpoint(url);api=api.strip()
   if not api or api.startswith('sb_secret_'):raise ValueError('Bruk publishable/anon key, aldri service_role eller secret.')
   if api.startswith('eyJ'):
    try:
     segment=api.split('.')[1];role=json.loads(base64.urlsafe_b64decode(segment+'='*((4-len(segment)%4)%4)))['role']
     if role!='anon':raise ValueError('API-nøkkelen må være anon/publishable.')
    except (KeyError,IndexError):raise ValueError('Ugyldig API-nøkkel.')
   session=request(url+'/auth/v1/token?grant_type=password',api,body={'email':email.strip(),'password':password})
   cfg={'url':url,'api':api,'email':email.strip(),'session':session};legacy=url+'|'+session['user']['id'];member=self.membership(cfg);identity=url+'|school:'+member['organization_id'] if member else legacy
   # Persist encrypted session before recording the permanent binding.
   with self.store.conn() as c:
    old=c.execute('SELECT account FROM cloud_binding WHERE id=1').fetchone()
    if old and old[0] not in [identity,legacy]:raise ValueError('Databasen er allerede knyttet til en annen skole/skykonto.')
   self.save(cfg);self.bind(identity,legacy)
 def membership(self,cfg):
  try:
   rows=request(cfg['url']+'/rest/v1/ysk_memberships?select=organization_id,role,active,display_name&user_id=eq.'+cfg['session']['user']['id'],cfg['api'],cfg['session']['access_token'])
  except APIError as e:
   if e.status==404 and e.code in ['PGRST205','42P01']:return None
   if e.status in (401,403):raise LoginRequired('Logg inn på nytt for å få tilgang.') from None
   raise
  if not rows or not rows[0]['active']:raise LoginRequired('Du har ikke aktiv tilgang til skolen.')
  return rows[0]
 def session(self):
  cfg=self.load()
  if not cfg:raise LoginRequired('Logg inn først.')
  s=cfg['session']
  if s.get('expires_at',0)<=time.time()+90:
   try:cfg['session']=request(cfg['url']+'/auth/v1/token?grant_type=refresh_token',cfg['api'],body={'refresh_token':s['refresh_token']})
   except APIError as e:
    if e.status in (400,401,403):raise LoginRequired('Innloggingen er utløpt. Logg inn på nytt.') from None
    raise
   self.save(cfg)
  return cfg
 def admin(self,action,**body):
  with self.lock:
   cfg=self.session()
   try:return request(cfg['url']+'/functions/v1/ysk-admin',cfg['api'],cfg['session']['access_token'],dict(body,action=action))
   except APIError as e:
    if e.status == 404:raise ValueError('Skole/admin er klargjort i pakken, men må aktiveres i Supabase før brukeradministrasjon virker.') from None
    raise
 def logout(self):
  with self.lock:
   try:
    cfg=self.load()
    if cfg:request(cfg['url']+'/auth/v1/logout?scope=local',cfg['api'],cfg['session']['access_token'],{})
   except Exception:pass
   finally:self.path.unlink(missing_ok=True)
 def remote(self,id):
  with self.store.conn() as c:r=c.execute('SELECT row FROM cloud_versions WHERE id=?',(id,)).fetchone()
  return json.loads(r[0]) if r else None
 def trip_list(self):
  rows=[]
  for offset in range(0,100000000,500):
   page=self.admin('trip_list',offset=offset)['rows'];rows.extend(page)
   if len(page)<500:return rows
 def queue_trip(self,d,expected_revision=''):
  cfg=self.load()
  if not cfg:raise LoginRequired('Logg inn før du legger turen i sendekøen.')
  owner=cfg['url']+'|'+cfg['session']['user']['id']
  validated=self.store.validate(d);ident=validated['id']
  with self.store.conn() as c:
   c.execute('BEGIN IMMEDIATE')
   old=c.execute('SELECT owner,expected FROM cloud_outbox WHERE id=?',(ident,)).fetchone()
   if old and old[0]!=owner:raise ValueError('Turen venter på sending fra en annen konto.')
   expected=old[1] if old else expected_revision
   if not old:
    for _ in range(100):
     ack=c.execute('SELECT revision FROM cloud_ack WHERE id=? AND base=?',(ident,expected)).fetchone()
     if not ack or ack[0]==expected:break
     expected=ack[0]
   validated['pc_draft_revision']=expected
   saved=self.store.save(validated,connection=c)
   payload=dict(saved);payload.pop('pc_draft_revision',None)
   c.execute("INSERT OR REPLACE INTO cloud_outbox VALUES(?,?,?,?,?, '')",(ident,owner,json.dumps(payload,ensure_ascii=False),str(uuid.uuid4()),expected))
  return saved
 def pending(self,id):
  with self.store.conn() as c:return c.execute('SELECT 1 FROM cloud_outbox WHERE id=?',(id,)).fetchone() is not None
 def send_queued(self,id):
  # Persist the exact in-flight request until acknowledged, including across restarts.
  # A newer local save stays queued while an older request is being acknowledged.
  with self.lock:
   cfg=self.load()
   if not cfg:raise LoginRequired('Logg inn først.')
   owner=cfg['url']+'|'+cfg['session']['user']['id']
   with self.store.conn() as c:
    c.execute('BEGIN IMMEDIATE')
    queued=c.execute('SELECT owner,payload,revision,expected FROM cloud_outbox WHERE id=?',(id,)).fetchone()
    if not queued:return {'row':self.remote(id)}
    if queued[0]!=owner:raise LoginRequired('Logg inn med kontoen som lagret utkastet.')
    flight=c.execute('SELECT owner,payload,revision,expected FROM cloud_flights WHERE id=?',(id,)).fetchone()
    if not flight:
     flight=queued;c.execute('INSERT INTO cloud_flights VALUES(?,?,?,?,?)',(id,*flight))
   try:result=self.admin('trip_save',payload=json.loads(flight[1]),revision=flight[2],expected_revision=flight[3])
   except Exception as error:
    with self.store.conn() as c:
     c.execute('UPDATE cloud_outbox SET error=? WHERE id=?',(str(error),id))
     if isinstance(error,APIError) and 400<=error.status<500:c.execute('DELETE FROM cloud_flights WHERE id=?',(id,))
    raise
   remote=result['row'];payload=remote['payload'];rh=fingerprint(payload)
   with self.store.conn() as c:
    c.execute('BEGIN IMMEDIATE')
    c.execute('INSERT OR REPLACE INTO cloud_ack VALUES(?,?,?)',(id,flight[3],remote['revision']))
    current=c.execute('SELECT revision FROM cloud_outbox WHERE id=?',(id,)).fetchone()
    c.execute('INSERT OR REPLACE INTO cloud_versions VALUES(?,?)',(id,json.dumps(remote,ensure_ascii=False)))
    c.execute('INSERT OR REPLACE INTO cloud_seen VALUES(?,?,?)',(id,rh,rh))
    c.execute('DELETE FROM cloud_conflicts WHERE id=?',(id,))
    if current and current[0]==flight[2]:
     self.store.save(payload,connection=c);c.execute('DELETE FROM cloud_outbox WHERE id=?',(id,))
    elif current:
     c.execute("UPDATE cloud_outbox SET expected=?,error='' WHERE id=?",(remote['revision'],id))
     local=c.execute('SELECT payload FROM trips WHERE id=?',(id,)).fetchone()
     if local:
      d=json.loads(local[0]);d['pc_draft_revision']=remote['revision'];c.execute('UPDATE trips SET payload=? WHERE id=?',(json.dumps(d,ensure_ascii=False),id))
    c.execute('DELETE FROM cloud_flights WHERE id=?',(id,))
   return result
 def save_trip(self,d,expected_revision=''):
  saved=self.queue_trip(d,expected_revision)
  return self.send_queued(saved['id'])
 def flush(self,cfg):
  owner=cfg['url']+'|'+cfg['session']['user']['id'];errors=[]
  with self.store.conn() as c:ids=[r[0] for r in c.execute('SELECT id FROM cloud_outbox WHERE owner=?',(owner,))]
  for id in ids:
   try:self.send_queued(id)
   except LoginRequired:raise
   except Exception as error:errors.append('Venter på sending: '+str(error))
  return errors
 def import_rows(self,rows,force=False):
  imported=0;conflicts=[]
  for remote in sorted(rows,key=lambda r:0 if r.get('deleted_at') else 1):
   d=remote['payload'];id=remote['id']
   if d.get('id')!=id:conflicts.append('Ugyldig ID fra sky');continue
   rh=fingerprint(d)
   with self.store.conn() as c:
    c.execute('BEGIN IMMEDIATE')
    seen=c.execute('SELECT remote_hash,local_hash FROM cloud_seen WHERE id=?',(id,)).fetchone()
    record=c.execute('SELECT payload FROM trips WHERE id=?',(id,)).fetchone()
    local=json.loads(record[0]) if record else None
    c.execute('INSERT OR REPLACE INTO cloud_versions VALUES(?,?)',(id,json.dumps(remote,ensure_ascii=False)))
    pending=c.execute('SELECT 1 FROM cloud_outbox WHERE id=?',(id,)).fetchone()
    if pending and not force:
     if remote.get('revision')!= (local or {}).get('pc_draft_revision'):
      message=f"{d.get('driver') or 'Utkast'}: lokale endringer venter; skyversjonen er ikke lagt over utkastet";conflicts.append(message)
     continue
    if force:
     c.execute('DELETE FROM cloud_outbox WHERE id=?',(id,));c.execute('DELETE FROM cloud_flights WHERE id=?',(id,))
    if remote.get('deleted_at'):
     if local:c.execute('INSERT OR REPLACE INTO cloud_deleted_local VALUES(?,?)',(id,json.dumps(local,ensure_ascii=False)))
     c.execute('DELETE FROM trips WHERE id=?',(id,));c.execute('DELETE FROM cloud_conflicts WHERE id=?',(id,))
     c.execute('INSERT OR REPLACE INTO cloud_seen VALUES(?,?,?)',(id,'deleted',rh))
     imported+=int(local is not None);continue
    if seen and seen[0]==rh and not force:continue
    if not force and local and ((seen and fingerprint(local)!=seen[1]) or (not seen and fingerprint(local)!=rh)):
     message=f"{d.get('driver','?')} tur {d.get('trip','?')}: endret på PC; ikke overskrevet";conflicts.append(message);c.execute('INSERT OR REPLACE INTO cloud_conflicts VALUES(?,?)',(id,message));continue
    try:stored=self.store.save(d,connection=c)
    except (ValueError,KeyError,TypeError) as e:
     message=f"{d.get('driver','?')}: {e}";conflicts.append(message);c.execute('INSERT OR REPLACE INTO cloud_conflicts VALUES(?,?)',(id,message));continue
    c.execute('INSERT OR REPLACE INTO cloud_seen VALUES(?,?,?)',(id,rh,fingerprint(stored)))
    c.execute('DELETE FROM cloud_conflicts WHERE id=?',(id,))
    imported+=1
  return imported,conflicts
 def sync(self,force=False):
  with self.lock:
   cfg=self.load()
   if not cfg:return 0,[],False
   s=cfg['session'];url=cfg['url'];api=cfg['api']
   if s.get('expires_at',0)<=time.time()+90:
    try:s=request(url+'/auth/v1/token?grant_type=refresh_token',api,body={'refresh_token':s['refresh_token']})
    except APIError as e:
     if e.status in (400,401,403):raise LoginRequired('Innloggingen er utløpt. Logg inn på nytt.') from None
     raise
    cfg['session']=s;self.save(cfg)
   member=self.membership(cfg);legacy=url+'|'+s['user']['id'];self.bind(url+'|school:'+member['organization_id'] if member else legacy,legacy);allrows=[];last=None
   with self.store.conn() as c:needs_full=bool(c.execute('SELECT 1 FROM cloud_seen WHERE id NOT IN (SELECT id FROM cloud_versions) LIMIT 1').fetchone())
   send_errors=[] if force else self.flush(cfg)
   while True:
    params={'select':'id,payload,updated_at,revision,deleted_at,owner_id','order':'updated_at.asc,id.asc','limit':'500'}
    if not force and not needs_full and cfg.get('cursor'):params['updated_at']='gte.'+cfg['cursor']
    if last:params['or']=f"(updated_at.gt.{last['updated_at']},and(updated_at.eq.{last['updated_at']},id.gt.{last['id']}))"
    rows=request(url+'/rest/v1/ysk_trips?'+urllib.parse.urlencode(params),api,s['access_token']);allrows.extend(rows)
    if len(rows)<500:break
    last=rows[-1]
   from course_setup import import_courses
   if member:import_courses(self.store,request(url+'/functions/v1/ysk-admin',api,s['access_token'],{'action':'course_setup_list'})['rows'])
   n,errors=self.import_rows(allrows,force)
   errors=send_errors+errors
   if allrows:cfg['cursor']=allrows[-1]['updated_at'];self.save(cfg)
   with self.store.conn() as c:persistent=[row[0] for row in c.execute('SELECT message FROM cloud_conflicts ORDER BY id')]
   return n,list(dict.fromkeys(errors+persistent)),True

class CloudPanel:
 def __init__(self,app,path):
  self.app=app;self.root=app.root;self.receiver=Receiver(app.store,path);self.queue=queue.Queue();self.busy=False;self.closed=False;self.account_label=''
  f=ttk.Frame(app.nb,padding=24);app.nb.add(f,text='Innlogging / sky');self.frame=f
  ttk.Label(f,text='Konto og sky',font=('Segoe UI',25,'bold')).grid(row=0,column=0,columnspan=2,sticky='w',pady=12)
  ttk.Label(f,text='Registrer i bilen, også uten dekning. Telefon og PC synkroniserer både ferdige turer og lagrede utkast.\nBruk e-post og passord fra administratoren. Skole og avdeling følger kontoen automatisk.').grid(row=1,column=0,columnspan=2,sticky='w',pady=12)
  self.fields={'url':tk.StringVar(value=DEFAULT_URL),'api':tk.StringVar(value=DEFAULT_API),'password':tk.StringVar()}
  for i,(k,label) in enumerate([('email','E-post')],start=2):
   ttk.Label(f,text=label).grid(row=i,column=0,sticky='w',padx=(0,15),pady=10);v=tk.StringVar(value='https://otuemdgmymgognzghmnu.supabase.co' if k=='url' else 'sb_publishable_9-BPAUPJ5gv_MJ1hz6ah0g_yoz3npSu' if k=='api' else '');self.fields[k]=v;ttk.Entry(f,textvariable=v,width=65,state='readonly').grid(row=i,column=1,sticky='ew')
  ttk.Button(f,text='Logg ut',command=self.logout).grid(row=6,column=1,sticky='w',pady=15)
  ttk.Button(f,text='Synkroniser nå',command=self.sync).grid(row=7,column=1,sticky='w',pady=8)
  ttk.Button(f,text='Bruk telefonens versjoner ved konflikt',command=self.force).grid(row=7,column=0,sticky='w',pady=8)
  self.status=tk.StringVar(value='Ikke koblet til. Android-appen kan fortsatt lagre turer lokalt.');ttk.Label(f,textvariable=self.status,wraplength=850).grid(row=8,column=0,columnspan=2,sticky='w',pady=15)
  ttk.Label(f,text='Automatisk sending og henting hvert 10. sekund. Uferdige turer synkroniseres også. Slettede skyturer fjernes fra klasserommet.\nEn konflikt vises her og må avklares før den turen kan oppdateres fra telefonen.\nRedigering og sletting av skyturer sendes tilbake til telefonen.\nPassord lagres ikke; innloggingsøkten beskyttes av Windows-kontoen.\nSkole og avdeling tildeles av administrator.').grid(row=9,column=0,columnspan=2,sticky='w',pady=10)
  try:
   cfg=self.receiver.load()
   if not cfg:app.nb.select(f)
   if cfg:
    for k in ['url','api','email']:self.fields[k].set(cfg[k])
    self.status.set('Tilkoblet. Venter på første henting.');self.sync()
  except Exception as e:self.status.set('Innlogging må gjøres på nytt: '+str(e))
  self.root.after(300,self.drain);self.root.after(10000,self.repeat)
 def launch(self,fn):
  if self.busy:return
  self.busy=True;self.status.set('Kobler til …')
  def work():
   try:
    result=fn()
    if self.receiver.load():
     info=self.receiver.admin('me');self.account_label=(info.get('school') or {}).get('name','')+(' · '+info['division']['name'] if info.get('division') else '')
    self.queue.put(('ok',result))
   except Exception as e:self.queue.put(('locked' if isinstance(e,LoginRequired) or isinstance(e,APIError) and e.status==401 else 'error',str(e)))
  threading.Thread(target=work,daemon=True).start()
 def connect(self):
  args=[self.fields[k].get() for k in ['url','api','email','password']];self.fields['password'].set('')
  def work():self.receiver.connect(*args);return self.receiver.sync()
  self.launch(work)
 def logout(self):
  if self.busy:return
  self.busy=True;self.status.set('Logger ut …')
  def work():self.receiver.logout();self.queue.put(('loggedout',None))
  threading.Thread(target=work,daemon=True).start()
 def force(self):
  if self.busy:return
  if messagebox.askyesno('Bruk telefonens versjoner','Erstatte PC-endringer med versjonene i skyen? En sikkerhetskopi tas først.'):
   def work():
    self.app.store.backup(self.receiver.path.parent/('før_skysynk_'+time.strftime('%Y%m%d_%H%M%S')+'.db'))
    return self.receiver.sync(force=True)
   self.launch(work)
 def sync(self):self.launch(self.receiver.sync)
 def drain(self):
  if self.closed:return
  try:
   while True:
    kind,result=self.queue.get_nowait();self.busy=False
    if kind in ('locked','loggedout'):
     self.app.lock();return
    if kind=='error':self.status.set('Venter: '+result);self.app.cloud_waiting=True
    else:
     n,errors,connected=result
     self.status.set(('Hentet '+str(n)+' nye/endrede turer. Oppdatert '+time.strftime('%H:%M:%S') if connected else 'Ikke koblet til.')+(' · '+self.account_label if connected and self.account_label else '')+ ('\n'+'\n'.join(errors[:6]) if errors else ''));
     self.app.cloud_waiting=not connected
     if connected:self.app.last_cloud_update=time.strftime('%H:%M:%S')
     self.app.refresh()
  except queue.Empty:pass
  self.root.after(300,self.drain)
 def repeat(self):
  if self.closed:return
  self.sync();self.root.after(10000,self.repeat)
