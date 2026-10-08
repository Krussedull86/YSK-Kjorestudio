"""Only build the application after the server confirms an active account."""
import queue
import threading
import tkinter as tk
from tkinter import ttk
from cloud_sync import DEFAULT_URL,DEFAULT_API,LoginRequired

def verify_access(receiver):
 info=receiver.admin('me')
 member=info.get('member') or {}
 if not member.get('active') or member.get('role') not in ('admin','teacher') or not member.get('organization_id'):
  raise LoginRequired('Du har ikke aktiv tilgang. Kontakt administratoren.')
 cfg=receiver.load()
 if not cfg:raise LoginRequired('Logg inn på nytt.')
 legacy=cfg['url']+'|'+cfg['session']['user']['id']
 receiver.bind(cfg['url']+'|school:'+member['organization_id'],legacy)
 return info

class LoginGate:
 def __init__(self,root,receiver,on_success):
  self.root=root;self.receiver=receiver;self.on_success=on_success;self.queue=queue.Queue();self.busy=False;self.finished=False
  root.title('YSK Kjørestudio · Logg inn');root.geometry('560x370');root.minsize(500,330)
  self.frame=ttk.Frame(root,padding=32);self.frame.pack(fill='both',expand=True);self.frame.columnconfigure(1,weight=1)
  ttk.Label(self.frame,text='Logg inn i YSK Kjørestudio',font=('Segoe UI',20,'bold')).grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,20))
  ttk.Label(self.frame,text='Du må være innlogget for å bruke programmet.').grid(row=1,column=0,columnspan=2,sticky='w',pady=(0,12))
  self.email=tk.StringVar();self.password=tk.StringVar();self.status=tk.StringVar(value='Bruk kontoen du har fått fra administratoren.')
  for row,(label,var,masked) in enumerate([('E-post',self.email,False),('Passord',self.password,True)],2):
   ttk.Label(self.frame,text=label).grid(row=row,column=0,sticky='w',padx=(0,14),pady=8)
   entry=ttk.Entry(self.frame,textvariable=var,show='•' if masked else '');entry.grid(row=row,column=1,sticky='ew');entry.bind('<Return>',lambda e:self.login())
  self.button=ttk.Button(self.frame,text='Logg inn',command=self.login);self.button.grid(row=4,column=1,sticky='w',pady=14)
  ttk.Label(self.frame,textvariable=self.status,wraplength=470).grid(row=5,column=0,columnspan=2,sticky='w')
  root.protocol('WM_DELETE_WINDOW',root.destroy);root.after(100,self.drain)
  try:
   cfg=receiver.load()
   if cfg:self.email.set(cfg.get('email',''));self.start(None)
  except Exception:self.status.set('Logg inn på nytt for å åpne programmet.')
 def login(self):
  credentials=(self.email.get(),self.password.get());self.password.set('');self.start(credentials)
 def start(self,credentials):
  if self.busy or self.finished:return
  self.busy=True;self.button.configure(state='disabled');self.status.set('Kontrollerer innlogging …')
  def work():
   try:
    if credentials:self.receiver.connect(DEFAULT_URL,DEFAULT_API,*credentials)
    self.queue.put((True,verify_access(self.receiver)))
   except Exception as e:self.queue.put((False,str(e)))
  threading.Thread(target=work,daemon=True).start()
 def drain(self):
  if self.finished:return
  try:
   ok,result=self.queue.get_nowait();self.busy=False
   if ok:
    self.finished=True;self.frame.destroy();self.on_success();return
   self.button.configure(state='normal');self.status.set('Innlogging kreves: '+result)
  except queue.Empty:pass
  self.root.after(100,self.drain)
