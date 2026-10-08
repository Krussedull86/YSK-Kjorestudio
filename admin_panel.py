import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
import threading,queue
class AdminPanel:
 def __init__(self,app,receiver):
  self.app=app;self.receiver=receiver;self.root=app.root;self.queue=queue.Queue();self.busy=False;self.members=[];self.role=None;self.schools=[];self.divisions=[]
  self.frame=ttk.Frame(app.nb,padding=22);app.nb.add(self.frame,text='Admin / lærere')
  ttk.Label(self.frame,text='Skoler, avdelinger og lærere',font=('Segoe UI',25,'bold')).grid(row=0,column=0,columnspan=3,sticky='w',pady=12)
  ttk.Label(self.frame,text='Hver lærer bruker egen innlogging. Skolens turer samles i klasserommet.\nBare administrator kan opprette eller deaktivere lærerkontoer.\nVed skolebytte beholdes gamle turer i opprinnelig skole. Lokal lagring må holdes separat.').grid(row=1,column=0,columnspan=3,sticky='w',pady=8)
  self.status=tk.StringVar(value='Logg inn under Innlogging / sky, og hent lærere.');ttk.Label(self.frame,textvariable=self.status,wraplength=950).grid(row=2,column=0,columnspan=3,sticky='w',pady=10)
  ttk.Button(self.frame,text='Hent min rolle / lærere',command=lambda:self.run('list')).grid(row=3,column=0,sticky='w',pady=10)
  tools=ttk.Frame(self.frame);tools.grid(row=3,column=1,columnspan=2,sticky='w')
  ttk.Button(tools,text='Ny skole',command=self.new_school).pack(side='left',padx=4)
  ttk.Button(tools,text='Endre skolenavn',command=self.rename_school).pack(side='left',padx=4)
  ttk.Button(tools,text='Ny avdeling',command=self.new_division).pack(side='left',padx=4)
  ttk.Button(tools,text='Endre avdelingsnavn',command=self.rename_division).pack(side='left',padx=4)
  self.fields={}
  for row,(key,label) in enumerate([('name','Lærerens navn'),('email','E-post'),('password','Startpassord (minst 12 tegn)'),('role','Rolle')],4):
   ttk.Label(self.frame,text=label).grid(row=row,column=0,sticky='w',pady=8);var=tk.StringVar(value='teacher' if key=='role' else '');self.fields[key]=var
   widget=ttk.Combobox(self.frame,textvariable=var,values=['teacher','admin'],state='readonly') if key=='role' else ttk.Entry(self.frame,textvariable=var,width=44,show='•' if key=='password' else '')
   widget.grid(row=row,column=1,sticky='ew',pady=8)
  selection=ttk.Frame(self.frame);selection.grid(row=8,column=0,columnspan=3,sticky='ew')
  ttk.Label(selection,text='Skole').pack(side='left');self.school=tk.StringVar();self.school_box=ttk.Combobox(selection,textvariable=self.school,state='readonly',width=30);self.school_box.pack(side='left',padx=8);self.school_box.bind('<<ComboboxSelected>>',lambda e:self.division_choices())
  ttk.Label(selection,text='Avdeling').pack(side='left');self.division=tk.StringVar(value='Ingen avdeling');self.division_box=ttk.Combobox(selection,textvariable=self.division,state='readonly',width=30);self.division_box.pack(side='left',padx=8)
  ttk.Button(self.frame,text='Opprett bruker',style='Accent.TButton',command=self.create).grid(row=9,column=1,sticky='w',pady=10)
  self.table=ttk.Treeview(self.frame,columns=('name','email','school','division','role','active','channel'),show='headings',height=7)
  for key,label in [('name','Navn'),('email','E-post'),('school','Skole'),('division','Avdeling'),('role','Rolle'),('active','Aktiv'),('channel','Oppdateringer')]:self.table.heading(key,text=label);self.table.column(key,width=145)
  self.table.grid(row=10,column=0,columnspan=3,sticky='nsew',pady=10);self.frame.rowconfigure(10,weight=1);self.frame.columnconfigure(1,weight=1)
  scrollbar=ttk.Scrollbar(self.frame,orient='vertical',command=self.table.yview);scrollbar.grid(row=10,column=3,sticky='ns');self.table.configure(yscrollcommand=scrollbar.set)
  ttk.Button(self.frame,text='Aktiver/deaktiver valgt lærer',command=self.toggle).grid(row=11,column=0,columnspan=2,sticky='w',pady=10)
  ttk.Button(self.frame,text='Gi valgt bruker dev',command=lambda:self.channel('dev')).grid(row=11,column=2,sticky='w')
  ttk.Button(self.frame,text='Gi valgt bruker stable',command=lambda:self.channel('stable')).grid(row=12,column=2,sticky='w')
  ttk.Button(self.frame,text='Tildel skole / avdeling til valgt bruker',command=self.assign).grid(row=12,column=0,columnspan=2,sticky='w')
  self.root.after(200,self.drain)
 def school_label(self,school):
  matches=[s for s in self.schools if s['name']==school['name']]
  return school['name'] if len(matches)==1 else school['name']+' ('+str(matches.index(school)+1)+')'
 def target(self):
  school=next((s for s in self.schools if self.school_label(s)==self.school.get()),None)
  if not school:raise ValueError('Hent lærere og velg skole først.')
  division=next((d for d in self.divisions if d['organization_id']==school['id'] and d['name']==self.division.get()),None)
  return {'school_id':school['id'],'division_id':division['id'] if division else None}
 def division_choices(self):
  school=next((s for s in self.schools if self.school_label(s)==self.school.get()),None)
  values=['Ingen avdeling']+[d['name'] for d in self.divisions if school and d['organization_id']==school['id']];self.division_box['values']=values
  if self.division.get() not in values:self.division.set(values[0])
 def new_school(self):
  name=simpledialog.askstring('Ny skole','Skolens navn:',parent=self.root)
  if name:self.run('school_save',name=name)
 def rename_school(self):
  try:target=self.target()
  except ValueError as e:messagebox.showinfo('Velg skole',str(e));return
  name=simpledialog.askstring('Endre skole','Skolens navn:',initialvalue=self.school.get(),parent=self.root)
  if name:self.run('school_save',school_id=target['school_id'],name=name)
 def new_division(self):
  try:target=self.target()
  except ValueError as e:messagebox.showinfo('Velg skole',str(e));return
  name=simpledialog.askstring('Ny avdeling','Avdelingens navn i '+self.school.get()+':',parent=self.root)
  if name:self.run('division_save',school_id=target['school_id'],name=name)
 def rename_division(self):
  try:target=self.target()
  except ValueError as e:messagebox.showinfo('Velg skole',str(e));return
  if not target['division_id']:return
  name=simpledialog.askstring('Endre avdeling','Avdelingens navn:',initialvalue=self.division.get(),parent=self.root)
  if name:self.run('division_save',name=name,**target)
 def assign(self):
  ids=self.table.selection()
  if not ids:return
  try:target=self.target()
  except ValueError as e:messagebox.showinfo('Velg skole',str(e));return
  self.run('set_school',user_id=ids[0],**target)
 def channel(self,value):
  ids=self.table.selection()
  if ids:self.run('set_channel',user_id=ids[0],channel=value)
 def create(self):
  try:body={k:v.get() for k,v in self.fields.items()};body.update(self.target())
  except ValueError as e:messagebox.showinfo('Velg skole',str(e));return
  self.fields['password'].set('');self.run('create',**body)
 def toggle(self):
  ids=self.table.selection()
  if not ids:return
  member=next((m for m in self.members if m['user_id']==ids[0]),None)
  if member and member['role']=='teacher':self.run('set_active',user_id=member['user_id'],active=not member['active'])
 def run(self,action,**body):
  if self.busy:return
  self.busy=True;self.status.set('Kontrollerer adminrettigheter …')
  def work():
   try:
    me=self.receiver.admin('me')['member']
    if me['role']!='admin':raise ValueError('Du er lærer. Bare administrator kan opprette brukere.')
    result=self.receiver.admin(action,**body);members=result if action=='list' else self.receiver.admin('list');schools=self.receiver.admin('school_list');self.queue.put((True,(me,members,result,schools)))
   except Exception as e:self.queue.put((False,str(e)))
  threading.Thread(target=work,daemon=True).start()
 def drain(self):
  if not self.root.winfo_exists():return
  try:
   while True:
    ok,result=self.queue.get_nowait();self.busy=False
    if not ok:self.status.set(str(result))
    else:
     me,members,response,catalog=result;self.schools=catalog['schools'];self.divisions=catalog['divisions'];self.school_box['values']=[self.school_label(s) for s in self.schools]
     if self.school.get() not in self.school_box['values']:self.school.set(next((self.school_label(s) for s in self.schools if s['id']==me['organization_id']),''))
     self.division_choices();self.role=me['role'];self.members=members['members'];self.table.delete(*self.table.get_children())
     for m in self.members:self.table.insert('','end',iid=m['user_id'],values=[m['display_name'],m['email'],next((s['name'] for s in self.schools if s['id']==m.get('organization_id')),''),next((d['name'] for d in self.divisions if d['id']==m.get('division_id')),'—'),'Admin' if m['role']=='admin' else 'Lærer','Ja' if m['active'] else 'Nei',m.get('update_channel','stable')])
     self.status.set(response.get('message','Admin: '+me['display_name']+' · '+str(len(self.members))+' brukere i skolen.'))
  except queue.Empty:pass
  self.root.after(200,self.drain)
