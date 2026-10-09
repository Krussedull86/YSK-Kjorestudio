"""Feedback submission and the school administrator's inbox."""
import tkinter as tk
from tkinter import ttk,messagebox
import threading,queue,json,uuid,platform
from version import VERSION,BUILD
KINDS={'Tilbakemelding / forslag':'suggestion','Feilmelding':'bug'}
STATES={'Ny':'open','Under behandling':'working','Ferdig':'resolved'}
DELIVERY={'pending':'Venter','sending':'Sender','sent':'Sendt','failed':'Feilet','off':'Ikke konfigurert'}
class FeedbackPanel:
 def __init__(self,app,receiver,data):
  self.app=app;self.receiver=receiver;self.file=data/'feedback_draft.json';self.queue=queue.Queue();self.busy=False;self.rows=[];self.offset=0
  f=ttk.Frame(app.nb,padding=20);app.nb.add(f,text='Tilbakemelding');self.frame=f
  ttk.Label(f,text='Tilbakemelding / forslag eller feilmelding',font=('Segoe UI',22,'bold')).pack(anchor='w',pady=8)
  self.kind=tk.StringVar(value=next(iter(KINDS)));self.kind_box=ttk.Combobox(f,textvariable=self.kind,values=list(KINDS),state='readonly',width=40);self.kind_box.pack(anchor='w',pady=6)
  ttk.Label(f,text='Tittel (maks 120 tegn)').pack(anchor='w');self.title=tk.StringVar();self.title_entry=ttk.Entry(f,textvariable=self.title);self.title_entry.pack(fill='x',pady=6)
  ttk.Label(f,text='Beskriv forslaget eller hva som skjedde. Ved feil: hva gjorde du, og hva forventet du? (maks 4000 tegn)').pack(anchor='w');self.body=tk.Text(f,height=10,wrap='word');self.body.pack(fill='both',expand=True,pady=8)
  self.id=str(uuid.uuid4())
  try:
   d=json.loads(self.file.read_text());self.id=d['id'];self.kind.set(d.get('kind',self.kind.get()));self.title.set(d.get('title',''));self.body.insert('1.0',d.get('body',''))
  except (OSError,ValueError,KeyError):pass
  self.title.trace_add('write',lambda *a:self.draft());self.kind.trace_add('write',lambda *a:self.draft());self.body.bind('<KeyRelease>',lambda e:self.draft())
  ttk.Button(f,text='Send tilbakemelding',command=self.submit).pack(anchor='w',pady=5)
  ttk.Label(f,text='Navn, programversjon og Windows-versjon følger med. Meldingen lagres i skolens adminpanel og sendes til Discord hvis admin har konfigurert det.').pack(anchor='w')
  self.status=tk.StringVar();ttk.Label(f,textvariable=self.status,wraplength=950).pack(anchor='w',pady=6)
  ttk.Button(app.admin_panel.frame,text='Tilbakemeldinger / feilmeldinger',command=self.inbox).grid(row=0,column=2,sticky='e',pady=6)
  app.root.after(150,self.drain)
 def draft(self):
  if self.busy:return
  try:self.file.write_text(json.dumps(dict(id=self.id,kind=self.kind.get(),title=self.title.get(),body=self.body.get('1.0','end-1c')),ensure_ascii=False),encoding='utf-8')
  except OSError:pass
 def run(self,fn,callback):
  if self.busy:return
  self.busy=True;self.status.set('Oppdaterer …')
  def work():
   try:self.queue.put((True,fn(),callback))
   except Exception as e:self.queue.put((False,str(e),None))
  threading.Thread(target=work,daemon=True).start()
 def drain(self):
  try:
   while True:
    ok,result,callback=self.queue.get_nowait();self.busy=False;self.body.configure(state='normal');self.title_entry.configure(state='normal');self.kind_box.configure(state='readonly')
    if ok:callback(result);self.status.set(result.get('message','Oppdatert') if isinstance(result,dict) else 'Oppdatert')
    else:self.status.set(result);messagebox.showerror('Tilbakemelding',result)
  except queue.Empty:pass
  self.app.root.after(150,self.drain)
 def submit(self):
  if self.busy:return
  title=self.title.get().strip();body=self.body.get('1.0','end-1c').strip()
  if not 1<=len(title)<=120 or not 1<=len(body)<=4000:return messagebox.showinfo('Kontroller meldingen','Tittel: 1–120 tegn. Melding: 1–4000 tegn.')
  self.draft();payload=dict(id=self.id,kind=KINDS[self.kind.get()],title=title,body=body,platform='windows',version=f'{VERSION} / B{BUILD}',device=platform.platform()[:200]);self.body.configure(state='disabled');self.title_entry.configure(state='disabled');self.kind_box.configure(state='disabled')
  def sent(r):
   self.body.configure(state='normal');self.title.set('');self.body.delete('1.0','end');self.id=str(uuid.uuid4());self.draft();messagebox.showinfo('Sendt',r['message'])
  self.run(lambda:self.receiver.admin('feedback_submit',**payload),sent)
 def inbox(self):
  if hasattr(self,'window') and self.window.winfo_exists():self.window.lift();return
  self.window=tk.Toplevel(self.app.root);self.window.title('Admin · Tilbakemeldinger / feilmeldinger');self.window.geometry('1100x700');f=ttk.Frame(self.window,padding=14);f.pack(fill='both',expand=True)
  controls=ttk.Frame(f);controls.pack(fill='x');ttk.Button(controls,text='Hent meldinger',command=self.load).pack(side='left');ttk.Button(controls,text='Discord · 2 webhooks',command=self.hooks).pack(side='left',padx=8)
  self.filter=tk.StringVar(value='Alle');box=ttk.Combobox(controls,textvariable=self.filter,values=['Alle',*KINDS],state='readonly');box.pack(side='left');box.bind('<<ComboboxSelected>>',lambda e:self.render())
  ttk.Button(controls,text='← Forrige',command=lambda:self.page(-100)).pack(side='right');ttk.Button(controls,text='Neste →',command=lambda:self.page(100)).pack(side='right')
  self.table=self.app.tree(f,['Type','Tittel','Fra','Program','Status','Discord','Dato']);self.table.bind('<<TreeviewSelect>>',lambda e:self.details())
  self.detail=tk.Text(f,height=8,wrap='word',state='disabled');self.detail.pack(fill='x',pady=6)
  actions=ttk.Frame(f);actions.pack(fill='x')
  for label,state in STATES.items():ttk.Button(actions,text=label,command=lambda state=state:self.change('feedback_status',status=state)).pack(side='left',padx=4)
  ttk.Button(actions,text='Prøv Discord på nytt',command=lambda:self.change('feedback_retry')).pack(side='left',padx=8);self.load()
 def page(self,step):self.offset=max(0,self.offset+step);self.load()
 def load(self):self.run(lambda:self.receiver.admin('feedback_list',offset=self.offset),self.loaded)
 def loaded(self,r):self.rows=r['rows'];self.render()
 def render(self):
  if not self.window.winfo_exists():return
  self.table.delete(*self.table.get_children())
  for r in self.rows:
   label=next(k for k,v in KINDS.items() if v==r['kind'])
   if self.filter.get() not in ('Alle',label):continue
   self.table.insert('','end',iid=r['id'],values=[label,r['title'],r['author'],r['platform']+' '+r['version'],next(k for k,v in STATES.items() if v==r['status']),DELIVERY.get(r['delivery'],r['delivery']),r['created_at'][:19]])
 def details(self):
  ids=self.table.selection()
  if not ids:return
  r=next(r for r in self.rows if r['id']==ids[0]);self.detail.configure(state='normal');self.detail.delete('1.0','end');self.detail.insert('1.0',r['body']+'\n\nEnhet: '+r['device']+'\n'+r['delivery_error']);self.detail.configure(state='disabled')
 def change(self,action,**body):
  ids=self.table.selection()
  if ids:self.run(lambda:self.receiver.admin(action,id=ids[0],**body),lambda r:self.load())
 def hooks(self):self.run(lambda:self.receiver.admin('feedback_hooks_get'),self.hooks_dialog)
 def hooks_dialog(self,r):
  if not self.window.winfo_exists():return
  w=tk.Toplevel(self.window);w.title('Discord-webhooks · egen skole');entries={};disable={}
  for label,kind in KINDS.items():
   enabled=next(h['enabled'] for h in r['hooks'] if h['kind']==kind);ttk.Label(w,text=label+(' · konfigurert' if enabled else ' · ikke konfigurert')).pack(anchor='w',padx=15,pady=8);e=ttk.Entry(w,show='•',width=75);e.pack(padx=15);entries[kind]=e;v=tk.BooleanVar();disable[kind]=v;ttk.Checkbutton(w,text='Deaktiver denne webhooken',variable=v).pack(anchor='w',padx=15)
  ttk.Label(w,text='Lim inn ny Discord-webhook. Tomt felt beholder eksisterende.').pack(padx=15,pady=8)
  def save():
   updates=[(k,'' if disable[k].get() else e.get().strip()) for k,e in entries.items() if disable[k].get() or e.get().strip()]
   def work():
    for kind,url in updates:self.receiver.admin('feedback_hooks_save',kind=kind,url=url)
    return {'message':'Webhook-innstillinger lagret.'}
   self.run(work,lambda r:w.destroy() if w.winfo_exists() else None)
  ttk.Button(w,text='Lagre',command=save).pack(pady=12)
