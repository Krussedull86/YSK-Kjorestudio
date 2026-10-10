"""Private, per-user releases. Files are verified before installation."""
import hashlib,os,queue,sys,threading,time,urllib.request,urllib.parse,subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk,messagebox
from version import VERSION,BUILD
MAX_SIZE=100*1024*1024

def download(asset,project,target):
 url=urllib.parse.urlsplit(asset['url']);origin=urllib.parse.urlsplit(project)
 if url.scheme!='https' or url.hostname!=origin.hostname or url.username or not url.path.startswith('/storage/v1/object/sign/'):raise ValueError('Ugyldig nedlastingsadresse.')
 size=int(asset['size'])
 if not 0<size<=MAX_SIZE:raise ValueError('Ugyldig filstørrelse.')
 target=Path(target);partial=target.with_suffix('.part');target.parent.mkdir(parents=True,exist_ok=True);digest=hashlib.sha256();total=0
 try:
  opener=urllib.request.build_opener(NoRedirect)
  with opener.open(url.geturl(),timeout=45) as response,partial.open('wb') as out:
   while True:
    block=response.read(65536)
    if not block:break
    total+=len(block)
    if total>size:raise ValueError('Filen er større enn oppgitt.')
    digest.update(block);out.write(block)
  if total!=size or digest.hexdigest()!=asset['sha256']:raise ValueError('Kontrollsummen eller filstørrelsen stemmer ikke.')
  os.replace(partial,target);return target
 finally:
  partial.unlink(missing_ok=True)
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise ValueError('Nedlastingen forsøkte å bytte adresse.')
def install_script(pid,source,target):
 quote=lambda p:"'"+str(p).replace("'","''")+"'"
 return f"""$ErrorActionPreference = 'Stop'
while (Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue) {{ Start-Sleep -Milliseconds 400 }}
$source = {quote(source)}
$target = {quote(target)}
$backup = $target + '.previous'
try {{
 Copy-Item -LiteralPath $target -Destination $backup -Force
 Copy-Item -LiteralPath $source -Destination $target -Force
 Start-Process -FilePath $target
}} catch {{
 if (Test-Path -LiteralPath $backup) {{ Copy-Item -LiteralPath $backup -Destination $target -Force }}
 Add-Type -AssemblyName System.Windows.Forms
 [System.Windows.Forms.MessageBox]::Show('Oppdateringen kunne ikke installeres. Forrige program er beholdt. ' + $_.Exception.Message, 'YSK')
}}
"""
class UpdatesPanel:
 def __init__(self,app,receiver,data):
  self.app=app;self.receiver=receiver;self.data=Path(data);self.queue=queue.Queue();self.busy=False;self.release=None;self.file=None;self.last=0;self.startup_checked=False
  frame=ttk.Frame(app.nb,padding=24);app.nb.add(frame,text='Oppdateringer')
  ttk.Label(frame,text='Oppdateringer',font=('Segoe UI',25,'bold')).pack(anchor='w')
  ttk.Label(frame,text=f'Installert: {VERSION} · bygg {BUILD}\nAdmin velger dev eller stable for hver bruker. Oppdateringer installeres når du velger det.').pack(anchor='w',pady=12)
  self.status=tk.StringVar(value='Logg inn under Telefon / sky.');ttk.Label(frame,textvariable=self.status,wraplength=850).pack(anchor='w',pady=8)
  self.notes=tk.Text(frame,height=12,wrap='word',bg='white',fg='#183047',relief='flat');self.notes.pack(fill='both',expand=True,pady=12);self.notes.configure(state='disabled')
  ttk.Button(frame,text='Sjekk oppdateringer',command=self.check).pack(anchor='w',pady=6)
  self.get_button=ttk.Button(frame,text='Last ned og installer',command=self.get,state='disabled');self.get_button.pack(anchor='w',pady=6)
  app.root.after(1000,self.poll)
 def task(self,fn):
  if self.busy:return
  self.busy=True
  def work():
   try:self.queue.put((True,fn()))
   except Exception as e:self.queue.put((False,str(e)))
  threading.Thread(target=work,daemon=True).start()
 def check(self):
  if self.busy:return
  self.last=time.time();self.status.set('Sjekker din oppdateringskanal …');self.task(lambda:('check',self.receiver.admin('update_check',platform='windows')))
 def get(self):
  if not self.release or self.busy:return
  if self.file:return self.install()
  release_id=self.release['id'];self.status.set('Laster ned og kontrollerer filen …')
  def work():
   result=self.receiver.admin('download_update',platform='windows',release_id=release_id);release=result['release']
   if release['build']<=BUILD:raise ValueError('Denne utgaven er allerede installert.')
   project=self.receiver.load()['url'];path=download(release['asset'],project,self.data/'updates'/('YSK_B'+str(release['build'])+'.exe'));return ('download',path)
  self.task(work)
 def install(self):
  if sys.platform!='win32' or not getattr(sys,'frozen',False):
   messagebox.showinfo('Lastet ned','EXE-filen er kontrollert og lagret her:\n'+str(self.file)+'\nStart den nye EXE-filen på Windows.');return
  if not messagebox.askyesno('Installer oppdatering','Programmet lukkes og starter igjen etter oppdateringen. Installere nå?'):return
  script=self.data/'updates'/'installer.ps1';script.write_text(install_script(os.getpid(),self.file,sys.executable),encoding='utf-8-sig')
  subprocess.Popen(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script)],creationflags=0x08000000);self.app.close()
 def poll(self):
  if not self.app.root.winfo_exists():return
  try:
   while True:
    ok,result=self.queue.get_nowait();self.busy=False
    if not ok:self.status.set(str(result));continue
    kind,value=result
    if kind=='download':self.file=value;self.status.set('Kontrollert og klar til installasjon.');self.get_button.configure(text='Installer nå');self.install()
    else:
     self.release=value.get('release');self.file=None;channel=value['channel'];r=self.release;new=r and r['build']>BUILD
     self.status.set(f'Kanal: {channel} · '+(f"Ny versjon {r['version']} · bygg {r['build']} · {r['published_at'][:10]}" if new else 'Du har siste tilgjengelige utgave.' if r else 'Ingen PC-utgave er publisert i denne kanalen ennå.'))
     self.notes.configure(state='normal');self.notes.delete('1.0','end');self.notes.insert('1.0',r['notes'] if r else '');self.notes.configure(state='disabled');self.get_button.configure(state='normal' if new else 'disabled',text='Last ned og installer')
     if new and not self.startup_checked:
      self.startup_checked=True
      if messagebox.askyesno('Ny YSK-utgave',f"Versjon {r['version']} er tilgjengelig på {channel}. Åpne Oppdateringer?"):
       self.app.nb.select(self.get_button.master)
     else:self.startup_checked=True
  except queue.Empty:pass
  if not self.busy and time.time()-self.last>3600:
   try:
    if self.receiver.load():self.check()
   except Exception as e:self.last=time.time();self.status.set(str(e))
  self.app.root.after(1000,self.poll)
