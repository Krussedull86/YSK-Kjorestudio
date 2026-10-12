"""PC registration workflow, using the same payload and validation as Android."""
import datetime,time
import tkinter as tk
from tkinter import ttk,messagebox
from course_setup import trip_number,course_config
from distribution import validate_run

class ElapsedClock:
 def __init__(self):self.elapsed=0;self.started=None
 def start(self,now):
  if self.started is None:self.started=now
 def stop(self,now):
  if self.started is not None:self.elapsed+=max(0,now-self.started);self.started=None
 def seconds(self,now):return self.elapsed+(max(0,now-self.started) if self.started is not None else 0)

def matching(rows,driver,course,vehicle,trip):
 return [r for r in rows if (r['driver'],r['course'],r['vehicle'],r['trip'])==(driver.strip(),course.strip(),vehicle.strip(),trip)]

def manual_run(config,started,events,finished):
 return validate_run(dict(version=1,expected_minutes=config['expected_minutes'],deadlines=config['deadlines'],started_at=started,events=events,finished_minutes=finished))

from trip_times import clock_text,clock_minutes

class PCWorkflow:
 def __init__(self,app):
  self.app=app;self.clock=ElapsedClock();self.loading=False
  bar=ttk.Frame(app.register_frame);bar.grid(row=16,column=0,columnspan=4,sticky='ew',padx=8,pady=8)
  self.status=tk.StringVar(value='Tid: 00:00:00');ttk.Label(bar,textvariable=self.status).pack(side='left',padx=8)
  for label,fn in [('Start / fortsett',self.start),('Pause',self.pause),('Stopp',self.stop),('+ Unødig stopp',self.add_stop),('Hent valgt aktivitet',self.lookup),('Etterregistrer stopp',self.distribution)]:ttk.Button(bar,text=label,command=fn).pack(side='left',padx=3)
  for box in [*app.catalog_boxes.values(),app.trip_box]:box.bind('<<ComboboxSelected>>',lambda e:self.lookup(),add='+')
  self.auto_time=tk.BooleanVar(value=True);self.time_hint=tk.StringVar(value='Skriv start og slutt med timer:minutter, eller skriv forbrukt tid direkte i minutter.')
  timing=ttk.Frame(app.register_frame);timing.grid(row=17,column=0,columnspan=4,sticky='ew',padx=8,pady=5)
  ttk.Checkbutton(timing,text='Beregn minutter fra start og slutt',variable=self.auto_time,command=self.recalculate).pack(side='left')
  ttk.Label(timing,textvariable=self.time_hint,foreground='#16803c',wraplength=650).pack(side='left',padx=12)
  for key in ('start_time','end_time'):
   app.time_entries[key].bind('<KeyRelease>',lambda e:self.recalculate())
   app.time_entries[key].bind('<FocusOut>',lambda e:self.recalculate())
  app.time_entries['minutes'].bind('<KeyRelease>',lambda e:self.auto_time.set(False))
  app.root.after(500,self.tick)
 def recalculate(self):
  if not self.auto_time.get():self.time_hint.set('Manuelle minutter brukes.');return
  try:
   start=self.app.fields['start_time'].get();end=self.app.fields['end_time'].get();minutes=clock_minutes(start,end)
   if minutes is not None:
    self.app.fields['minutes'].set(str(minutes));self.time_hint.set(f'Beregnet: {minutes} minutter'+(' · slutt neste dag' if clock_text(end)<clock_text(start) else ''))
  except ValueError as error:self.time_hint.set(str(error))
 def prepare(self,d):
  for k in ('start_time','end_time'):d[k]=clock_text(d.get(k,''))
  if self.auto_time.get():
   minutes=clock_minutes(d['start_time'],d['end_time'])
   if minutes is not None:d['minutes']=minutes;self.app.fields['minutes'].set(str(minutes))
  d['duration_source']='clock' if self.auto_time.get() else 'manual'
  return d
 def tick(self):
  if not self.app.root.winfo_exists():return
  total=int(self.clock.seconds(time.monotonic()));self.status.set(f'Tid: {total//3600:02}:{total//60%60:02}:{total%60:02}'+(' · pågår' if self.clock.started is not None else ''))
  self.app.root.after(500,self.tick)
 def start(self):
  if not self.clock.seconds(time.monotonic()):
   now=datetime.datetime.now();self.app.fields['date'].set(now.date().isoformat());self.app.fields['start_time'].set(now.strftime('%H:%M'))
  self.clock.start(time.monotonic())
 def pause(self):self.clock.stop(time.monotonic())
 def stop(self):
  self.pause();self.auto_time.set(False);self.app.fields['end_time'].set(datetime.datetime.now().strftime('%H:%M'));self.app.fields['minutes'].set(f'{self.clock.elapsed/60:.4f}')
 def add_stop(self):
  try:self.app.fields['stops'].set(str(int(self.app.fields['stops'].get() or 0)+1))
  except ValueError:messagebox.showerror('Stopp','Skriv antall stopp som et heltall.')
 def lookup(self):
  if self.loading or self.clock.started is not None:return
  a=self.app;f=a.fields;rows=matching(a.store.all(True),f['driver'].get(),f['course'].get(),f['vehicle'].get(),trip_number(f['trip'].get()))
  if not rows or rows[0]['id']==a.edit_id:return
  dirty=any(f[k].get().strip() for k in ('minutes','km','liters','fuel_per_100','notes'))
  if dirty and not messagebox.askyesno('Registrert aktivitet','Denne aktiviteten finnes. Åpne de lagrede dataene og erstatte målingene i skjemaet?'):return
  self.loading=True
  try:a.open_trip(rows[0])
  finally:self.loading=False
 def distribution(self):
  a=self.app
  if trip_number(a.fields['trip'].get())!=4:return messagebox.showinfo('Distribusjon','Velg distribusjonstur først.')
  old=a.edit_distribution;config=course_config(a.store,a.fields['course'].get())['distribution_plan']
  if old:config={'expected_minutes':old['expected_minutes'],'deadlines':old['deadlines']}
  if not config['deadlines']:return messagebox.showinfo('Distribusjon','Angi antall stopp og forventet totaltid i Kursoppsett først.')
  win=tk.Toplevel(a.root);win.title('Etterregistrer / rediger distribusjonsstopp');win.geometry('850x650')
  ttk.Label(win,text='Minutter fra start ved skolen · la uregistrerte stopp og retur stå tomme',font=('Segoe UI',15,'bold')).pack(pady=10)
  canvas=tk.Canvas(win,highlightthickness=0);scroll=ttk.Scrollbar(win,command=canvas.yview);scroll.pack(side='right',fill='y');canvas.configure(yscrollcommand=scroll.set);canvas.pack(fill='both',expand=True);form=ttk.Frame(canvas,padding=12);canvas.create_window(0,0,window=form,anchor='nw');form.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
  for j,label in enumerate(('Stopp','Fra start (min)','Status','Kommentar')):ttk.Label(form,text=label).grid(row=0,column=j,padx=7,pady=5)
  variables=[]
  for i in range(len(config['deadlines'])):
   e=old['events'][i] if old and i<len(old['events']) else {};mins=tk.StringVar(value=str(e.get('elapsed_minutes','')));status=tk.StringVar(value='Avbrutt' if e.get('status')=='aborted' else 'Rygget til rampe');reason=tk.StringVar(value=e.get('reason',''));variables.append((mins,status,reason));ttk.Label(form,text=str(i+1)).grid(row=i+1,column=0);ttk.Entry(form,textvariable=mins,width=14).grid(row=i+1,column=1,padx=7,pady=5);ttk.Combobox(form,textvariable=status,values=['Rygget til rampe','Avbrutt'],state='readonly',width=20).grid(row=i+1,column=2,padx=7);ttk.Entry(form,textvariable=reason,width=40).grid(row=i+1,column=3,padx=7)
  total=tk.StringVar(value=str(old['finished_minutes']) if old and old['finished_minutes'] is not None else a.fields['minutes'].get());row=len(variables)+2;ttk.Label(form,text='Tilbake ved skolen (min fra start)').grid(row=row,column=0,columnspan=2);ttk.Entry(form,textvariable=total).grid(row=row,column=2,pady=10)
  def done():
   try:
    started=old['started_at'] if old else int(datetime.datetime.fromisoformat(a.fields['date'].get()+'T'+(a.fields['start_time'].get() or '00:00')).timestamp()*1000)
    events=[]
    for i,(m,s,r) in enumerate(variables):
     if not m.get().strip():
      if any(v[0].get().strip() for v in variables[i+1:]):raise ValueError('Registrer stoppene i rekkefølge.')
      break
     events.append(dict(stop=i+1,elapsed_minutes=m.get().replace(',','.'),status='aborted' if s.get()=='Avbrutt' else 'ramp',reason=r.get()))
    log=manual_run(config,started,events,total.get().replace(',','.') if total.get().strip() else None);a.edit_distribution=log;a.fields['minutes'].set(str(log['finished_minutes']) if log['finished_minutes'] is not None else '');a.editlabel.set('Stopplogg oppdatert – trykk Lagre tur');win.destroy()
   except Exception as error:messagebox.showerror('Kontroller stopploggen',str(error),parent=win)
  ttk.Button(form,text='Bruk stopplogg i skjemaet',command=done).grid(row=row+1,column=1,columnspan=3,pady=12)
