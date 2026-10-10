"""Full classroom delivery timeline, including aborted and pending stops."""
import tkinter as tk
from tkinter import ttk,messagebox
from distribution import validate_run,rows,summary,return_minutes

def show(parent,trip,on_change=None):
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
 if on_change is not None:
  def edit():
   selected=table.selection()
   if not selected:return
   stop=table.item(selected[0],'values')[0]
   try:stop=int(stop)
   except ValueError:return
   if stop>len(data['events']):return
   e=data['events'][stop-1];dialog=tk.Toplevel(window);dialog.title('Endre stopp '+str(stop));status=tk.StringVar(value='Rygget til rampe' if e['status']=='ramp' else 'Avbrutt')
   ttk.Combobox(dialog,textvariable=status,values=['Rygget til rampe','Avbrutt'],state='readonly',width=30).pack(padx=16,pady=10)
   note=tk.Text(dialog,height=5,width=50);note.pack(padx=16,pady=8);note.insert('1.0',e['reason'])
   ttk.Label(dialog,text='Tidspunktet beholdes. Trykk Lagre tur etterpå.').pack(padx=16,pady=8)
   def apply():
    from distribution import edit_event
    try:
     changed=edit_event(data,stop,'ramp' if status.get()=='Rygget til rampe' else 'aborted',note.get('1.0','end-1c'));on_change(changed);dialog.destroy();window.destroy();show(parent,dict(trip,distribution=changed),on_change)
    except ValueError as error:messagebox.showerror('Kontroller stopp',str(error),parent=dialog)
   ttk.Button(dialog,text='Bruk endring',command=apply).pack(pady=10)
  ttk.Button(window,text='Endre valgt stopp / kommentar',command=edit).pack(pady=8)
  table.bind('<Double-1>',lambda event:edit())
 ttk.Button(window,text='Lukk' ,command=window.destroy).pack(pady=8)
 return window
