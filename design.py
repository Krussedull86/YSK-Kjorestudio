from course_setup import trip_name,course_count
import tkinter as tk
from tkinter import ttk
from core import QUAL,metrics
from classroom import board
from classroom_views import MODES,projection,value_text
BG='#f3f6fa';PANEL='#ffffff';EDGE='#dfe7ef';TEXT='#183047';MUTED='#61778c';TEAL='#087f72';BLUE='#346fd2';GOLD='#9d6717'

def classroom_class(Base):
 class ClassroomApp(Base):
  def __init__(self,root):
   self.ready=False;self.page=0;self.presentation='Rangering';self.autoplay=False;self.focus_driver=None;self.live_changes={};self.live_fingerprints={};self.live_display=None;self.last_cloud_update=None
   super().__init__(root)
   root.title('YSK Kjørestudio · '+('DEMO' if '--demo' in __import__('sys').argv else 'Klasserom'));root.configure(bg=BG);root.geometry('1380x900')
   style=ttk.Style();style.configure('.',background=BG,foreground=TEXT,font=('Segoe UI',11))
   style.configure('TFrame',background=BG);style.configure('TLabel',background=BG,foreground=TEXT)
   style.configure('TButton',background=EDGE,foreground=TEXT,padding=(14,10),borderwidth=0)
   style.map('TButton',background=[('active','#d3e7e2')],foreground=[('disabled',MUTED)])
   style.configure('Accent.TButton',background=TEAL,foreground='white',font=('Segoe UI',11,'bold'))
   style.map('Accent.TButton',background=[('active','#076a60')])
   style.configure('TEntry',fieldbackground=PANEL,foreground=TEXT,insertcolor=TEXT,padding=8)
   style.configure('TCombobox',fieldbackground=PANEL,background=EDGE,foreground=TEXT,arrowcolor=TEAL,padding=6)
   style.map('TCombobox',fieldbackground=[('readonly',PANEL)],foreground=[('readonly',TEXT)])
   root.option_add('*TCombobox*Listbox.background',PANEL);root.option_add('*TCombobox*Listbox.foreground',TEXT)
   style.configure('TNotebook',background=BG,borderwidth=0);style.configure('TNotebook.Tab',background=PANEL,foreground=MUTED,padding=(20,13))
   style.map('TNotebook.Tab',background=[('selected',EDGE)],foreground=[('selected',TEAL)])
   style.configure('Treeview',background=PANEL,fieldbackground=PANEL,foreground=TEXT,rowheight=36,borderwidth=0)
   style.configure('Treeview.Heading',background=EDGE,foreground=TEXT,font=('Segoe UI',10,'bold'),padding=8)
   style.map('Treeview',background=[('selected','#265a78')],foreground=[('selected','white')])
   self.dashboard=ttk.Frame(self.nb,padding=20);self.nb.insert(0,self.dashboard,text='Klasserom');self.nb.select(self.dashboard)
   hero=ttk.Frame(self.dashboard);hero.pack(fill='x')
   ttk.Label(hero,text='Dagens kjøreturer',font=('Segoe UI',27,'bold')).pack(side='left')
   ttk.Button(hero,text='+ Registrer tur',style='Accent.TButton',command=lambda:self.nb.select(1)).pack(side='right')
   ttk.Label(self.dashboard,text='Velg gruppe og tur. Klikk en sjåfør for å undersøke utviklingen sammen med klassen.',foreground=MUTED).pack(anchor='w',pady=(6,18))
   self.stats=ttk.Frame(self.dashboard);self.stats.pack(fill='x',pady=(0,18))
   self.stat_vars=[]
   for title in ['SJÅFØRER','REGISTRERTE TURER','SNITT FORBRUK','FULLFØRT KURS']:
    f=tk.Frame(self.stats,bg=PANEL,padx=20,pady=14);f.pack(side='left',fill='x',expand=True,padx=(0,10));tk.Label(f,text=title,bg=PANEL,fg=MUTED,font=('Segoe UI',10,'bold')).pack(anchor='w');v=tk.StringVar(value='—');self.stat_vars.append(v);tk.Label(f,textvariable=v,bg=PANEL,fg=TEAL,font=('Segoe UI',25,'bold')).pack(anchor='w')
   controls=ttk.Frame(self.dashboard);controls.pack(fill='x',pady=(0,15))
   for key,label in [('course','Kurs'),('vehicle','Kjøretøy'),('trip','Tur')]:
    ttk.Label(controls,text=label,foreground=MUTED).pack(side='left',padx=(0,6));v=self.filters[key][0];b=ttk.Combobox(controls,textvariable=v,state='readonly',width=16);b.pack(side='left',padx=(0,16));b.bind('<<ComboboxSelected>>',lambda e:self.refresh());setattr(self,'dash_'+key,b)
   ttk.Button(controls,text='Sammenlign turer',command=self.compare_dialog).pack(side='left')
   self.mode=tk.StringVar(value='Samlet poeng');box=ttk.Combobox(controls,textvariable=self.mode,values=MODES,width=19,state='readonly');box.pack(side='right',padx=5);box.bind('<<ComboboxSelected>>',lambda e:self.update_mode())
   ttk.Button(controls,text='Vis på storskjerm',style='Accent.TButton',command=self.bigscreen).pack(side='right',padx=8)
   self.body=ttk.Frame(self.dashboard);self.body.pack(fill='both',expand=True);self.body.columnconfigure(0,weight=3);self.body.columnconfigure(1,weight=2);self.body.rowconfigure(0,weight=1)
   left=ttk.Frame(self.body);left.grid(row=0,column=0,sticky='nsew',padx=(0,16));self.cards=tk.Canvas(left,bg=BG,highlightthickness=0);scroll=ttk.Scrollbar(left,command=self.cards.yview);self.cards.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.cards.pack(fill='both',expand=True)
   self.card_frame=tk.Frame(self.cards,bg=BG);self.card_window=self.cards.create_window(0,0,window=self.card_frame,anchor='nw');self.card_frame.bind('<Configure>',lambda e:self.cards.configure(scrollregion=self.cards.bbox('all')));self.cards.bind('<Configure>',lambda e:self.cards.itemconfigure(self.card_window,width=e.width))
   self.detail=tk.Frame(self.body,bg=PANEL,padx=20,pady=20);self.detail.grid(row=0,column=1,sticky='nsew')
   footer=ttk.Frame(self.dashboard);footer.pack(fill='x',pady=(16,0));ttk.Label(footer,text='LIVE · Nye turer kommer automatisk inn',foreground=TEAL).pack(side='left');ttk.Button(footer,text='← Forrige side',command=lambda:self.move_page(-1)).pack(side='right');ttk.Button(footer,text='Neste side →',command=lambda:self.move_page(1)).pack(side='right',padx=8);ttk.Button(footer,text='Start / stopp automatisk visning',command=self.toggle_auto).pack(side='right',padx=8)
   self.install_rating_buttons()
   self.ready=True;self.refresh();root.after(10000,self.auto_tick)
  def install_rating_buttons(self):
   register=self.nb.nametowidget(self.nb.tabs()[1])
   for k in QUAL:
    row,col=self.rating_positions[k]
    for widget in register.grid_slaves(row=row,column=col):widget.destroy()
    group=tk.Frame(register,bg=BG);group.grid(row=row,column=col,sticky='ew',padx=8,pady=8)
    var=self.fields[k];buttons=[]
    for value,color in [('Bra',TEAL),('Middel',GOLD),('Svak','#bb414e'),('-',MUTED),('',MUTED)]:
     b=tk.Button(group,text='Middels' if value=='Middel' else 'Tøm' if value=='' else value,relief='flat',font=('Segoe UI',11,'bold'),padx=12,pady=10,command=lambda v=var,value=value:v.set(value));b.pack(side='left',padx=(0,5));buttons.append((b,value,color))
    def update(*args,var=var,buttons=buttons):
     for b,value,color in buttons:b.configure(bg=color if var.get()==value else EDGE,fg='white' if var.get()==value else MUTED)
    var.trace_add('write',update);update()
  def update_mode(self):
   self.presentation=self.mode.get();self.page=0
   if self.live_display:self.live_display.set_mode(self.mode.get())
   self.refresh()
  def display_rows(self):
   if self.presentation!='Utvikling':return self.ranked
   groups={}
   for d in self.ranked:
    key=(d['course'],d['vehicle'],d['driver'])
    if key not in groups or d['trip']>groups[key]['trip']:groups[key]=d
   return list(groups.values())
  def move_page(self,step):
   if self.live_display:self.live_display.move(step);return
   pages=max(1,(len(self.display_rows())+5)//6);self.page=(self.page+step)%pages
   if self.display and self.display.winfo_exists():self.paint_display()
  def toggle_auto(self):
   if self.live_display and self.display and self.display.winfo_exists():self.live_display.toggle();self.autoplay=self.live_display.auto
   else:self.autoplay=not self.autoplay
  def auto_tick(self):
   # The full-screen view owns its rotation timer.
   self.root.after(10000,self.auto_tick)
  def refresh(self):
   import time,json
   current={d['id']:json.dumps({k:v for k,v in d.items() if k!='updated'},sort_keys=True,ensure_ascii=False) for d in self.store.all()}
   for id,value in current.items():
    if id not in self.live_fingerprints or self.live_fingerprints[id]!=value:self.live_changes[id]=time.monotonic()
   self.live_fingerprints=current
   super().refresh()
   if not self.ready:return
   for key,(v,box) in self.filters.items():getattr(self,'dash_'+key)['values']=box['values']
   rows=self.filtered(self.rows);people={(d['course'],d['vehicle'],d['driver']) for d in rows};avg=sum(metrics(d)['forbruk10'] for d in rows)/len(rows) if rows else None
   vals=[str(len(people)),str(len(rows)),f'{avg:.3f} L/10 km' if avg is not None else '—',str(len({(d['course'],d['vehicle'],d['driver']) for d in self.rows if d['trip']==course_count(self.store,d['course']) and self.filters['course'][0].get() in ['Alle',d['course']] and self.filters['vehicle'][0].get() in ['Alle',d['vehicle']]}))]
   for v,val in zip(self.stat_vars,vals):v.set(val)
   for child in self.card_frame.winfo_children():child.destroy()
   if not self.ranked:
    f=tk.Frame(self.card_frame,bg=PANEL,padx=25,pady=40);f.pack(fill='x');tk.Label(f,text='Klar for første kjøretur?',bg=PANEL,fg=TEXT,font=('Segoe UI',22,'bold')).pack(anchor='w');tk.Label(f,text='Registrer på PC eller åpne mobiladressen øverst.\nResultatene vises her når turen er lagret.',bg=PANEL,fg=MUTED,justify='left',font=('Segoe UI',12)).pack(anchor='w',pady=12)
   self.classroom_rows=projection(self.rows,self.store.settings(),mode=self.mode.get(),selected_trips=self.compare_trips,**{k:v.get() for k,(v,box) in self.filters.items()})
   for d in self.classroom_rows:
    f=tk.Frame(self.card_frame,bg=PANEL,padx=18,pady=14,cursor='hand2');f.pack(fill='x',pady=(0,10))
    group=f"{d['course']} · {d['vehicle']} · {trip_name(d['trip'])}";title=tk.Label(f,text=f"{'—' if d['view_place'] is None or self.mode.get()=='Siste turer' else '#'+str(d['view_place'])}  {d['driver']}",bg=PANEL,fg=TEXT,font=('Segoe UI',18,'bold'),anchor='w');title.pack(fill='x');tk.Label(f,text=group,bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w',pady=(3,8))
    tk.Label(f,text=value_text(d,self.mode.get())+f"    ·    {d['forbruk10']:.2f} L/10 km    ·    {int(d['stops'])} stopp",bg=PANEL,fg=TEAL,font=('Segoe UI',12,'bold')).pack(anchor='w')
    gain=d['fuel_improvement'];summary='Første registrerte tur' if len(d['history'])<2 else 'Utgangsforbruk 0' if gain is None else f'{gain:+.1f}% forbedring i forbruk'
    tk.Label(f,text=summary,bg=PANEL,fg=TEAL if gain is not None and gain>=0 else GOLD,font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(6,3))
    tk.Label(f,text=' · '.join(f"Tur {n} {'✓' if n in d['completed'] else '–'}" for n in range(1,6)),bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w')
    for widget in [f,*f.winfo_children()]:widget.bind('<Button-1>',lambda e,d=d:self.choose_driver(d))
   valid=[d for d in self.ranked if (d['course'],d['vehicle'],d['driver'])==self.focus_driver]
   if valid:self.choose_driver(valid[-1])
   elif self.ranked:self.choose_driver(self.ranked[0])
   else:
    for child in self.detail.winfo_children():child.destroy()
    tk.Label(self.detail,text='Her følger vi utviklingen',bg=PANEL,fg=TEXT,font=('Segoe UI',18,'bold'),wraplength=330).pack(anchor='w');tk.Label(self.detail,text='Velg et sjåførkort for å se turene,\nvurderingene og endringen i forbruk.',bg=PANEL,fg=MUTED,justify='left').pack(anchor='w',pady=15)
  def choose_driver(self,d):
   self.focus_driver=(d['course'],d['vehicle'],d['driver'])
   for child in self.detail.winfo_children():child.destroy()
   tk.Label(self.detail,text=d['driver'],bg=PANEL,fg=TEXT,font=('Segoe UI',23,'bold')).pack(anchor='w');tk.Label(self.detail,text='UTVIKLING · TUR 1–5',bg=PANEL,fg=TEAL,font=('Segoe UI',10,'bold')).pack(anchor='w',pady=(4,15))
   ds=sorted([r for r in self.rows if (self.compare_trips is None or r['trip'] in self.compare_trips) and (r['course'],r['vehicle'],r['driver'])==self.focus_driver],key=lambda r:r['trip'])
   chips=tk.Frame(self.detail,bg=PANEL);chips.pack(fill='x')
   for n in range(1,6):
    r=next((x for x in ds if x['trip']==n),None)
    tk.Button(chips,text=str(n),bg=TEAL if r and n==d['trip'] else EDGE,fg=BG if r and n==d['trip'] else TEXT,relief='flat',font=('Segoe UI',13,'bold'),width=4,state='normal' if r else 'disabled',command=lambda r=r:self.choose_driver(r)).pack(side='left',padx=3)
   canvas=tk.Canvas(self.detail,height=190,bg=PANEL,highlightthickness=0);canvas.pack(fill='x',pady=14);canvas.bind('<Configure>',lambda e:self.draw_curve(canvas,ds))
   first,last=metrics(ds[0]),metrics(ds[-1]);delta=last['forbruk10']-first['forbruk10'];pct=100*delta/first['forbruk10'] if first['forbruk10'] else None
   summary='Første registrerte tur' if len(ds)==1 else f"Forbruk: {delta:+.3f} L/10 km"+(f' ({pct:+.1f} %)' if pct is not None else '')
   tk.Label(self.detail,text=summary,bg=PANEL,fg=TEAL if delta<=0 else GOLD,font=('Segoe UI',13,'bold')).pack(anchor='w')
   tk.Label(self.detail,text=f"Vurderinger · {trip_name(d['trip'])}",bg=PANEL,fg=MUTED).pack(anchor='w',pady=(20,8))
   for k in QUAL:
    f=tk.Frame(self.detail,bg=PANEL);f.pack(fill='x',pady=4);tk.Label(f,text={'avpassing':'Fartsavpassing','økning':'Fartsøkning'}.get(k,k.capitalize()),bg=PANEL,fg=TEXT).pack(side='left');tk.Label(f,text='Middels' if d[k]=='Middel' else d[k],bg=PANEL,fg={'Bra':TEAL,'Middel':GOLD,'Svak':'#bb414e'}[d[k]],font=('Segoe UI',11,'bold')).pack(side='right')
   tk.Label(self.detail,text=f"{d.get('date','')} {d.get('start_time','')} · Lærer: {d.get('teacher','')}",bg=PANEL,fg=MUTED,wraplength=330,justify='left').pack(anchor='w',pady=6)
   tk.Label(self.detail,text=d.get('notes',''),bg=PANEL,fg=MUTED,wraplength=330,justify='left').pack(anchor='w',pady=12)
  def draw_curve(self,c,rows):
   c.delete('all');w=max(c.winfo_width(),280);h=c.winfo_height();vals=[metrics(r)['forbruk10'] for r in rows];hi=max(vals+[.01]);pts=[]
   for j in range(4):
    y=35+j*(h-65)/3;c.create_line(40,y,w-25,y,fill=EDGE)
   for r,v in zip(rows,vals):
    x=45+(r['trip']-1)*(w-75)/4;y=h-35-v/hi*(h-75);pts.extend([x,y]);c.create_oval(x-5,y-5,x+5,y+5,fill=TEAL,outline=TEAL);c.create_text(x,y-17,text=f'{v:.3f}',fill=TEXT,font=('Segoe UI',10));c.create_text(x,h-12,text=f"Tur {r['trip']}",fill=MUTED)
   if len(pts)>2:c.create_line(*pts,fill=TEAL,width=3)
  def bigscreen(self):
   self.live_display=None
   super().bigscreen()
   from live_display import LiveDisplay
   self.live_display=LiveDisplay(self,self.display)
   self.live_display.mode=self.mode.get()
   self.live_display.paint()
  def paint_display(self):
   if self.live_display and self.display and self.display.winfo_exists():self.live_display.paint()
 return ClassroomApp
