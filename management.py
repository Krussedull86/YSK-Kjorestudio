"""School administration. All writes use the authenticated server transaction."""
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
import threading,queue,time
from cloud_sync import fingerprint

class ManagementPanel:
 def __init__(self,app,receiver):
  self.app=app;self.receiver=receiver;self.queue=queue.Queue();self.busy=False;self.rows=[];self.role='teacher';self.items={}
  self.frame=ttk.Frame(app.nb,padding=24);app.nb.add(self.frame,text='Turer, kurs og biler')
  ttk.Label(self.frame,text='Turer, kurs og biler',font=('Segoe UI',25,'bold')).pack(anchor='w',pady=10)
  ttk.Label(self.frame,text='Lærere administrerer egne turer. Admin administrerer alle skolens turer, kurs og biler.\nSlettede turer beholdes i papirkurven og tas ut av rangeringen.').pack(anchor='w',pady=8)
  nav=ttk.Frame(self.frame);nav.pack(fill='x',pady=12)
  self.kind=tk.StringVar(value='Turer')
  for label in ['Turer','Kurs','Biler','Papirkurv']:
   ttk.Radiobutton(nav,text=label,variable=self.kind,value=label,command=self.render).pack(side='left',padx=12)
  ttk.Button(nav,text='Hent fra sky',command=self.load).pack(side='right')
  self.table=app.tree(self.frame,['Navn / sjåfør','Kurs','Bil','Tur / antall','Dato','Lærer'])
  self.table.bind('<Double-1>',lambda e:self.edit())
  actions=ttk.Frame(self.frame);actions.pack(fill='x',pady=12)
  ttk.Button(actions,text='Rediger valgt',style='Accent.TButton',command=self.edit).pack(side='left',padx=6)
  ttk.Button(actions,text='Slett valgt …',command=self.delete).pack(side='left',padx=6)
  ttk.Button(actions,text='Gjenopprett fra papirkurv',command=self.restore).pack(side='left',padx=6)
  self.status=tk.StringVar(value='Logg inn under Telefon / sky og trykk Hent fra sky.')
  ttk.Label(self.frame,textvariable=self.status,wraplength=1000).pack(anchor='w',pady=8)
  app.root.after(200,self.drain)
 def run(self,fn,callback=None):
  if self.busy:messagebox.showinfo('Venter','En handling pågår. Vent til den er ferdig.');return
  self.busy=True;self.status.set('Oppdaterer …')
  def work():
   try:self.queue.put((True,fn(),callback))
   except Exception as e:self.queue.put((False,str(e),None))
  threading.Thread(target=work,daemon=True).start()
 def fetch(self):
  me=self.receiver.admin('me')['member'];rows=self.receiver.trip_list();return me,rows
 def load(self):self.run(self.fetch,self.loaded)
 def loaded(self,result):
  me,self.rows=result;self.role=me['role'];self.render()
  self.status.set(('Administrator' if self.role=='admin' else 'Lærer')+' · '+str(len(self.rows))+' turer, inkludert papirkurven.')
 def render(self):
  self.table.delete(*self.table.get_children());self.items={};kind=self.kind.get()
  if kind in ['Kurs','Biler']:
   key='course' if kind=='Kurs' else 'vehicle';groups={}
   for r in self.rows:
    if not r.get('deleted_at'):groups.setdefault(r['payload'][key],[]).append(r)
   for i,(name,rows) in enumerate(sorted(groups.items())):
    ident=str(i);self.items[ident]=(key,name,rows);self.table.insert('','end',iid=ident,values=[name,'','',str(len(rows))+' turer','',''])
  else:
   for r in self.rows:
    if bool(r.get('deleted_at'))!=(kind=='Papirkurv'):continue
    p=r['payload'];self.items[r['id']]=r
    self.table.insert('','end',iid=r['id'],values=[p['driver'],p['course'],p['vehicle'],p['trip'],p.get('date',''),p.get('teacher','')])
 def selected(self):
  ids=self.table.selection();return self.items.get(ids[0]) if ids else None
 def edit(self):
  item=self.selected()
  if not item:return
  if isinstance(item,tuple):
   if self.role!='admin':messagebox.showerror('Tilgang','Bare admin kan endre kurs og biler.');return
   key,name,rows=item;new=simpledialog.askstring('Endre navn',f'Nytt navn på {name} ({len(rows)} turer):',initialvalue=name,parent=self.app.root)
   if new and new.strip()!=name:self.action('catalog_rename',kind=key,name=name,new_name=new.strip())
  elif item.get('deleted_at'):messagebox.showinfo('Papirkurv','Gjenopprett turen før du redigerer den.')
  else:
   # The selected cloud version is the starting point for this explicit edit.
   local=next((r for r in self.app.store.all() if r['id']==item['id']),None)
   if local and fingerprint(local)!=fingerprint(item['payload']):self.app.store.backup(self.receiver.path.parent/('før_skyredigering_'+time.strftime('%Y%m%d_%H%M%S')+'.db'))
   self.receiver.import_rows([item],force=True);self.app.refresh();self.app.open_trip(item['payload'])
   self.app.edit_revision=item['revision']
 def delete(self):
  item=self.selected()
  if not item:return
  if isinstance(item,tuple):
   if self.role!='admin':messagebox.showerror('Tilgang','Bare admin kan slette kurs og biler.');return
   key,name,rows=item
   if messagebox.askyesno('Flytt til papirkurv',f'Slette {name} og flytte ALLE {len(rows)} tilhørende turer til papirkurven?'):
    self.action('catalog_delete',kind=key,name=name)
  elif not item.get('deleted_at') and messagebox.askyesno('Slett tur','Flytte denne turen til papirkurven på telefon og PC?'):
   self.action('trip_delete',id=item['id'],expected_revision=item['revision'])
 def restore(self):
  item=self.selected()
  if isinstance(item,dict) and item.get('deleted_at'):self.action('trip_restore',id=item['id'],expected_revision=item['revision'])
 def action(self,action,**body):
  def work():
   result=self.receiver.admin(action,**body);self.receiver.sync();return result,self.fetch()
  def done(result):
   response,data=result;self.loaded(data);self.app.refresh();self.status.set(response.get('message','Utført'))
  self.run(work,done)
 def save(self,d,expected_revision=''):
  def done(result):self.app.reset();self.app.refresh();messagebox.showinfo('Lagret','Turen er lagret i skyen og synkroniseres til telefonen.')
  self.run(lambda:self.receiver.save_trip(d,expected_revision),done)
 def drain(self):
  if not self.app.root.winfo_exists():return
  try:
   while True:
    ok,result,callback=self.queue.get_nowait();self.busy=False
    if ok:
     self.status.set('Oppdatert.')
     if callback:callback(result)
    else:self.status.set(result);messagebox.showerror('Kunne ikke oppdatere',result)
  except queue.Empty:pass
  self.app.root.after(200,self.drain)
