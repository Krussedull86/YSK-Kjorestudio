import tkinter as tk
from tkinter import ttk,messagebox,filedialog
import os,sys,socket,secrets,threading,json,csv,ctypes,datetime
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from core import Store,QUAL,WEIGHTS,metrics,ranking,changes,missing_fields
from course_setup import NAMES,trip_number,trip_name,course_count,save_course,course_names,course_config
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
DATA=Path(os.getenv('LOCALAPPDATA',Path.home()))/('YSK_Kjorestudio_Demo' if '--demo' in sys.argv else 'YSK_Kjorestudio')

def monitors(root):
 out=[]
 if sys.platform=='win32':
  from ctypes import wintypes
  cbtype=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HANDLE,wintypes.HDC,ctypes.POINTER(wintypes.RECT),wintypes.LPARAM)
  def cb(h,dc,r,p):
   v=r.contents;out.append((v.left,v.top,v.right-v.left,v.bottom-v.top));return True
  ctypes.windll.user32.EnumDisplayMonitors(None,None,cbtype(cb),0)
 return out or [(0,0,root.winfo_screenwidth(),root.winfo_screenheight())]

def server(store):
 token=secrets.token_hex(8)
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def reply(self,code,obj):
   body=json.dumps(obj,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  def do_GET(self):
   if self.path=='/api/choices':
    if not secrets.compare_digest(self.headers.get('X-Token',''),token):return self.reply(403,{'error':'Feil tilgangskode'})
    return self.reply(200,{k:sorted({d[k] for d in store.all()}) for k in ['driver','course','vehicle']})
   if self.path.split('?')[0]!='/':return self.reply(404,{'error':'Ikke funnet'})
   body=(ROOT/'mobile.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  def do_POST(self):
   if self.path!='/api/trips':return self.reply(404,{'error':'Ikke funnet'})
   if not secrets.compare_digest(self.headers.get('X-Token',''),token):return self.reply(403,{'error':'Feil tilgangskode'})
   try:
    n=int(self.headers.get('Content-Length','0'))
    if not 0<n<=16000:raise ValueError('Ugyldig registreringsstørrelse')
    d=json.loads(self.rfile.read(n));result=store.save(d);self.reply(200,{'id':result['id']})
   except (ValueError,KeyError,TypeError) as e:self.reply(400,{'error':str(e)})
   except Exception:self.reply(500,{'error':'Kunne ikke lagre. Prøv igjen.'})
 httpd=ThreadingHTTPServer(('0.0.0.0',8765),Handler);httpd.daemon_threads=True
 threading.Thread(target=httpd.serve_forever,daemon=True).start()
 return httpd,token

class App:
 def __init__(self,root):
  self.root=root;self.store=Store(DATA/'ysk.db');self.edit_id=None;self.edit_distribution=None;self.display=None
  if '--demo' in sys.argv and not self.store.all():
   from demo import seed
   seed(self.store)
  root.title('YSK Kjørestudio · Lokal registrering og rangering');root.geometry('1250x820');root.minsize(1000,680)
  ttk.Style().theme_use('clam');ttk.Style().configure('Treeview',rowheight=29)
  header=ttk.Frame(root,padding=12);header.pack(fill='x')
  ttk.Label(header,text='YSK KJØRESTUDIO',font=('Segoe UI',22,'bold')).pack(side='left')
  ttk.Button(header,text='Sikkerhetskopi',command=self.backup).pack(side='right',padx=4)
  ttk.Button(header,text='Eksporter CSV',command=self.export).pack(side='right',padx=4)
  self.screens=monitors(root);self.screen=tk.StringVar(value='1');ttk.Button(header,text='Åpne storskjerm',command=self.bigscreen).pack(side='right',padx=4)
  ttk.Combobox(header,textvariable=self.screen,values=[str(i+1) for i in range(len(self.screens))],width=3,state='readonly').pack(side='right');ttk.Label(header,text='Skjerm: ').pack(side='right')
  self.notice=tk.StringVar();ttk.Label(root,textvariable=self.notice,padding=10).pack(fill='x')
  try:
   self.http,self.token=server(self.store)
   try:
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:s.connect(('192.0.2.1',80));ip=s.getsockname()[0]
   except OSError:ip=socket.gethostbyname(socket.gethostname())
   self.notice.set(f'Mobil: http://{ip}:8765   |   Tilgangskode: {self.token}   |   Samme Wi-Fi/hotspot. PC må være på.')
  except OSError as e:self.http=None;self.notice.set(f'Mobilserver startet ikke: {e}. PC-registrering virker fortsatt.')
  nb=ttk.Notebook(root);nb.pack(fill='both',expand=True,padx=12,pady=8)
  register=ttk.Frame(nb,padding=15);overview=ttk.Frame(nb,padding=10);progress=ttk.Frame(nb,padding=10);settings=ttk.Frame(nb,padding=15)
  for frame,title in [(register,'Registrer / rediger'),(overview,'Rangering og turer'),(progress,'Utvikling tur 1–5'),(settings,'Vekter og forklaring')]:nb.add(frame,text=title)
  self.nb=nb;self.register_frame=register;self.fields={}
  self.catalog_boxes={};self.rating_positions={};self.compare_trips=None
  labels=[('driver','Sjåfør ▾'),('course','Kurs / gruppe ▾'),('vehicle','Bil / sammenligningsgruppe ▾'),('trip','Tur (1–5)'),('date','Dato (ÅÅÅÅ-MM-DD)'),('start_time','Starttid (TT:MM)'),('minutes','Forbrukt tid (min eller mm:ss)'),('km','Kjørt distanse (km)'),('liters','Forbruk totalt (liter)'),('stops','Antall unødige stopp'),('average_speed','Gjennomsnitt km/t (valgfritt)'),('teacher','Lærer / signatur (navn eller initialer)'),('notes','Notater'),('trafikksikkerhet','Trafikksikkerhet'),('avpassing','Fartsavpassing'),('økning','Fartsøkning'),('komfort','Komfort')]
  for i,(k,label) in enumerate(labels):
   col=0 if i<9 else 2;row=i if i<9 else i-9
   ttk.Label(register,text=label).grid(row=row,column=col,sticky='w',padx=8,pady=6)
   v=tk.StringVar(value='' if k in QUAL else NAMES[0] if k=='trip' else '0' if k=='stops' else datetime.date.today().isoformat() if k=='date' else '')
   self.fields[k]=v
   if k in QUAL:self.rating_positions[k]=(row,col+1)
   if k in QUAL or k=='trip':widget=ttk.Combobox(register,textvariable=v,values=['','Bra','Middel','Svak','-'] if k in QUAL else NAMES,state='readonly',width=24)
   elif k in ['driver','course','vehicle']:
    widget=ttk.Combobox(register,textvariable=v,width=30);self.catalog_boxes[k]=widget
   else:widget=ttk.Entry(register,textvariable=v,width=32)
   if k=='trip':self.trip_box=widget;widget.configure(width=40)
   widget.grid(row=row,column=col+1,sticky='ew',padx=8,pady=6)
  self.fields['course'].trace_add('write',lambda *a:self.update_trip_choices())
  ttk.Button(register,text='Vis distribusjonsstopp',command=self.show_edit_distribution).grid(row=12,column=3,pady=6)
  ttk.Button(register,text='Kursoppsett',command=self.setup_course).grid(row=12,column=1,pady=6)
  self.preview=tk.StringVar(value='Forbruk per 10 km beregnes fra liter og distanse. Kjørepoeng vises i rangeringen.')
  ttk.Label(register,textvariable=self.preview,wraplength=600).grid(row=9,column=0,columnspan=4,pady=6)
  def preview(*args):
   try:self.preview.set(f"Forbruk per 10 km: {10*float(self.fields['liters'].get().replace(',','.'))/float(self.fields['km'].get().replace(',','.')):.2f} liter · Kjørepoeng beregnes i rangeringen")
   except (ValueError,ZeroDivisionError):self.preview.set('Forbruk per 10 km beregnes fra liter og distanse. Kjørepoeng vises i rangeringen.')
  for k in ['liters','km']:self.fields[k].trace_add('write',preview)
  ttk.Button(register,text='Lagre tur',command=self.save).grid(row=10,column=1,pady=12,sticky='ew')
  ttk.Button(register,text='Ny registrering',command=self.reset).grid(row=10,column=3,pady=12,sticky='ew')
  self.editlabel=tk.StringVar(value='Ny tur');ttk.Label(register,textvariable=self.editlabel).grid(row=11,column=1,columnspan=3)
  filters=ttk.Frame(overview);filters.pack(fill='x');self.filters={}
  for k,label in [('course','Kurs'),('vehicle','Kjøretøy'),('trip','Tur')]:
   ttk.Label(filters,text=label).pack(side='left',padx=4);v=tk.StringVar(value='Alle');box=ttk.Combobox(filters,textvariable=v,width=19,state='readonly');box.pack(side='left',padx=4);box.bind('<<ComboboxSelected>>',lambda e:self.refresh());self.filters[k]=(v,box)
  ttk.Button(filters,text='Rediger valgt',command=self.edit).pack(side='right');ttk.Button(filters,text='Slett valgt',command=self.delete).pack(side='right',padx=8)
  self.table=self.tree(overview,['Sjåfør','Kurs','Kjøretøy','Tur','Poeng','Tid min','min/km','L/10 km','km/t','Stopp','Trafikksikkerhet','Fartsavpassing','Fartsøkning','Komfort'])
  self.table.tag_configure('incomplete',foreground='#d22837')
  self.trip_warning=tk.StringVar();ttk.Label(overview,textvariable=self.trip_warning,foreground='#d22837').pack(fill='x',pady=6)
  self.table.bind('<Double-1>',lambda e:self.edit())
  ttk.Label(overview,text='Poeng gjelder samme kurs, kjøretøygruppe og turnummer. Bruk sammenlignbare ruter, last og forhold. Fart gir ingen poeng.').pack(fill='x',pady=8)
  self.progress=self.tree(progress,['Sjåfør','Kurs','Kjøretøy','Fra → til','Δ min/km','Δ L/10 km','Forbruk %','Δ km/t','Δ stopp/km','Trafikksikkerhet','Fartsavpassing','Fartsøkning','Komfort'])
  self.canvas=tk.Canvas(progress,height=180,bg='#102132',highlightthickness=0);self.canvas.pack(fill='x',pady=8);self.progress.bind('<<TreeviewSelect>>',lambda e:self.chart())
  ttk.Label(progress,text='Endring fra første til siste registrerte tur. Minus i tid, forbruk og stopp = reduksjon. Velg sjåfør for forbrukskurve.').pack(fill='x')
  self.weights={}
  for i,k in enumerate(WEIGHTS):
   ttk.Label(settings,text=k.capitalize()).grid(row=i,column=0,sticky='w',padx=8,pady=6);v=tk.StringVar(value=str(self.store.settings()[k]));self.weights[k]=v;ttk.Entry(settings,textvariable=v,width=10).grid(row=i,column=1,padx=8)
  ttk.Button(settings,text='Lagre vekter',command=self.save_weights).grid(row=8,column=1,pady=12)
  explanation='Bra = 100, Middel = 50, Svak = 0.\nTallkriterier: lavest verdi i sammenligningsgruppen = 100, høyest = 0.\nLik verdi for alle = 100. Poeng er relativ rangering, ikke en faglig godkjenning.\nTomme felt = uferdig tur, lagres lokalt med rød prikk.\n- = bevisst utelatt. Slike turer vises uten samlet poeng; ingen manglende verdi regnes som null.\nSamlet poeng er vektet gjennomsnitt. Tid må aldri belønne utrygg kjøring.\nGjennomsnittsfart kan legges inn eller beregnes; forbruk per 10 km = 10 × liter / km; stopp normaliseres per km.\nFartsøkning vurderes med Bra, Middels eller Svak.\nAndroid-appen lagrer lokalt og sender via Supabase.\nData: '+str(DATA)
  ttk.Label(settings,text=explanation,justify='left').grid(row=0,column=2,rowspan=10,padx=30,sticky='nw')
  root.protocol('WM_DELETE_WINDOW',self.close);self.refresh();root.after(2000,self.poll)
 def tree(self,parent,cols):
  box=ttk.Frame(parent);box.pack(fill='both',expand=True);t=ttk.Treeview(box,columns=cols,show='headings',height=10)
  for c in cols:t.heading(c,text=c);t.column(c,width=110,minwidth=65)
  sy=ttk.Scrollbar(box,orient='vertical',command=t.yview);sx=ttk.Scrollbar(box,orient='horizontal',command=t.xview);t.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
  t.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew');box.rowconfigure(0,weight=1);box.columnconfigure(0,weight=1);return t
 def update_trip_choices(self):
  count=course_count(self.store,self.fields['course'].get())
  self.trip_box['values']=NAMES[:count]
  if not self.edit_id and trip_number(self.fields['trip'].get())>count:self.fields['trip'].set(NAMES[0])
 def setup_course(self):
  dialog=tk.Toplevel(self.root);dialog.title('Kursoppsett')
  name=tk.StringVar(value=self.fields['course'].get());count=tk.StringVar(value=str(course_count(self.store,name.get())))
  stop_count=tk.StringVar();total=tk.StringVar()
  def load(*args):
   config=course_config(self.store,name.get());p=config['distribution_plan'];count.set(str(config['active_trips']));stop_count.set(str(p['stop_count']));total.set(str(p['expected_minutes']))
  load();name.trace_add('write',load)
  ttk.Label(dialog,text='Kursnavn').pack();ttk.Combobox(dialog,textvariable=name,values=course_names(self.store)).pack(padx=20,pady=8)
  ttk.Label(dialog,text='Antall aktive turer (tur 1 til valgt antall)').pack();ttk.Combobox(dialog,textvariable=count,values=[1,2,3,4,5],state='readonly').pack(padx=20,pady=8)
  ttk.Label(dialog,text='\n'.join(f'{i}. {n}' for i,n in enumerate(NAMES,1))).pack(padx=20,pady=8)
  for label,var in [('Antall distribusjonsstopp (0–30; 0 = av)',stop_count),('Forventet totaltid skole → skole (minutter)',total)]:
   ttk.Label(dialog,text=label).pack(padx=20);ttk.Entry(dialog,textvariable=var,width=55).pack(padx=20,pady=5)
  def done():
   try:
    from distribution import plan
    distribution_plan=plan(stop_count.get(),total.get())
    course=name.get().strip();number=int(count.get())
    if not course or len(course)>100 or number not in range(1,6):raise ValueError('Velg kursnavn og 1–5 turer.')
    if hasattr(self,'management') and self.cloud_panel.receiver.load():
     def saved(result):save_course(self.store,course,number,distribution_plan);self.fields['course'].set(course);self.update_trip_choices();self.refresh();dialog.destroy()
     self.management.run(lambda:self.cloud_panel.receiver.admin('course_setup_save',name=course,active_trips=number,distribution_plan=distribution_plan),saved)
    else:save_course(self.store,course,number,distribution_plan);self.fields['course'].set(course);self.update_trip_choices();self.refresh();dialog.destroy()
   except Exception as e:messagebox.showerror('Kursoppsett',str(e))
  ttk.Button(dialog,text='Lagre kursoppsett',command=done).pack(pady=12)
 def show_distribution(self,d,parent=None):
  from distribution_view import show
  return show(parent or self.root,d)
 def show_edit_distribution(self):
  if self.edit_distribution is None:return messagebox.showinfo('Distribusjon','Åpne en registrert distribusjonstur med stopplogg først.')
  self.show_distribution({'driver':self.fields['driver'].get(),'course':self.fields['course'].get(),'distribution':self.edit_distribution})
 def compare_dialog(self):
  dialog=tk.Toplevel(self.root);dialog.title('Turer som sammenlignes');values=[]
  for n,name in enumerate(NAMES,1):
   var=tk.BooleanVar(value=self.compare_trips is None or n in self.compare_trips);values.append(var);ttk.Checkbutton(dialog,text=name,variable=var).pack(anchor='w',padx=20,pady=5)
  def done():
   self.compare_trips=[n for n,var in enumerate(values,1) if var.get()];self.refresh();dialog.destroy()
  ttk.Button(dialog,text='Bruk sammenligning',command=done).pack(pady=12)
 def reset(self):
  self.edit_id=None;self.edit_distribution=None;self.edit_revision='';self.editlabel.set('Ny tur')
  for k,v in self.fields.items():
   if k not in ['course','vehicle']:v.set('' if k in QUAL else NAMES[0] if k=='trip' else '0' if k=='stops' else datetime.date.today().isoformat() if k=='date' else '')
 def save(self):
  try:
   d={k:v.get() for k,v in self.fields.items()};d['id']=self.edit_id;d['trip']=trip_number(d['trip'])
   if self.edit_distribution is not None:d['distribution']=self.edit_distribution
   if not self.edit_id and d['trip']>course_count(self.store,d['course']):raise ValueError('Denne turen er ikke aktivert på kurset.')
   validated=self.store.validate(d)
   if missing_fields(validated) and getattr(self,'edit_revision',''):
    raise ValueError('Skyredigering: fullfør feltene eller bruk - før lagring. Nye uferdige turer kan lagres lokalt.')
   if not missing_fields(validated) and hasattr(self,'management') and self.cloud_panel.receiver.load():
    self.management.save(d,getattr(self,'edit_revision',''));return
   self.store.save(validated);self.reset();self.refresh();messagebox.showinfo('Lagret','Uferdig tur lagret lokalt – se rød prikk i turoversikten.' if missing_fields(validated) else 'Turen er lagret lokalt på PC.')
  except Exception as e:messagebox.showerror('Kunne ikke lagre',str(e))
 def edit(self):
  ids=self.table.selection()
  if not ids:return
  self.open_trip(next(d for d in self.store.all(True) if d['id']==ids[0]))
 def open_trip(self,d):
  self.edit_id=d['id'];self.edit_distribution=d.get('distribution');self.edit_revision=''
  if hasattr(self,'cloud_panel'):
   remote=self.cloud_panel.receiver.remote(d['id']);self.edit_revision=remote.get('revision','') if remote else ''
  for k,v in self.fields.items():v.set(trip_name(d['trip']) if k=='trip' else d.get(k,''))
  self.update_trip_choices()
  self.editlabel.set('Redigerer eksisterende tur');self.nb.select(self.register_frame)
 def delete(self):
  ids=self.table.selection()
  if not ids:return
  if hasattr(self,'management'):
   remote=self.cloud_panel.receiver.remote(ids[0])
   if remote:
    if messagebox.askyesno('Slett tur','Flytte den valgte turen til papirkurven i skyen?'):
     self.management.action('trip_delete',id=ids[0],expected_revision=remote['revision'])
    return
  if messagebox.askyesno('Slett lokal tur','Slette den lokale turen? En sikkerhetskopi tas først.'):
   self.store.backup(DATA/('før_sletting_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.db'));self.store.delete(ids[0]);self.refresh()
 def filtered(self,rows):return [d for d in rows if (self.compare_trips is None or d['trip'] in self.compare_trips) and all(v.get()=='Alle' or str(d[k])==str(trip_number(v.get()) if k=='trip' else v.get()) for k,(v,box) in self.filters.items())]
 def refresh(self):
  self.update_trip_choices()
  rows=self.store.all();self.rows=rows;self.all_rows=self.store.all(True)
  unfinished=sum(bool(missing_fields(d)) for d in self.all_rows)
  self.trip_warning.set(f'● {unfinished} uferdige turer – åpne dem for å fullføre. Bruk - for bevisst utelatte felt.' if unfinished else '')
  for k,box in self.catalog_boxes.items():box['values']=sorted({d[k] for d in self.store.all(True)} | (set(course_names(self.store)) if k=='course' else set()),key=str.casefold)
  for k,(v,box) in self.filters.items():
   values=['Alle']+(NAMES if k=='trip' else sorted({str(d[k]) for d in self.store.all(True)} | (set(course_names(self.store)) if k=='course' else set())));box['values']=values
   if v.get() not in values:v.set('Alle')
  selected=self.table.selection();self.table.delete(*self.table.get_children());self.ranked=self.filtered(ranking(rows,self.store.settings()))
  for d in self.ranked:self.table.insert('', 'end',iid=d['id'],values=[d['driver'],d['course'],d['vehicle'],trip_name(d['trip']),d['score'],d['minutes'],f"{d['tid']:.3f}",f"{d['forbruk10']:.2f}",f"{d['fart']:.1f}",int(d['stops']),*[d[k] for k in QUAL]])
  scored_ids={d['id'] for d in rows}
  for d in self.filtered(self.store.all(True)):
   if d['id'] not in scored_ids:self.table.insert('', 'end',iid=d['id'],tags=('incomplete',) if missing_fields(d) else (),values=[('● ' if missing_fields(d) else '✓ ')+d['driver'],d['course'],d['vehicle'],trip_name(d['trip']),'Ikke ferdig' if missing_fields(d) else '—',d['minutes'],'—','—','—',d['stops'],*[d[k] for k in QUAL]])
  if selected and self.table.exists(selected[0]):self.table.selection_set(selected)
  psel=self.progress.selection();self.progress.delete(*self.progress.get_children());self.change_rows=changes(rows)
  for i,d in enumerate(self.change_rows):
   c,v,n=d['group'];p=d['percent']['forbruk'];self.progress.insert('','end',iid=str(i),values=[n,c,v,f"{d['first']['trip']} → {d['last']['trip']}",f"{d['delta']['tid']:+.3f}",f"{d['delta']['forbruk10']:+.2f}",'—' if p is None else f'{p:+.1f}%',f"{d['delta']['fart']:+.1f}",f"{d['delta']['stopp']:+.3f}",*[d['ratings'][k] for k in QUAL]])
  if psel and self.progress.exists(psel[0]):self.progress.selection_set(psel);self.chart()
  if self.display and self.display.winfo_exists():self.paint_display()
 def chart(self):
  self.canvas.delete('all');ids=self.progress.selection()
  if not ids:return
  d=self.change_rows[int(ids[0])];rows=[r for r in self.rows if (r['course'],r['vehicle'],r['driver'])==d['group']];rows.sort(key=lambda r:r['trip']);w=max(self.canvas.winfo_width(),500);vals=[metrics(r)['forbruk10'] for r in rows];high=max(vals+[0.01]);points=[]
  self.canvas.create_text(20,20,anchor='w',fill='white',text=f"{d['group'][2]} · Forbruk liter/10 km",font=('Segoe UI',12,'bold'))
  for r,val in zip(rows,vals):
   x=65+(r['trip']-1)*(w-130)/4;y=140-val/high*85;points.extend([x,y]);self.canvas.create_oval(x-5,y-5,x+5,y+5,fill='#56d1bc');self.canvas.create_text(x,y-15,text=f'{val:.3f}',fill='white');self.canvas.create_text(x,165,text=f"Tur {r['trip']}",fill='white')
  if len(points)>=4:self.canvas.create_line(*points,fill='#56d1bc',width=3)
 def save_weights(self):
  try:self.store.set_settings({k:v.get().replace(',','.') for k,v in self.weights.items()});self.refresh();messagebox.showinfo('Vekter','Vektene er lagret.')
  except Exception as e:messagebox.showerror('Ugyldige vekter',str(e))
 def fill_screen(self,window):
  x,y,w,h=self.screens[int(self.screen.get())-1]
  window.overrideredirect(True);window.geometry(f'{w}x{h}{x:+d}{y:+d}');window.update_idletasks()
  if sys.platform=='win32':
   from ctypes import wintypes
   user=ctypes.windll.user32;user.GetParent.argtypes=[wintypes.HWND];user.GetParent.restype=wintypes.HWND
   user.SetWindowPos.argtypes=[wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_uint]
   hwnd=user.GetParent(window.winfo_id()) or window.winfo_id()
   user.SetWindowPos(hwnd,wintypes.HWND(-1),x,y,w,h,0x0040|0x0020)
  else:window.attributes('-fullscreen',True)
  window.lift();window.focus_force()
 def bigscreen(self):
  if self.display and self.display.winfo_exists():self.display.destroy()
  self.screens=monitors(self.root)
  if int(self.screen.get())>len(self.screens):self.screen.set('1')
  self.display=tk.Toplevel(self.root);self.display.configure(bg='#f3f6fa');self.fill_screen(self.display)
  self.display.bind('<Escape>',lambda e:self.display.destroy());self.paint_display()
 def paint_display(self):
  for child in self.display.winfo_children():child.destroy()
  tk.Label(self.display,text='YSK · SJÅFØROVERSIKT',bg='#102132',fg='white',font=('Segoe UI',30,'bold')).pack(pady=20)
  selected=' · '.join(v.get() for v,b in self.filters.values());tk.Label(self.display,text=selected+'  |  Esc lukker visningen',bg='#102132',fg='#a7bdca',font=('Segoe UI',16)).pack()
  rows=self.ranked
  # When filters span groups, identify each group; never number as one global leaderboard.
  for d in rows[:12]:
   label=f"{d['driver']}   |   {d['course']} · {d['vehicle']} · tur {d['trip']}   |   {d['score']:.1f} poeng   |   {d['forbruk']:.3f} L/km"
   tk.Label(self.display,text=label,bg='#1a3348',fg='white',font=('Segoe UI',19),anchor='w',padx=20,pady=9).pack(fill='x',padx=35,pady=3)
  tk.Label(self.display,text=f'Viser {min(12,len(rows))} av {len(rows)} turer. Velg kurs, kjøretøy og tur på PC-en.',bg='#102132',fg='#a7bdca',font=('Segoe UI',14)).pack(pady=12)
 def backup(self):
  path=filedialog.asksaveasfilename(defaultextension='.db',initialfile='YSK_backup_'+datetime.date.today().isoformat()+'.db')
  if path:
   try:self.store.backup(path);messagebox.showinfo('Sikkerhetskopi','Sikkerhetskopien er lagret.')
   except Exception as e:messagebox.showerror('Feil',str(e))
 def export(self):
  path=filedialog.asksaveasfilename(defaultextension='.csv',initialfile='YSK_turer.csv')
  if path:
   try:
    rows=ranking(self.store.all(),self.store.settings())
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
     fields=['driver','course','vehicle','trip','minutes','km','liters','stops',*QUAL,'date','start_time','average_speed','teacher','notes','forbruk10','score','tid','forbruk','fart'];writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',delimiter=';');writer.writeheader();writer.writerows(rows)
    messagebox.showinfo('Eksport','CSV-filen er lagret.')
   except Exception as e:messagebox.showerror('Feil',str(e))
 def poll(self):
  if self.store.all(True)!=self.all_rows:self.refresh()
  self.root.after(2000,self.poll)
 def close(self):
  if hasattr(self,'cloud_panel'):self.cloud_panel.closed=True
  try:self.store.backup(DATA/'automatisk_backup.db')
  except Exception:pass
  if self.http:threading.Thread(target=self.http.shutdown,daemon=True).start()
  self.root.destroy()
if __name__=='__main__':
 if sys.platform=='win32':
  try:ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
  except Exception:pass
 from design import classroom_class
 from cloud_sync import Receiver,CloudPanel
 from auth_gate import LoginGate
 root=tk.Tk()
 receiver=Receiver(Store(DATA/'ysk.db'),DATA/'cloud_session.dpapi')
 def open_application():
  app=classroom_class(App)(root)
  app.authenticated=True
  def lock_application():
   if not app.authenticated:return
   app.authenticated=False
   if hasattr(app,'cloud_panel'):app.cloud_panel.closed=True
   root.withdraw()
   if app.display:
    try:app.display.destroy()
    except Exception:pass
   if app.http:
    app.http.shutdown();app.http.server_close()
   for timer_id in root.tk.call('after','info'):
    try:root.after_cancel(timer_id)
    except Exception:pass
   for widget in root.winfo_children():widget.destroy()
   LoginGate(root,receiver,open_application);root.deiconify()
  app.lock=lock_application
  app.cloud_panel=CloudPanel(app,DATA/'cloud_session.dpapi')
  from management import ManagementPanel
  app.management=ManagementPanel(app,app.cloud_panel.receiver)
  from admin_panel import AdminPanel
  app.admin_panel=AdminPanel(app,app.cloud_panel.receiver)
  from feedback_panel import FeedbackPanel
  app.feedback_panel=FeedbackPanel(app,app.cloud_panel.receiver,DATA)
  from updates import UpdatesPanel
  app.updates_panel=UpdatesPanel(app,app.cloud_panel.receiver,DATA)
 LoginGate(root,receiver,open_application)
 root.mainloop()
