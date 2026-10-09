"""Full classroom delivery timeline, including aborted and pending stops."""
import tkinter as tk
from tkinter import ttk
from distribution import validate_run,rows,summary,return_minutes

def show(parent,trip):
 data=validate_run(trip['distribution']);window=tk.Toplevel(parent);window.title('Distribusjon · '+trip['driver']);window.geometry('1100x600')
 ttk.Label(window,text=trip['driver']+' · '+trip['course'],font=('Segoe UI',18,'bold')).pack(anchor='w',padx=16,pady=10)
 ttk.Label(window,text=summary(data)).pack(anchor='w',padx=16)
 finished=data['finished_minutes'];ttk.Label(window,text=f"Forventet skole → skole: {data['expected_minutes']:.1f} min · Faktisk skole → skole: "+('Pågår' if finished is None else f'{finished:.1f} min')).pack(anchor='w',padx=16,pady=8)
 ttk.Label(window,text='Turen går fra skole til skole. Returen måles fra siste registrerte stopp og inkluderer eventuell lasting/venting der. Alle tider er minutter.').pack(anchor='w',padx=16)
 box=ttk.Frame(window,padding=12);box.pack(fill='both',expand=True);cols=['Stopp','Status','Fra forrige','Fra start','Kommentar'];table=ttk.Treeview(box,columns=cols,show='headings')
 for col in cols:table.heading(col,text=col);table.column(col,width=100 if col!='Kommentar' else 220,minwidth=70)
 sy=ttk.Scrollbar(box,orient='vertical',command=table.yview);sx=ttk.Scrollbar(box,orient='horizontal',command=table.xview);table.configure(yscrollcommand=sy.set,xscrollcommand=sx.set);table.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew');box.rowconfigure(0,weight=1);box.columnconfigure(0,weight=1);table.tag_configure('aborted',foreground='#bb414e')
 events=rows(data)
 for i,deadline in enumerate(data['deadlines'],1):
  if i<=len(events):
   e=events[i-1];table.insert('','end',tags=('aborted',) if e['status']=='aborted' else (),values=[i,'Rygget til rampe' if e['status']=='ramp' else 'AVBRUTT',f"{e['segment_minutes']:.1f}",f"{e['elapsed_minutes']:.1f}",e['reason']])
  else:table.insert('','end',values=[i,'Ikke registrert','—','—',''])
 if finished is not None:table.insert('','end',values=['Retur','Tilbake ved skolen',f'{return_minutes(data):.1f}',f'{finished:.1f}','Siste registrerte stopp → skole'])
 elif len(events)==len(data['deadlines']):table.insert('','end',values=['Retur','Pågår','—','—','Avslutt tur først ved skolen'])
 ttk.Button(window,text='Lukk',command=window.destroy).pack(pady=8)
 return window
