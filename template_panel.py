"""Parameter bank, immutable trip templates, dynamic forms and school course selection."""
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog,filedialog
import json,uuid,threading,queue,datetime,hashlib,time
from pathlib import Path
TYPES=['number','integer','minutes','stopwatch','rating','boolean','choice','text','fuel']
TYPE_NAMES=['Tall','Heltall','Minutter','Tidtakning','Vurdering','Ja / nei','Valgliste','Tekst','Beregnet l/mil']
class TemplatePanel:
 def __init__(self,app,receiver,data):
  self.app=app;self.receiver=receiver;self.data=Path(data);self.queue=queue.Queue();self.busy=False;self.catalog=None;self.widgets={};self.current=None;self.run=None;self.cache=None;self.starts={}
  frame=ttk.Frame(app.nb,padding=18);app.nb.add(frame,text='Turmaler / egendefinerte turer');self.frame=frame
  ttk.Label(frame,text='Turmaler og parameterbank',font=('Segoe UI',22,'bold')).pack(anchor='w')
  self.status=tk.StringVar(value='Henter skolens turmaler …');ttk.Label(frame,textvariable=self.status,wraplength=1000).pack(anchor='w',pady=8)
  tools=ttk.Frame(frame);tools.pack(fill='x')
  for label,fn in [('Hent / synkroniser',self.load),('Ny tur',self.new_run),('Registrerte turer',self.history),('Klasserom / analyse',self.classroom),('Lag papirskjema / PDF',self.paper_forms)]:ttk.Button(tools,text=label,command=fn).pack(side='left',padx=3)
  self.admin_tools=ttk.Frame(frame)
  for label,fn in [('Parameterbank',self.bank),('Endre valgt turmal',self.edit_template),('Ny egendefinert turmal',lambda:self.edit_template(True)),('Turmaler i kurs',self.course_templates)]:ttk.Button(self.admin_tools,text=label,command=fn).pack(side='left',padx=3)
  selector=ttk.Frame(frame);selector.pack(fill='x',pady=10);ttk.Label(selector,text='Turmal').pack(side='left');self.choice=tk.StringVar();self.box=ttk.Combobox(selector,textvariable=self.choice,state='readonly',width=50);self.box.pack(side='left',padx=8);self.box.bind('<<ComboboxSelected>>',lambda e:self.new_run())
  self.course_choice=tk.StringVar(value='Alle');ttk.Label(selector,text='Kurs').pack(side='left',padx=(12,3));self.course_box=ttk.Combobox(selector,textvariable=self.course_choice,state='readonly',width=22);self.course_box.pack(side='left');self.course_box.bind('<<ComboboxSelected>>',lambda e:self.filter_templates())
  self.form_canvas=tk.Canvas(frame,highlightthickness=0);sy=ttk.Scrollbar(frame,command=self.form_canvas.yview);sy.pack(side='right',fill='y');self.form_canvas.configure(yscrollcommand=sy.set);self.form_canvas.pack(fill='both',expand=True);self.form=ttk.Frame(self.form_canvas);self.form_id=self.form_canvas.create_window(0,0,window=self.form,anchor='nw');self.form.bind('<Configure>',lambda e:self.form_canvas.configure(scrollregion=self.form_canvas.bbox('all')));self.form_canvas.bind('<Configure>',lambda e:self.form_canvas.itemconfigure(self.form_id,width=e.width))
  bottom=ttk.Frame(frame);bottom.pack(fill='x',pady=8);ttk.Button(bottom,text='Lagre uferdig',command=lambda:self.save(False)).pack(side='left',padx=4);ttk.Button(bottom,text='Lagre ferdig tur',command=lambda:self.save(True)).pack(side='left',padx=4)
  ttk.Label(bottom,text='– = bevisst utelatt. Poeng gjelder bare vektede felt. Gamle turer beholder malversjonen.').pack(side='left',padx=14)
  app.root.after(200,self.poll);app.root.after(700,self.load)
 def task(self,fn,done):
  if self.busy:return
  self.busy=True
  def work():
   try:self.queue.put((True,fn(),done))
   except Exception as e:self.queue.put((False,str(e),done))
  threading.Thread(target=work,daemon=True).start()
 def poll(self):
  if not self.app.root.winfo_exists():return
  try:
   while True:
    ok,result,done=self.queue.get_nowait();self.busy=False
    if ok:done(result)
    else:self.status.set(result)
  except queue.Empty:pass
  self.app.root.after(200,self.poll)
 def load(self):
  if self.busy:return
  def work():
   result=self.receiver.admin('template_catalog');key=result['organization_id']+'|'+result['user_id'];folder=self.data/'templates'/hashlib.sha256(key.encode()).hexdigest();folder.mkdir(parents=True,exist_ok=True);(folder/'catalog.json').write_text(json.dumps(result,ensure_ascii=False));pending=folder/'pending.json'
   if pending.exists():
    try:
     request=json.loads(pending.read_text());reply=self.receiver.admin('template_run_save',**request);(folder/(reply['run']['id']+'.json')).write_text(json.dumps(reply['run'],ensure_ascii=False));pending.unlink()
    except Exception:pass
   return result,folder
  def done(result):
   self.catalog,self.cache=result;self.available_templates=self.catalog['templates'];self.box['values']=[t['definition']['name']+' · v'+str(t['revision']) for t in self.available_templates];self.course_box['values']=['Alle']+sorted(set([r['name'] for r in self.catalog['courses']]+[d['course'] for d in self.app.store.all(include_unscored=True)]))
   if self.catalog['role']=='admin':self.admin_tools.pack(fill='x',before=self.form_canvas,pady=8)
   if self.current and self.run and (self.cache/(self.run['id']+'.json')).exists():
    saved=json.loads((self.cache/(self.run['id']+'.json')).read_text())
    if saved['revision']>self.run.get('revision',0):self.run=saved;self.persist_draft()
   if not self.current and (self.cache/'draft.json').exists():
    try:
     draft=json.loads((self.cache/'draft.json').read_text());self.current=draft['template'];self.run=draft['run'];self.render(draft['payload']);self.starts=draft.get('clocks',{})
    except (ValueError,KeyError):self.current=None
   if not self.current and self.catalog['templates']:self.box.current(0);self.new_run()
   self.status.set('Skolens maler er hentet. Nye parameterturer registreres her; gamle turer finnes fortsatt i turoversikten.')
  self.task(work,done)
 def selected_template(self):
  index=self.box.current();return self.available_templates[index] if self.catalog and 0<=index<len(self.available_templates) else None
 def filter_templates(self):
  if not self.catalog:return
  assigned=next((c['template_ids'] for c in self.catalog['courses'] if c['name']==self.course_choice.get()),None)
  self.available_templates=[t for t in self.catalog['templates'] if assigned is None or t['id'] in assigned];self.box['values']=[t['definition']['name']+' · v'+str(t['revision']) for t in self.available_templates]
  self.choice.set('')
  if self.available_templates:self.box.current(0);self.new_run()
 def capture(self,convert=True):
  if not self.current:return None
  values={}
  for p in self.current['definition']['parameters']:
   raw=self.widgets[p['id']].get().strip()
   if raw in ('','-'):values[p['id']]=None if raw=='' else '-'
   elif p['type'] in ('minutes','stopwatch'):
    from speed_preview import duration_minutes
    values[p['id']]=duration_minutes(raw) if convert else raw
   elif p['type'] in ('number','integer'):values[p['id']]=float(raw.replace(',','.')) if convert else raw
   elif p['type']=='boolean':values[p['id']]=raw=='Ja'
   elif p['type']!='fuel':values[p['id']]=raw
  from speed_preview import calculated_speed
  if convert and 'average_speed' in values and values['average_speed'] is None:
   values['average_speed']=calculated_speed(values.get('km'),values.get('minutes'))
  return dict(driver=self.widgets['@driver'].get(),course=self.widgets['@course'].get(),vehicle=self.widgets['@vehicle'].get(),date=self.widgets['@date'].get(),complete=False,values=values)
 def persist_draft(self):
  if self.cache and self.current:
   try:(self.cache/'draft.json').write_text(json.dumps(dict(template=self.current,run=self.run,payload=self.capture(False),clocks=self.starts),ensure_ascii=False))
   except (ValueError,KeyError,tk.TclError):pass
 def new_run(self):
  if self.cache and (self.cache/'pending.json').exists():
   self.status.set('En tur venter på sending. Fortsett / rett utkastet eller trykk Hent / synkroniser.');return
  self.persist_draft();template=self.selected_template()
  if not template:return
  self.current=template;self.run={'id':str(uuid.uuid4()),'revision':0};self.render({})
 def render(self,payload):
  for w in self.form.winfo_children():w.destroy()
  self.widgets={};self.starts={};self.form.columnconfigure(1,weight=1)
  fields=[('@driver','Elev','text'),('@course','Kurs','text'),('@vehicle','Bil','text'),('@date','Dato','text')]
  parameters=self.current['definition']['parameters'];fields+=[(p['id'],p['label']+(' *' if p['required'] else '')+(' ('+p['unit']+')' if p['unit'] else ''),p['type']) for p in parameters]
  for row,(id,label,type_) in enumerate(fields):
   ttk.Label(self.form,text=label).grid(row=row,column=0,sticky='w',padx=8,pady=7);var=tk.StringVar();self.widgets[id]=var
   v=payload.get(id[1:],'') if id.startswith('@') else payload.get('values',{}).get(id,'')
   if id=='@course' and not v:v=self.course_choice.get() if self.course_choice.get()!='Alle' else self.app.filters['course'][0].get() if self.app.filters['course'][0].get()!='Alle' else ''
   if id=='@date' and not v:v=datetime.date.today().isoformat()
   if type_=='boolean' and isinstance(v,bool):v='Ja' if v else 'Nei'
   var.set('' if v is None else v);p=next((p for p in parameters if p['id']==id),{})
   options=['','Bra','Middels','Svak','-'] if type_=='rating' else ['','Ja','Nei','-'] if type_=='boolean' else ['']+p.get('options',[])+['-'] if type_=='choice' else None
   widget=ttk.Combobox(self.form,textvariable=var,values=options,state='readonly') if options else ttk.Entry(self.form,textvariable=var,state='readonly' if type_=='fuel' else 'normal');widget.grid(row=row,column=1,sticky='ew',padx=8,pady=7)
   if type_=='stopwatch':ttk.Button(self.form,text='Start / stopp',command=lambda id=id:self.stopwatch(id)).grid(row=row,column=2)
   var.trace_add('write',lambda *args:self.persist_draft())
  if 'fuel' in self.widgets:
   def calculate(*args):
    try:self.widgets['fuel'].set(f"{10*float(self.widgets['liters'].get().replace(',','.'))/float(self.widgets['km'].get().replace(',','.')):.3f}")
    except (ValueError,ZeroDivisionError,KeyError):self.widgets['fuel'].set('')
   for id in ('km','liters'):
    if id in self.widgets:self.widgets[id].trace_add('write',calculate)
   calculate()
  if 'average_speed' in self.widgets:
   from speed_preview import calculated_speed
   result=tk.StringVar();ttk.Label(self.form,textvariable=result,foreground='#16803c').grid(row=len(fields),column=0,columnspan=3,sticky='w',padx=8,pady=6)
   def show_speed(*args):
    value=calculated_speed(self.widgets['km'].get() if 'km' in self.widgets else '',self.widgets['minutes'].get() if 'minutes' in self.widgets else '',self.widgets['average_speed'].get())
    result.set(f'Beregnet gjennomsnittsfart: {value:.1f} km/t (inkludert stopp)' if value is not None else '')
   for key in ('km','minutes','average_speed'):
    if key in self.widgets:self.widgets[key].trace_add('write',show_speed)
   show_speed()
 def paper_forms(self):
  if not self.catalog:return
  def work():
   rows=[];offset=0
   while True:
    page=self.receiver.admin('template_runs',offset=offset)['runs'];rows+=page
    if len(page)<100:break
    offset+=100
   return rows
  def done(rows):
   from paper_forms import FormsDialog
   FormsDialog(self.app,self.catalog,self.cache,rows)
  self.task(work,done)
 def stopwatch(self,id):
  if id in self.starts:
   base,start=self.starts.pop(id);self.widgets[id].set(f'{base+(time.time()-start)/60:.2f}')
  else:
   try:base=float(self.widgets[id].get().replace(',','.'))
   except ValueError:base=0
   self.starts[id]=(base,time.time());self.status.set('Tidtakning startet. Trykk igjen for å registrere minutter.')
 def save(self,complete):
  if self.busy or not self.current:return
  for id in list(self.starts):self.stopwatch(id)
  try:
   payload=self.capture();payload['complete']=complete
   if not all(payload[k].strip() for k in ('driver','course','vehicle','date')):raise ValueError('Fyll inn elev, kurs, bil og dato.')
   request=dict(id=self.run['id'],expected_revision=self.run.get('revision',0),template_id=self.current['id'],template_revision=self.current['revision'],payload=payload)
   if (self.cache/'pending.json').exists() and json.loads((self.cache/'pending.json').read_text())['id']!=self.run['id']:raise ValueError('En tidligere tur venter på sending. Trykk Hent / synkroniser først.')
   (self.cache/'pending.json').write_text(json.dumps(request,ensure_ascii=False))
  except Exception as e:messagebox.showerror('Turmal',str(e));return
  def work():
   r=self.receiver.admin('template_run_save',**request);(self.cache/(r['run']['id']+'.json')).write_text(json.dumps(r['run'],ensure_ascii=False));(self.cache/'pending.json').unlink();return r
  def done(r):self.run=r['run'];self.status.set(r['message']+(' Poeng: '+str(r['run']['payload']['score']) if r['run']['payload']['score'] is not None else ' Ingen samlet score.'));self.persist_draft()
  self.task(work,done)
 def history(self):
  def work():
   result=[]
   for offset in range(0,100001,100):
    page=self.receiver.admin('template_runs',offset=offset)['runs'];result+=page
    if len(page)<100:break
   return result
  def done(rows):
   win=tk.Toplevel(self.app.root);win.title('Parameterturer · samme malversjon sammenlignes');win.geometry('1050x650');table=ttk.Treeview(win,columns=('student','course','vehicle','template','version','score'),show='headings');table.pack(fill='both',expand=True)
   for k,n in [('student','Elev'),('course','Kurs'),('vehicle','Bil'),('template','Turmal'),('version','Versjon'),('score','Poeng')]:table.heading(k,text=n)
   for i,r in enumerate(rows):p=r['payload'];table.insert('','end',iid=str(i),values=[p['driver'],p['course'],p['vehicle'],r['snapshot']['name'],r['template_revision'],p['score'] if p['score'] is not None else 'Uferdig / uten score'])
   def open_():
    ids=table.selection()
    if not ids:return
    r=rows[int(ids[0])];self.current={'id':r['template_id'],'revision':r['template_revision'],'definition':r['snapshot']};self.run=r;self.render(r['payload']);win.destroy();self.app.nb.select(self.frame)
   table.bind('<Double-1>',lambda e:open_());ttk.Button(win,text='Åpne / endre valgt tur',command=open_).pack(pady=6)
  self.task(work,done)
 def bank(self):
  if not self.catalog:return
  win=tk.Toplevel(self.app.root);win.title('Parameterbank');win.geometry('850x650');table=ttk.Treeview(win,columns=('name','type','unit'),show='headings');table.pack(fill='both',expand=True)
  for k,n in [('name','Parameter'),('type','Type'),('unit','Enhet')]:table.heading(k,text=n)
  for i,p in enumerate(self.catalog['parameters']):table.insert('','end',iid=str(i),values=[p['label'],TYPE_NAMES[TYPES.index(p['type'])],p['unit']])
  ttk.Button(win,text='Ny parameter',command=lambda:self.parameter_editor(None,win)).pack(side='left',padx=8,pady=8)
  ttk.Button(win,text='Endre valgt parameter',command=lambda:self.parameter_editor(self.catalog['parameters'][int(table.selection()[0])],win) if table.selection() else None).pack(side='left',padx=8,pady=8)
 def parameter_editor(self,p,parent):
  p=p or {'id':'p_'+uuid.uuid4().hex,'label':'','type':'number'};win=tk.Toplevel(parent);win.title('Parameter');vars={}
  definitions=[('label','Navn',p.get('label','')),('type','Felttype',TYPE_NAMES[TYPES.index(p.get('type','number'))]),('unit','Måleenhet',p.get('unit','')),('weight','Poengvekt (0 = ingen)',p.get('weight',0)),('direction','Poengretning',{'none':'Ingen','low':'Lavere er bedre','high':'Høyere er bedre'}[p.get('direction','none')]),('min','Nedre grense',p.get('min')),('max','Øvre grense',p.get('max')),('options','Valg, adskilt med ;',';'.join(p.get('options',[])))]
  for row,(key,label,val) in enumerate(definitions):
   ttk.Label(win,text=label).grid(row=row,column=0,padx=8,pady=6);var=tk.StringVar(value='' if val is None else str(val));vars[key]=var
   widget=ttk.Combobox(win,textvariable=var,values=TYPE_NAMES if key=='type' else ['Ingen','Lavere er bedre','Høyere er bedre'],state='readonly') if key in ('type','direction') else ttk.Entry(win,textvariable=var,width=40);widget.grid(row=row,column=1,padx=8,pady=6)
  required=tk.BooleanVar(value=p.get('required',False));graph=tk.BooleanVar(value=p.get('graph',False));ttk.Checkbutton(win,text='Obligatorisk',variable=required).grid(row=8,column=0);ttk.Checkbutton(win,text='Vis i grafer',variable=graph).grid(row=8,column=1)
  def save():
   try:
    parameter=dict(p,id=p['id'],label=vars['label'].get(),type=TYPES[TYPE_NAMES.index(vars['type'].get())],unit=vars['unit'].get(),weight=float(vars['weight'].get()),direction={'Ingen':'none','Lavere er bedre':'low','Høyere er bedre':'high'}[vars['direction'].get()],min=float(vars['min'].get()) if vars['min'].get() else None,max=float(vars['max'].get()) if vars['max'].get() else None,options=[s.strip() for s in vars['options'].get().split(';') if s.strip()],required=required.get(),graph=graph.get())
   except ValueError:messagebox.showerror('Parameter','Kontroller tallene.');return
   self.task(lambda:self.receiver.admin('parameter_save',parameter=parameter),lambda r:(win.destroy(),parent.destroy(),self.load()))
  ttk.Button(win,text='Lagre parameter',command=save).grid(row=9,column=1,pady=10)
 def edit_template(self,new=False):
  if not self.catalog:return
  old=self.selected_template()
  if not old:return
  win=tk.Toplevel(self.app.root);win.title('Egendefinert turmal' if new else 'Endre turmal');win.geometry('950x650');name=tk.StringVar(value='Ny turmal' if new else old['definition']['name']);ttk.Entry(win,textvariable=name,width=55).pack(pady=8);ttk.Label(win,text='Velg parametre. Dobbeltklikk et felt for å endre krav, grenser og vekting for denne malen.').pack()
  parameters=[] if new else json.loads(json.dumps(old['definition']['parameters']));table=ttk.Treeview(win,columns=('name','required','weight'),show='headings');table.pack(fill='both',expand=True)
  for k,n in [('name','Parameter'),('required','Obligatorisk'),('weight','Poengvekt')]:table.heading(k,text=n)
  def refresh():
   table.delete(*table.get_children())
   for i,p in enumerate(parameters):table.insert('','end',iid=str(i),values=[p['label'],'Ja' if p['required'] else 'Nei',p['weight']])
  bank_choice=tk.StringVar();bank_box=ttk.Combobox(win,textvariable=bank_choice,state='readonly',values=[p['label'] for p in self.catalog['parameters']],width=40);bank_box.pack(pady=5)
  def add():
   if bank_box.current()<0:return
   p=self.catalog['parameters'][bank_box.current()]
   if all(q['id']!=p['id'] for q in parameters):parameters.append(dict(p));refresh()
  def remove():
   if table.selection():parameters.pop(int(table.selection()[0]));refresh()
  def edit(e=None):
   if not table.selection():return
   p=parameters[int(table.selection()[0])];editwin=tk.Toplevel(win);editwin.title(p['label']);required=tk.BooleanVar(value=p['required']);ttk.Checkbutton(editwin,text='Obligatorisk',variable=required).pack();fields={}
   for k,label in [('weight','Poengvekt'),('direction','none / low / high'),('min','Min'),('max','Maks')]:ttk.Label(editwin,text=label).pack();v=tk.StringVar(value='' if p[k] is None else str(p[k]));fields[k]=v;ttk.Entry(editwin,textvariable=v).pack()
   def done():
    try:p.update(required=required.get(),weight=float(fields['weight'].get()),direction=fields['direction'].get(),min=float(fields['min'].get()) if fields['min'].get() else None,max=float(fields['max'].get()) if fields['max'].get() else None);refresh();editwin.destroy()
    except ValueError:messagebox.showerror('Turmal','Kontroller tallene.')
   ttk.Button(editwin,text='Bruk',command=done).pack(pady=8)
  table.bind('<Double-1>',edit);buttons=ttk.Frame(win);buttons.pack(fill='x')
  for label,fn in [('Legg til',add),('Fjern valgt',remove),('Endre felt',edit)]:ttk.Button(buttons,text=label,command=fn).pack(side='left',padx=5)
  def save():
   definition=dict(name=name.get(),base_trip=None if new else old['definition'].get('base_trip'),parameters=parameters)
   self.task(lambda:self.receiver.admin('template_save',id=str(uuid.uuid4()) if new else old['id'],expected_revision=0 if new else old['revision'],definition=definition),lambda r:(win.destroy(),self.load()))
  ttk.Button(buttons,text='Lagre ny malversjon',command=save).pack(side='right',padx=5);refresh()
 def course_templates(self):
  if not self.catalog:return
  win=tk.Toplevel(self.app.root);win.title('Turmaler i kurs');name=tk.StringVar();ttk.Label(win,text='Kursnavn').pack();ttk.Entry(win,textvariable=name,width=45).pack(pady=8);variables=[]
  for t in self.catalog['templates']:v=tk.BooleanVar();variables.append((t,v));ttk.Checkbutton(win,text=t['definition']['name'],variable=v).pack(anchor='w',padx=12)
  def changed(*args):
   saved=next((r['template_ids'] for r in self.catalog['courses'] if r['name']==name.get()),[])
   for t,v in variables:v.set(t['id'] in saved)
  name.trace_add('write',changed)
  def save():self.task(lambda:self.receiver.admin('template_course_save',name=name.get(),template_ids=[t['id'] for t,v in variables if v.get()]),lambda r:(win.destroy(),self.load()))
  ttk.Button(win,text='Lagre kursvalg',command=save).pack(pady=10)
 def classroom(self,rows=None):
  if rows is None:
   def work():
    result=[]
    for offset in range(0,100001,100):
     page=self.receiver.admin('template_runs',offset=offset)['runs'];result+=page
     if len(page)<100:break
    return result
   self.task(work,lambda result:self.classroom(result));return
  from template_analysis import comparable,numeric,percent
  win=tk.Toplevel(self.app.root);win.title('Parameterturer · klasserom');win.geometry('1300x850');split=ttk.PanedWindow(win,orient='horizontal');split.pack(fill='both',expand=True);left=ttk.Frame(split);right=ttk.Frame(split);split.add(left,weight=1);split.add(right,weight=1)
  table=ttk.Treeview(left,columns=('driver','vehicle','template','revision','score'),show='headings');table.pack(fill='both',expand=True)
  for k,n in [('driver','Elev'),('vehicle','Bil'),('template','Turmal'),('revision','Versjon'),('score','Poeng')]:table.heading(k,text=n);table.column(k,width=110)
  for i,r in enumerate(rows):p=r['payload'];table.insert('','end',iid=str(i),values=[p['driver'],p['vehicle'],r['snapshot']['name'],r['template_revision'],'—' if p['score'] is None else p['score']])
  canvas=tk.Canvas(right,bg='#102b3e',highlightthickness=0);scroll=ttk.Scrollbar(right,command=canvas.yview);scroll.pack(side='right',fill='y');canvas.configure(yscrollcommand=scroll.set);canvas.pack(fill='both',expand=True)
  def draw(e=None):
   selected=table.selection()
   if not selected:return
   run=rows[int(selected[0])];history=comparable(rows,run);canvas.delete('all');w=max(480,canvas.winfo_width());y=15
   def text(x,y,s,color='#edf5fb',size=12):canvas.create_text(x,y,text=s,anchor='nw',fill=color,font=('Segoe UI',size),width=w-30)
   text(15,y,run['payload']['driver']+' · '+run['payload']['vehicle'],size=20);y+=36;text(15,y,'Sammenligner samme kurs, malversjon, parametre og vekting.');y+=28
   for p in run['snapshot']['parameters']:
    vals=[r['payload']['values'].get(p['id']) for r in history];text(15,y,p['label']+(' · '+p['unit'] if p['unit'] else ''));y+=28
    numbers=[v for v in vals if numeric(v)]
    if p['graph'] and numbers:
     low=min(numbers+[0]);high=max(numbers+[1]);delta=percent(vals[0],vals[-1]) if len(vals)>1 else None
     if delta is not None:text(w-210,y-28,f'{delta:+.1f}% fra første',color='#32d4bf')
     top=y+18;bottom=y+100;last=None
     for i,(r,v) in enumerate(zip(history,vals)):
      px=40+i*(w-90)/max(1,len(history)-1);text(px-12,bottom+8,str(r['snapshot'].get('base_trip') or i+1),size=10)
      if not numeric(v):last=None;continue
      py=bottom-(v-low)/(high-low)*(bottom-top)
      if last:canvas.create_line(*last,px,py,fill='#32d4bf',width=2)
      canvas.create_oval(px-4,py-4,px+4,py+4,fill='#32d4bf',outline='');text(px-12,py-19,f'{v:.2f}',size=10);last=(px,py)
     y=bottom+40
    else:text(15,y,' / '.join('—' if v is None else str(v) for v in vals));y+=32
   canvas.configure(scrollregion=(0,0,w,y))
  table.bind('<<TreeviewSelect>>',draw);canvas.bind('<Configure>',draw)
  if rows:table.selection_set('0')
