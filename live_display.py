"""Compact classroom list and selected-student analysis."""
import tkinter as tk
from tkinter import ttk
from classroom_analysis import analyse,value,percent
from core import QUAL
from course_setup import trip_name
BG='#081c2b';PANEL='#102b3e';TEXT='#edf5fb';MUTED='#a4b9c9';TEAL='#32d4bf';COLORS=['#3898ff',TEAL,'#ffc84e']
LABELS=['Trafikksikkerhet','Fartsavpassing','Fartsøkning','Komfort']
class LiveDisplay:
 def __init__(self,app,window):
  self.app=app;self.window=window;self.mode='Optimaltur 1–2–3';self.focus=None;self.signature=None
  window.configure(bg=BG)
  self.frame=tk.Frame(window,bg=BG);self.frame.pack(fill='both',expand=True,padx=16,pady=12)
  top=tk.Frame(self.frame,bg=BG);top.pack(fill='x',pady=(0,12))
  tk.Label(top,text='YSK Kjørestudio · Klasserom',bg=BG,fg=TEXT,font=('Segoe UI',22,'bold')).pack(side='left')
  self.course=tk.StringVar(value=app.filters['course'][0].get());self.vehicle=tk.StringVar(value=app.filters['vehicle'][0].get());self.view=tk.StringVar(value='Optimaltur 1–2–3')
  for label,var in [('Kurs',self.course),('Bil',self.vehicle),('Visning',self.view)]:
   tk.Label(top,text=label,bg=BG,fg=MUTED).pack(side='left',padx=(16,5));box=ttk.Combobox(top,textvariable=var,state='readonly',width=24 if label=='Visning' else 16);box.pack(side='left');box.bind('<<ComboboxSelected>>',lambda e:self.paint(True));setattr(self,'box_'+label,box)
  self.box_Visning['values']=['Optimaltur 1–2–3',trip_name(4),trip_name(5)]
  split=tk.PanedWindow(self.frame,orient='horizontal',bg=BG,sashwidth=8);split.pack(fill='both',expand=True)
  left=tk.Frame(split,bg=BG);right=tk.Frame(split,bg=PANEL);split.add(left,minsize=500,stretch='always');split.add(right,minsize=380,stretch='always')
  style=ttk.Style();style.configure('Classroom.Treeview',background=PANEL,fieldbackground=PANEL,foreground=TEXT,rowheight=35,font=('Segoe UI',12));style.configure('Classroom.Treeview.Heading',font=('Segoe UI',12,'bold'));style.map('Classroom.Treeview',background=[('selected','#135967')],foreground=[('selected',TEXT)])
  self.tree=ttk.Treeview(left,style='Classroom.Treeview',show='headings',selectmode='browse');scroll=ttk.Scrollbar(left,command=self.tree.yview);self.tree.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.tree.pack(fill='both',expand=True);self.tree.bind('<<TreeviewSelect>>',self.select);self.tree.bind('<Double-1>',lambda e:self.details())
  self.canvas=tk.Canvas(right,bg=PANEL,highlightthickness=0);self.canvas.pack(fill='both',expand=True);self.canvas.bind('<Configure>',lambda e:self.draw());self.canvas.bind('<Button-1>',lambda e:self.details() if e.y>self.canvas.winfo_height()-45 else None)
  self.footer=tk.Label(self.frame,bg=BG,fg=MUTED,anchor='w',font=('Segoe UI',10));self.footer.pack(fill='x',pady=(8,0))
  window.bind('<Escape>',lambda e:window.destroy());window.bind('<F11>',lambda e:app.fill_screen(window));window.bind('<Destroy>',self.destroyed,add='+');self.paint(True);self.timer=window.after(1000,self.tick)
 def destroyed(self,e):
  if e.widget==self.window:
   try:self.window.after_cancel(self.timer)
   except (tk.TclError,AttributeError):pass
 def tick(self):
  if self.window.winfo_exists():self.paint();self.timer=self.window.after(1000,self.tick)
 def source(self):return self.app.store.all(include_unscored=True)
 def paint(self,force=False):
  rows=self.source();signature=repr((rows,self.app.store.settings(),self.course.get(),self.vehicle.get(),self.view.get()))
  if not force and signature==self.signature:return
  self.signature=signature
  self.box_Kurs['values']=['Alle']+sorted({d['course'] for d in rows});self.box_Bil['values']=['Alle']+sorted({d['vehicle'] for d in rows})
  self.optimal=self.view.get()=='Optimaltur 1–2–3'
  if self.optimal:
   self.data=analyse(rows,self.app.store.settings(),self.course.get(),self.vehicle.get());columns=['Elev','Bil','Tur 1','Tur 2','Tur 3','Endring']
  else:
   n=4 if self.view.get()==trip_name(4) else 5;self.data=[d for d in rows if d['trip']==n and (self.course.get()=='Alle' or d['course']==self.course.get()) and (self.vehicle.get()=='Alle' or d['vehicle']==self.vehicle.get())];self.data.sort(key=lambda d:(d['driver'].casefold(),d.get('date','')));columns=['Elev','Bil','Dato','Tid','Distanse','Status']
  self.tree['columns']=columns
  for name in columns:self.tree.heading(name,text=name);self.tree.column(name,width=155 if name=='Elev' else 85,minwidth=60,stretch=True)
  self.tree.delete(*self.tree.get_children());self.lookup={}
  for i,d in enumerate(self.data):
   if self.optimal:
    scores=[('—' if d['points'].get(t) is None else f"{d['points'][t]:.1f}") for t in (1,2,3)];state='Flere registreringer' if d['ambiguous'] else 'Bilbytte' if d['changed'] else 'Mangler / utelatt' if d['delta'] is None else f"{d['delta']:+.1f} p";values=[d['driver'],' → '.join(d['cars']),*scores,state];key=d['key']
   else:values=[d['driver'],d['vehicle'],d.get('date',''),d.get('minutes','—'),d.get('km','—'),d.get('completion','')];key=d['id']
   self.lookup[str(i)]=d;self.tree.insert('','end',iid=str(i),values=values)
   if key==self.focus:self.tree.selection_set(str(i))
  if not self.tree.selection() and self.data:self.tree.selection_set('0')
  self.footer.configure(text=f'{len(self.data)} elever / registreringer · Rull for hele lista · Dobbeltklikk for alle turdata · Poeng er relative innen kurs og bil, med felles skala for tur 1–3. Gjeldende vekter brukes, også tid.')
  self.draw()
 def select(self,e=None):
  selected=self.tree.selection()
  if selected and selected[0] in self.lookup:
   d=self.lookup[selected[0]];self.focus=d['key'] if self.optimal else d['id'];self.draw()
 def chosen(self):
  ids=self.tree.selection();return self.lookup.get(ids[0]) if ids else None
 def draw(self):
  c=self.canvas;c.delete('all');d=self.chosen()
  if not d:return
  w=max(c.winfo_width(),380);h=max(c.winfo_height(),550);x=18
  def text(y,s,size=12,color=TEXT):c.create_text(x,y,text=s,fill=color,font=('Segoe UI',size),anchor='nw',width=w-36)
  text(15,d['driver']+' · Analyse',22)
  if not self.optimal:
   text(55,trip_name(d['trip'])+' · '+d['vehicle']);y=95
   for k,label in [('date','Dato'),('minutes','Tid (min)'),('km','Distanse (km)'),('liters','Liter totalt'),('stops','Unødige stopp'),('teacher','Lærer'),('notes','Notater')]:text(y,label+': '+str(d.get(k,'—')));y+=45
   text(h-32,'Alle turdata og leveringsstopp →',12,TEAL);return
  text(52,' · '.join(d['cars'])+(' · Bilbytte: ingen samlet endring' if d['changed'] else ' · Samme bil'),11,MUTED)
  history=d['history'];chart_h=max(95,min(160,(h-285)/3));y=84
  for key,label in [('fuel','Forbruk · l/mil'),('stops','Unødige stopp · per 10 km'),('time','Tid · minutter')]:
   vals=[value(history.get(t),key) for t in (1,2,3)];pct=percent(vals[0],vals[2]) if not d['changed'] and not d['ambiguous'] else None
   text(y,label+('  '+f'{pct:+.1f}% fra tur 1' if pct is not None else ''),13);top=y+35;bottom=y+chart_h-24
   peers=[value(p['history'].get(t),key) for p in self.data for t in (1,2,3)];available=[v for v in peers if v is not None];hi=max(available+[1])*1.12
   for fraction in (0,.5,1):
    py=bottom-fraction*(bottom-top);c.create_line(48,py,w-22,py,fill='#29465a');c.create_text(43,py,text=f'{hi*fraction:.1f}',fill=MUTED,anchor='e',font=('Segoe UI',9))
   previous=None
   for i,v in enumerate(vals):
    px=65+i*(w-95)/2;c.create_text(px,bottom+13,text='Tur '+str(i+1),fill=MUTED,font=('Segoe UI',10))
    if v is None:previous=None;continue
    py=bottom-v/hi*(bottom-top)
    if previous:c.create_line(*previous,px,py,fill=TEAL,width=2)
    c.create_oval(px-4,py-4,px+4,py+4,fill=COLORS[i],outline='');c.create_text(px,py-12,text=f'{v:.1f}',fill=TEXT,font=('Segoe UI',11));previous=(px,py)
   y+=chart_h+9
  text(y,'Faglige vurderinger · Tur 1 / 2 / 3',12,TEAL);y+=27
  for q,label in zip(QUAL,LABELS):
   ratings=[str(history.get(t,{}).get(q,'—')).replace('Middel','Middels') or '—' for t in (1,2,3)];text(y,label+': '+ ' / '.join(ratings),11);y+=25
  text(h-32,'Alle turdata og notater →',12,TEAL)
 def details(self):
  d=self.chosen()
  if not d:return
  win=tk.Toplevel(self.window);win.title(d['driver']+' · Alle turdata');win.geometry('850x650');box=tk.Text(win,wrap='word',font=('Segoe UI',12));box.pack(fill='both',expand=True);scroll=ttk.Scrollbar(win,command=box.yview);box.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y')
  records=list(d['history'].values()) if self.optimal else [d]
  for r in records:
   box.insert('end',trip_name(r['trip'])+'\n')
   for k,v in r.items():
    if k not in ('id','distribution'):
     label={'driver':'Elev','course':'Kurs','vehicle':'Bil','trip':'Turnummer','date':'Dato','start_time':'Starttid','minutes':'Minutter','km':'Distanse (km)','liters':'Forbruk totalt (liter)','stops':'Unødige stopp','average_speed':'Gjennomsnittsfart (km/t)','teacher':'Lærer','notes':'Notater','completion':'Registreringsstatus','updated':'Oppdatert','trafikksikkerhet':'Trafikksikkerhet','avpassing':'Fartsavpassing','økning':'Fartsøkning','komfort':'Komfort'}.get(k,k);box.insert('end',f'{label}: {v}\n')
   box.insert('end','\n')
   if r.get('distribution'):ttk.Button(win,text='Leveringsstopp · '+r['driver'],command=lambda r=r:self.app.show_distribution(r,win)).pack()
  box.configure(state='disabled')
