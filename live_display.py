"""Native classroom dashboard: compact list, real percentage changes and line charts."""
import tkinter as tk
from tkinter import ttk
from classroom_analysis import analyse,value,percent,summary,class_ranking
from core import QUAL
from course_setup import trip_name
BG='#f3f5f8';PANEL='#ffffff';TEXT='#132235';MUTED='#65758a';EDGE='#e1e7ee';TEAL='#087f72';RED='#b53c43';BLUE='#276ad4';GOLD='#a86b12';COLORS=[BLUE,TEAL,GOLD]
LABELS=['Trafikksikkerhet','Fartsavpassing','Fartsøkning','Komfort']
METRICS={'Poeng':('score','poeng / 100'),'Forbruk':('fuel','l/100 km'),'Tid':('time','minutter'),'Unødige stopp':('stops','stopp / 10 km'),'Gjennomsnittsfart':('speed','km/t'),'Tid per km':('time_per_km','min/km')}
class LiveDisplay:
 def __init__(self,app,window,embedded=False):
  self.app=app;self.window=window;self.embedded=embedded;self.focus=None;self.signature=None;self.sort_key='Snitt';self.desc=True;self.auto=False;self.auto_count=0;self.images=[];self.timer=None
  window.configure(bg=BG);self.frame=tk.Frame(window,bg=BG);self.frame.pack(fill='both',expand=True,padx=16,pady=12)
  top=tk.Frame(self.frame,bg=BG);top.pack(fill='x',pady=(0,10));tk.Label(top,text='YSK Kjørestudio',bg=BG,fg=TEXT,font=('Segoe UI',23,'bold')).pack(side='left');tk.Label(top,text='  KLASSEOVERSIKT',bg=BG,fg=MUTED,font=('Segoe UI',10,'bold')).pack(side='left')
  self.back_button=ttk.Button(top,text='Tillbake til alle elever',command=self.overview)
  if embedded:ttk.Button(top,text='+ Registrer tur',command=lambda:app.nb.select(app.register_frame)).pack(side='right')
  ttk.Button(top,text='Storskjerm' if embedded else 'Alle turdata',command=app.bigscreen if embedded else self.details).pack(side='right',padx=8)
  self.course=tk.StringVar(value=app.filters['course'][0].get());self.vehicle=tk.StringVar(value=app.filters['vehicle'][0].get());self.view=tk.StringVar(value='Optimaltur 1–2–3');self.search=tk.StringVar();self.table_mode=tk.StringVar(value='Poeng og målinger');self.metric=tk.StringVar(value='Poeng');self.trip_vars={t:tk.BooleanVar(value=app.compare_trips is None or t in app.compare_trips) for t in (1,2,3)}
  stats=tk.Frame(self.frame,bg=BG);stats.pack(fill='x',pady=(0,12));self.stats=[];self.stat_titles=[]
  for title in ('ELEVER','REGISTRERTE OPTIMALTURER','FERDIG MED VALGTE TURER','SAMMENLIGNBARE ELEVER'):
   f=tk.Frame(stats,bg=PANEL,padx=14,pady=9);f.pack(side='left',fill='x',expand=True,padx=(0,8));label=tk.Label(f,text=title,bg=PANEL,fg=MUTED,font=('Segoe UI',9,'bold'));label.pack(anchor='w');self.stat_titles.append(label);v=tk.StringVar(value='—');self.stats.append(v);tk.Label(f,textvariable=v,bg=PANEL,fg=TEXT,font=('Segoe UI',23,'bold')).pack(anchor='w')
  controls=tk.Frame(self.frame,bg=BG);controls.pack(fill='x',pady=(0,10))
  for label,var in [('Kurs',self.course),('Bil',self.vehicle),('Visning',self.view)]:
   tk.Label(controls,text=label,bg=BG,fg=MUTED).pack(side='left',padx=(0,5));box=ttk.Combobox(controls,textvariable=var,state='readonly',width=23 if label=='Visning' else 17);box.pack(side='left',padx=(0,12));box.bind('<<ComboboxSelected>>',lambda e:self.paint(True));setattr(self,'box_'+label,box)
  self.box_Visning['values']=['Optimaltur 1–2–3',trip_name(4),trip_name(5)];ttk.Entry(controls,textvariable=self.search,width=20).pack(side='right');tk.Label(controls,text='Søk elev / lærer',bg=BG,fg=MUTED).pack(side='right',padx=5);self.search.trace_add('write',lambda *a:self.paint(True))
  self.trip_controls=tk.Frame(self.frame,bg=BG);self.trip_controls.pack(fill='x',pady=(0,10));tk.Label(self.trip_controls,text='Sammenlign',bg=BG,fg=MUTED).pack(side='left',padx=(0,10))
  for t,v in self.trip_vars.items():ttk.Checkbutton(self.trip_controls,text='Tur '+str(t),variable=v,command=lambda:self.paint(True)).pack(side='left',padx=5)
  tk.Label(self.trip_controls,text='  Klikk en kolonne for å sortere · Dobbeltklikk en elev for analyse',bg=BG,fg=MUTED,font=('Segoe UI',10)).pack(side='left')
  self.split=tk.PanedWindow(self.frame,orient='horizontal',bg=BG,sashwidth=8,relief='flat');self.split.pack(fill='both',expand=True);left=tk.Frame(self.split,bg=PANEL);right=tk.Frame(self.split,bg=PANEL);self.split.add(left,minsize=510,stretch='always');self.right=right;self.analysis_open=False
  style=ttk.Style();style.configure('Classroom.Treeview',background=PANEL,fieldbackground=PANEL,foreground=TEXT,rowheight=34,font=('Segoe UI',11),borderwidth=0);style.configure('Classroom.Treeview.Heading',background=EDGE,foreground=MUTED,font=('Segoe UI',9,'bold'),padding=7);style.map('Classroom.Treeview',background=[('selected','#e1f2ee')],foreground=[('selected',TEXT)])
  self.tree=ttk.Treeview(left,style='Classroom.Treeview',show='tree headings',selectmode='browse');sy=ttk.Scrollbar(left,command=self.tree.yview);sx=ttk.Scrollbar(left,orient='horizontal',command=self.tree.xview);self.tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set);sy.pack(side='right',fill='y');sx.pack(side='bottom',fill='x');self.tree.pack(fill='both',expand=True);self.tree.bind('<<TreeviewSelect>>',self.select);self.tree.bind('<Double-1>',lambda e:self.open_analysis());self.tree.tag_configure('warn',foreground=GOLD);self.tree.tag_configure('up',foreground=TEAL)
  chart_controls=tk.Frame(right,bg=PANEL);chart_controls.pack(fill='x',padx=12,pady=(10,0));tk.Label(chart_controls,text='Analyse',bg=PANEL,fg=TEXT,font=('Segoe UI',11,'bold')).pack(side='left');metric_box=ttk.Combobox(chart_controls,textvariable=self.metric,values=list(METRICS),state='readonly',width=20);metric_box.pack(side='right');metric_box.bind('<<ComboboxSelected>>',lambda e:self.draw())
  self.canvas=tk.Canvas(right,bg=PANEL,highlightthickness=0);cs=ttk.Scrollbar(right,command=self.canvas.yview);self.canvas.configure(yscrollcommand=cs.set);cs.pack(side='right',fill='y');self.canvas.pack(fill='both',expand=True);self.canvas.bind('<Configure>',lambda e:self.draw());self.canvas.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-int(e.delta/120),'units'));self.canvas.bind('<Button-1>',self.canvas_click)
  tk.Label(self.trip_controls,text='  Vis',bg=BG,fg=MUTED).pack(side='left',padx=6)
  modes=ttk.Combobox(self.trip_controls,textvariable=self.table_mode,values=['Poeng og målinger','Alle data'],state='readonly',width=18);modes.pack(side='left');modes.bind('<<ComboboxSelected>>',lambda e:self.paint(True))
  self.footer=tk.Label(self.frame,bg=BG,fg=MUTED,anchor='w',font=('Segoe UI',9),wraplength=1400,justify='left');self.footer.pack(fill='x',pady=(8,0))
  if not embedded:window.bind('<Escape>',lambda e:window.destroy());window.bind('<F11>',lambda e:app.fill_screen(window))
  window.bind('<Destroy>',self.destroyed,add='+');self.paint(True);self.timer=window.after(1500,self.tick);window.after(100,self.overview)
 def destroyed(self,e):
  if e.widget==self.window and self.timer:
   try:self.window.after_cancel(self.timer)
   except tk.TclError:pass
 def tick(self):
  if self.window.winfo_exists():
   self.paint();self.auto_count+=1
   if self.auto and self.auto_count%7==0:self.move(1)
   self.timer=self.window.after(1500,self.tick)
 def source(self):return self.app.store.all(include_unscored=True)
 def trips(self):return tuple(t for t,v in self.trip_vars.items() if v.get())
 def set_mode(self,mode):
  if mode in METRICS:self.metric.set(mode)
  elif mode=='Samlet poeng':self.metric.set('Poeng')
  elif mode=='Stopp per km':self.metric.set('Unødige stopp')
  self.paint(True)
 def move(self,step):
  ids=list(self.tree.get_children());selected=self.tree.selection()
  if ids:
   index=(ids.index(selected[0]) if selected and selected[0] in ids else 0)+step;iid=ids[index%len(ids)];self.tree.selection_set(iid);self.tree.see(iid)
 def toggle(self):self.auto=not self.auto
 def spark(self,d):
  from PIL import Image,ImageDraw,ImageTk
  image=Image.new('RGB',(62,26),PANEL);draw=ImageDraw.Draw(image);last=None
  for i,t in enumerate(self.trips()):
   v=d['points'].get(t);x=7+i*23
   if v is None:last=None;continue
   y=22-max(0,min(100,v))/100*18
   if last and not d['changed'] and not d['ambiguous']:draw.line([last,(x,y)],fill=TEAL,width=2)
   draw.ellipse((x-2,y-2,x+2,y+2),fill=COLORS[t-1]);last=(x,y)
  result=ImageTk.PhotoImage(image,master=self.window);self.images.append(result);return result
 def paint(self,force=False):
  rows=self.source();signature=repr((rows,self.app.store.settings(),self.course.get(),self.vehicle.get(),self.view.get(),self.search.get(),self.trips(),self.sort_key,self.desc,self.table_mode.get()))
  if not force and signature==self.signature:return
  self.signature=signature;self.box_Kurs['values']=['Alle']+sorted({d['course'] for d in rows});self.box_Bil['values']=['Alle']+sorted({d['vehicle'] for d in rows if self.course.get()=='Alle' or d['course']==self.course.get()});self.optimal=self.view.get()=='Optimaltur 1–2–3';trips=self.trips()
  if self.optimal:
   data=class_ranking(analyse(rows,self.app.store.settings(),self.course.get(),self.vehicle.get(),trips),trips);counts=summary(data,trips);columns=['Plass','Elev','Bil',*['T'+str(t) for t in trips],'Snitt','Δ poeng',*['Forbruk T'+str(t) for t in trips],*['Forbedring 1→'+str(t) for t in trips if t!=1],*['Min T'+str(t) for t in trips],*['Stopp T'+str(t) for t in trips],'Status']
   if self.table_mode.get()=='Alle data':columns+=['Lærer',*[label+' T'+str(t) for label in ['Km','Liter','Km/t',*LABELS] for t in trips]]
   stat=[counts['students'],counts['registered'],counts['complete'] if trips else '—',counts['comparable']];self.trip_controls.pack(fill='x',before=self.split,pady=(0,10));self.tree.heading('#0',text='Trend');self.tree.column('#0',width=70,minwidth=70,stretch=False)
  else:
   n=4 if self.view.get()==trip_name(4) else 5;data=[d for d in rows if d['trip']==n and (self.course.get()=='Alle' or d['course']==self.course.get()) and (self.vehicle.get()=='Alle' or d['vehicle']==self.vehicle.get())];columns=['Elev','Bil','Dato','Tid','Distanse','Status'];stat=[len({(d['course'],d['driver']) for d in data}),len(data),sum(d.get('completion')!='incomplete' for d in data),'—'];self.trip_controls.pack_forget();self.tree.column('#0',width=0,minwidth=0,stretch=False);self.tree.heading('#0',text='')
  for label,title in zip(self.stat_titles,('ELEVER','REGISTRERTE OPTIMALTURER' if self.optimal else 'REGISTRERTE TURER','FERDIG MED VALGTE TURER' if self.optimal else 'FERDIGE REGISTRERINGER','SAMMENLIGNBARE ELEVER' if self.optimal else 'ENKELTVISNING')):label.configure(text=title)
  for var,v in zip(self.stats,stat):var.set(str(v))
  query=self.search.get().strip().casefold();self.data=[d for d in data if query in (d['driver']+' '+d['course']+' '+' '.join(d['teachers'] if self.optimal else [d.get('teacher','')])).casefold()]
  def sort(d):
   if self.sort_key=='Plass' and self.optimal:v=d['place']
   elif self.optimal and self.sort_key not in ('Elev','Bil','Snitt','Δ poeng'):v=self.table_values(d,trips).get(self.sort_key)
   elif self.sort_key=='Elev':v=d['driver'].casefold()
   elif self.sort_key=='Bil':v=' '.join(d['cars']) if self.optimal else d['vehicle']
   elif self.sort_key.startswith('T') and self.sort_key[1:].isdigit() and self.optimal:v=d['points'].get(int(self.sort_key[1:]))
   elif self.sort_key=='Status' and self.optimal:v=self.registration_status(d,trips)
   elif self.sort_key=='Lærer' and self.optimal:v=' / '.join(d['teachers'])
   elif self.sort_key=='Snitt' and self.optimal:v=d['average']
   elif self.sort_key=='Δ poeng' and self.optimal:v=d['delta']
   elif self.sort_key in ('Forbruk %','Stopp %') and self.optimal:v=d['changes']['fuel' if self.sort_key=='Forbruk %' else 'stops']
   else:v=d.get({'Tid':'minutes','Distanse':'km','Dato':'date','Status':'completion'}.get(self.sort_key,'driver'))
   if not self.optimal and self.sort_key in ('Tid','Distanse'):
    try:v=float(v)
    except (TypeError,ValueError):v=None
   return (v is None,str(v) if isinstance(v,str) else v if isinstance(v,(int,float)) else '')
  # Missing scores are always last, independently of sort direction.
  available=[d for d in self.data if not sort(d)[0]];missing=[d for d in self.data if sort(d)[0]];self.data=sorted(available,key=sort,reverse=self.desc)+missing
  position=self.tree.yview()[0];self.tree['columns']=columns
  for name in columns:self.tree.heading(name,text=name,command=lambda name=name:self.sort_by(name));self.tree.column(name,width=155 if name=='Elev' else 110 if name in ('Bil','Lærer','Status') or name.startswith('Forbedring') else 85 if name.startswith('Forbruk') else 62,minwidth=45,stretch=name in ('Elev','Bil'))
  self.tree.delete(*self.tree.get_children());self.lookup={};self.images=[]
  for i,d in enumerate(self.data):
   if self.optimal:
    values=self.table_values(d,trips);vals=[self.pct(values.get(col)) if col.startswith('Forbedring') else self.number(values.get(col),signed=col=='Δ poeng') if isinstance(values.get(col),(int,float)) or values.get(col) is None else values[col] for col in columns];key=d['key'];image=self.spark(d);tags=('warn',) if d['changed'] or d['ambiguous'] else ('up',) if d['delta'] is not None and d['delta']>0 else ()
   else:vals=[d['driver'],d['vehicle'],d.get('date',''),d.get('minutes','—'),d.get('km','—'),'Uferdig' if d.get('completion')=='incomplete' else 'Registrert'];key=d['id'];image='';tags=()
   self.lookup[str(i)]=d;self.tree.insert('','end',iid=str(i),values=vals,image=image,tags=tags)
   if key==self.focus:self.tree.selection_set(str(i))
  if not self.tree.selection() and self.data:self.tree.selection_set('0')
  self.tree.yview_moveto(position);self.select()
  sync=getattr(self.app,'last_cloud_update',None);self.footer.configure(text=f'{len(self.data)} av {len(data)} elever / aktiviteter · '+(f'Siste skyhenting {sync} · ' if sync else '')+'Poeng 0–100: felles relativ skala innen kurs og bil for optimaltur 1–3. Plassering etter snittpoeng, kun ferdige tursett innen samme kurs og bil. Forbedring 1→2/3 er reduksjon i l/100 km: positiv prosent betyr lavere forbruk. Null utgangspunkt gir —. Tid følger gjeldende vekter.')
  if not self.data:self.draw()
 def table_values(self,d,trips):
  out={'Plass':d.get('place'),'Elev':d['driver'],'Bil':' → '.join(d['cars']),'Snitt':d['average'],'Δ poeng':d['delta'],'Status':self.registration_status(d,trips),'Lærer':' / '.join(d['teachers']) or '—'}
  for t in trips:
   r=d['history'].get(t,{})
   out['T'+str(t)]=d['points'].get(t)
   fuel=value(r,'fuel');out['Forbruk T'+str(t)]=None if fuel is None else 10*fuel
   out['Forbedring 1→'+str(t)]=d['fuel_improvement'].get(t)
   out['Min T'+str(t)]=value(r,'time')
   for label,key in [('Stopp','stops'),('Km','km'),('Liter','liters')]:
    try:out[label+' T'+str(t)]=float(r[key])
    except (KeyError,TypeError,ValueError):out[label+' T'+str(t)]=None
   out['Km/t T'+str(t)]=value(r,'speed')
   for key,label in zip(QUAL,LABELS):out[label+' T'+str(t)]=r.get(key) or '—'
  return out
 def overview(self):
  if self.analysis_open:self.split.forget(self.right)
  self.analysis_open=False;self.back_button.pack_forget()
 def open_analysis(self):
  if not self.chosen():return
  if not self.analysis_open:self.split.add(self.right,minsize=390,stretch='always')
  self.analysis_open=True;self.back_button.pack(side='right',padx=8)
  self.window.after_idle(lambda:self.split.sash_place(0,int(self.split.winfo_width()*.55),0))
  self.draw()
 def sort_by(self,name):self.desc=not self.desc if self.sort_key==name else name not in ('Elev','Bil','Dato','Plass');self.sort_key=name;self.paint(True)
 @staticmethod
 def registration_status(d,trips):
  if d['ambiguous']:return 'Flere registreringer'
  if d['changed']:return 'Bilbytte'
  if not trips:return 'Ingen turer valgt'
  complete=sum(d['points'].get(t) is not None for t in trips)
  return 'Klar' if complete==len(trips) else f'{complete}/{len(trips)} klare'
 @staticmethod
 def number(v,signed=False):return '—' if v is None else f'{v:+.1f}' if signed else f'{v:.1f}'
 @staticmethod
 def pct(v):return '—' if v is None else f'{v:+.1f}%'
 def select(self,e=None):
  d=self.chosen()
  if d:self.focus=d['key'] if self.optimal else d['id'];self.draw()
 def chosen(self):
  ids=self.tree.selection();return self.lookup.get(ids[0]) if ids else None
 def draw(self):
  c=self.canvas;c.delete('all');d=self.chosen();w=max(c.winfo_width(),360);content=0
  def text(x,y,s,size=11,color=TEXT,width=None):return c.create_text(x,y,text=s,fill=color,font=('Segoe UI',size),anchor='nw',width=width or w-x-18)
  def box(x,y,bw,bh):c.create_rectangle(x,y,x+bw,y+bh,fill='#f7f9fb',outline=EDGE)
  if not d:
   text(18,24,'Ingen elever i dette utvalget',18);text(18,65,'Velg et kurs, en annen bil eller tøm søket.');c.configure(scrollregion=(0,0,w,200));return
  text(18,14,d['driver'],22);text(18,50,d['course']+' · '+(' → '.join(d['cars']) if self.optimal else d['vehicle']),10,MUTED)
  if not self.optimal:
   y=85;text(18,y,trip_name(d['trip']),14);y+=35
   for k,label in [('date','Dato'),('start_time','Starttid'),('minutes','Tid (min)'),('km','Distanse (km)'),('liters','Liter totalt'),('fuel_per_100','Manuelt forbruk (l/100 km)'),('stops','Unødige stopp'),('teacher','Lærer'),('notes','Notater')]:
    item=text(18,y,label+': '+str(d.get(k,'—')));y+=max(32,c.bbox(item)[3]-y+14)
   if d.get('distribution'):
    from distribution import rows,summary as distribution_summary,return_minutes
    log=d['distribution'];text(18,y,distribution_summary(log),13,TEAL);y+=35
    for event in rows(log):
     item=text(18,y,f"Stopp {event['stop']} · {'Rampe' if event['status']=='ramp' else 'Avbrutt'}\n{event['segment_minutes']:.1f} min fra forrige · {event['elapsed_minutes']:.1f} min fra start\n{event['reason']}");y+=c.bbox(item)[3]-y+18
    ret=return_minutes(log);text(18,y,'Retur til skolen: '+('Pågår' if ret is None else f'{ret:.1f} min'));y+=40
   text(18,y,'Åpne alle turdata →',12,TEAL);self.details_y=y;c.configure(scrollregion=(0,0,w,y+55));return
  trips=self.trips();history=d['history'];warning='Flere registreringer av samme tur: velg turdata for gjennomgang.' if d['ambiguous'] else 'Bilbytte: samlet endring beregnes ikke.' if d['changed'] else 'Ingen turer valgt.' if not trips else 'Sammenligning: '+ ' → '.join('Tur '+str(t) for t in trips)
  text(18,74,warning,10,GOLD if d['ambiguous'] or d['changed'] else MUTED)
  bw=(w-48)/2;y=110
  first,last=(trips[0],trips[-1]) if len(trips)>=2 else (None,None)
  fuel_now=value(history.get(trips[-1]),'fuel') if trips else None
  tiles=[('SNITTPOENG',self.number(d['average'])+' / 100'),('ENDRING POENG',self.number(d['delta'],True)+' p'),('SISTE FORBRUK',('—' if fuel_now is None else f'{10*fuel_now:.1f}')+' l/100 km'),('FORBRUKSENDRING',self.pct(d['changes']['fuel']))]
  for i,(label,val) in enumerate(tiles):
   bx=18+(i%2)*(bw+12);by=y+(i//2)*78;box(bx,by,bw,68);text(bx+10,by+9,label,9,MUTED,width=bw-20);text(bx+10,by+28,val,18,TEAL,width=bw-20)
  y=282;metric,unit=METRICS[self.metric.get()];text(18,y,self.metric.get()+' · '+unit,14);y+=36;chart_top=y+15;bottom=y+195
  vals=[d['points'].get(t) if metric=='score' else value(history.get(t),metric) for t in trips]
  if metric=='fuel':vals=[v*10 if v is not None else None for v in vals]
  peers=[p['points'].get(t) if metric=='score' else value(p['history'].get(t),metric) for p in self.data for t in trips];available=[v*(10 if metric=='fuel' else 1) for v in peers if v is not None];hi=100 if metric=='score' else max(available+[1])*1.15
  for fraction in (0,.25,.5,.75,1):
   py=bottom-fraction*(bottom-chart_top);c.create_line(52,py,w-28,py,fill=EDGE);c.create_text(46,py,text=f'{hi*fraction:.0f}' if hi>20 else f'{hi*fraction:.1f}',fill=MUTED,anchor='e',font=('Segoe UI',9))
  previous=None
  for i,(t,v) in enumerate(zip(trips,vals)):
   px=68+i*(w-110)/max(1,len(trips)-1) if len(trips)>1 else w/2;c.create_text(px,bottom+22,text='Tur '+str(t),fill=MUTED,font=('Segoe UI',10))
   if v is None:c.create_text(px,chart_top+35,text='Mangler',fill=MUTED,font=('Segoe UI',9));previous=None;continue
   py=bottom-v/hi*(bottom-chart_top)
   if previous and not d['changed'] and not d['ambiguous']:c.create_line(*previous,px,py,fill=TEAL,width=3)
   c.create_oval(px-5,py-5,px+5,py+5,fill=COLORS[t-1],outline=PANEL,width=2);c.create_text(px,py-15,text=f'{v:.1f}',fill=TEXT,font=('Segoe UI',11,'bold'));previous=(px,py)
  y=bottom+50;text(18,y,'Endring mellom valgte turer',12);y+=28
  for key,label in [('fuel','Forbruk'),('stops','Unødige stopp per 10 km'),('time','Forbrukt tid'),('speed','Gjennomsnittsfart')]:
   text(18,y,label,11,MUTED);v=d['changes'][key];c.create_text(w-24,y,text=self.pct(v),fill=TEAL if v is not None and v<=0 and key!='speed' else TEXT,anchor='ne',font=('Segoe UI',11,'bold'));y+=28
  y+=12;text(18,y,'Faglige vurderinger',13);y+=30;col=(w-185)/max(1,len(trips))
  for i,t in enumerate(trips):text(172+i*col,y,'T'+str(t),10,MUTED,width=col-3)
  y+=24
  for q,label in zip(QUAL,LABELS):
   text(18,y,label,10,width=150)
   for i,t in enumerate(trips):
    rating=history.get(t,{}).get(q,'—') or '—';text(172+i*col,y,'Middels' if rating=='Middel' else rating,10,TEAL if rating=='Bra' else GOLD if rating in ('Middel','Svak') else MUTED,width=col-3)
   y+=29
  y+=10;text(18,y,'Lærer: '+(' / '.join(d['teachers']) or 'Ikke registrert'),10,MUTED);y+=35;text(18,y,'Åpne alle turdata og kommentarer →',12,TEAL);self.details_y=y;c.configure(scrollregion=(0,0,w,y+55))
 def canvas_click(self,event):
  if abs(self.canvas.canvasy(event.y)-getattr(self,'details_y',-100))<25:self.details()
 def details(self):
  d=self.chosen()
  if not d:return
  win=tk.Toplevel(self.window);win.title(d['driver']+' · Alle turdata');win.geometry('850x650');frame=ttk.Frame(win);frame.pack(fill='both',expand=True);scroll=ttk.Scrollbar(frame);scroll.pack(side='right',fill='y');box=tk.Text(frame,wrap='word',font=('Segoe UI',12),yscrollcommand=scroll.set);box.pack(fill='both',expand=True);scroll.configure(command=box.yview)
  records=sorted(d['records'],key=lambda r:(r['trip'],r.get('date',''),r['vehicle'])) if self.optimal else [d]
  labels={'driver':'Elev','course':'Kurs','vehicle':'Bil','trip':'Turnummer','date':'Dato','start_time':'Starttid','minutes':'Minutter','km':'Distanse (km)','liters':'Forbruk totalt (liter)','stops':'Unødige stopp','average_speed':'Gjennomsnittsfart (km/t)','fuel_per_100':'Manuelt forbruk (l/100 km)','teacher':'Lærer','notes':'Notater','completion':'Registreringsstatus','updated':'Oppdatert','trafikksikkerhet':'Trafikksikkerhet','avpassing':'Fartsavpassing','økning':'Fartsøkning','komfort':'Komfort'}
  for r in records:
   box.insert('end',trip_name(r['trip'])+'\n')
   for k,label in labels.items():
    if k in r:box.insert('end',f'{label}: {r[k]}\n')
   box.insert('end','\n')
   if r.get('distribution'):ttk.Button(win,text='Leveringsstopp · '+r['driver'],command=lambda r=r:self.app.show_distribution(r,win)).pack()
  box.configure(state='disabled')
