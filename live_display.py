import tkinter as tk
import time,math,datetime
from classroom_views import MODES,projection,value_text,statistics,LABELS,RATING
from core import metrics,QUAL
BG='#f3f6fa';PANEL='#ffffff';EDGE='#dfe7ef';TEAL='#087f72';TEXT='#183047';MUTED='#61778c';GOLD='#9d6717';RED='#bb414e';BLUE='#346fd2'
class LiveDisplay:
 def __init__(self,app,window):
  self.app=app;self.window=window;self.mode='Samlet poeng';self.baseline='Første tur';self.page=0;self.auto=False;self.last_flip=time.monotonic();self.dwell=18;self.focus=None;self.focus_trip=None
  self.canvas=tk.Canvas(window,bg=BG,highlightthickness=0);self.canvas.pack(fill='both',expand=True)
  self.canvas.bind('<Configure>',lambda e:self.paint());window.bind('<Escape>',lambda e:window.destroy());window.bind('<Right>',lambda e:self.move(1));window.bind('<Left>',lambda e:self.move(-1));window.bind('<space>',lambda e:self.toggle());window.bind('<F11>',lambda e:app.fill_screen(window))
  self.timer=window.after(100,self.tick);window.bind('<Destroy>',self.destroyed,add='+')
 def destroyed(self,event):
  if event.widget==self.window:
   try:self.window.after_cancel(self.timer)
   except tk.TclError:pass
 def set_mode(self,mode):
  if mode not in MODES:mode='Samlet poeng'
  self.mode=mode;self.page=0;self.last_flip=time.monotonic();self.paint()
 def toggle(self):self.auto=not self.auto;self.last_flip=time.monotonic();self.paint()
 def rows(self):return projection(self.app.rows,self.app.store.settings(),self.mode,self.baseline,**{k:v.get() for k,(v,box) in self.app.filters.items()})
 def move(self,step):self.page=(self.page+step)%max(1,math.ceil(len(self.rows())/8));self.last_flip=time.monotonic();self.paint()
 def tick(self):
  if not self.window.winfo_exists():return
  if self.auto and time.monotonic()-self.last_flip>=self.dwell:
   pages=max(1,math.ceil(len(self.rows())/8))
   if self.page+1>=pages:self.page=0;self.mode=MODES[(MODES.index(self.mode)+1)%len(MODES)]
   else:self.page+=1
   self.last_flip=time.monotonic()
  self.paint();self.timer=self.window.after(1000,self.tick)
 def menu(self,event,key):
  menu=tk.Menu(self.window,tearoff=False,bg='white',fg=TEXT,font=('Segoe UI',12))
  choices=['Første tur','1','2','3','4','5'] if key=='baseline' else list(self.app.filters[key][1]['values'])
  for value in choices:
   def choose(value=value):
    if key=='baseline':self.baseline=value
    else:self.app.filters[key][0].set(value);self.app.refresh()
    self.page=0;self.paint()
   menu.add_command(label=('Tur '+value if key=='baseline' and value!='Første tur' else value),command=choose)
  try:menu.tk_popup(event.x_root,event.y_root)
  finally:menu.grab_release()
 def paint(self):
  if not self.window.winfo_exists():return
  c=self.canvas;c.delete('all');w=max(c.winfo_width(),800);h=max(c.winfo_height(),500);s=min(w/1600,h/900);font=lambda n:('Segoe UI',max(9,int(n*s)),'bold')
  def txt(x,y,text,size=18,color=TEXT,anchor='nw',width=None):return c.create_text(x,y,text=text,fill=color,font=font(size),anchor=anchor,width=width)
  def rect(x,y,x2,y2,color=PANEL):return c.create_rectangle(x,y,x2,y2,fill=color,outline='')
  def button(x,y,width,label,fn,selected=False,color=None):
   tag='b'+str(x)+str(y);r=rect(x,y,x+width,y+34*s,color or (TEAL if selected else PANEL));t=txt(x+10*s,y+8*s,label,13,'white' if selected else TEXT);c.addtag_withtag(tag,r);c.addtag_withtag(tag,t);c.tag_bind(tag,'<Button-1>',fn)
  margin=26*s;rows=self.rows();pages=max(1,math.ceil(len(rows)/8));self.page%=pages;visible=rows[self.page*8:(self.page+1)*8]
  txt(margin,18*s,'YSK / FELLES GJENNOMGANG',14,TEAL);txt(margin,44*s,self.mode,32);txt(w-margin,21*s,datetime.datetime.now().strftime('%H:%M'),24,MUTED,'ne')
  for i,mode in enumerate(MODES):button(w*.43+(i%4)*(w*.14),43*s+(i//4)*40*s,w*.135,mode,lambda e,mode=mode:self.set_mode(mode),mode==self.mode)
  for i,(key,label) in enumerate([('course','Kurs'),('vehicle','Bil'),('trip','Tur'),('baseline','Sammenlign fra')]):
   value=self.baseline if key=='baseline' else self.app.filters[key][0].get();button(margin+i*(w-2*margin)/4,160*s,(w-2*margin)/4-10*s,label+': '+value+' ▾',lambda e,key=key:self.menu(e,key))
  stats=statistics(rows);cards=[('ELEVER / TURER',f"{stats['students']} / {stats['trips']}"),('SNITT FORBRUK','—' if stats['fuel'] is None else f"{stats['fuel']:.2f} L/10 km"),('SNITT FORBEDRING','—' if stats['improvement'] is None else f"{stats['improvement']:+.1f}%"),('FULLFØRT TUR 5',str(stats['complete']))]
  for i,(label,value) in enumerate(cards):
   x=margin+i*(w-2*margin)/4;rect(x,207*s,x+(w-2*margin)/4-10*s,271*s);txt(x+14*s,218*s,label,12,MUTED);txt(x+14*s,239*s,value,22,TEAL)
  top=297*s;bottom=h-96*s;left=w*.64;side=left+19*s;row_h=(bottom-top)/8
  txt(margin,top-12*s,'PLASS / ELEV',12,MUTED);txt(left*.62,top-12*s,self.mode.upper(),12,MUTED)
  for i,d in enumerate(visible):
   y=top+15*s+i*row_h;tag='student'+str(i);active=(d['course'],d['vehicle'],d['driver'])==self.focus;new=time.monotonic()-self.app.live_changes.get(d['id'],0)<25
   r=rect(margin,y,left,y+row_h-5*s,'#e7f4f0' if active or new else PANEL);c.addtag_withtag(tag,r)
   place=d['view_place'];txt(margin+12*s,y+7*s,'—' if place is None or self.mode=='Siste turer' else '#'+str(place),22,TEAL)
   txt(margin+78*s,y+5*s,d['driver'][:28],19,width=left*.43);txt(margin+78*s,y+30*s,f"{d['course']} · {d['vehicle']} · Tur {d['trip']}"+(' · NY' if new else ''),11,MUTED,width=left*.48)
   txt(left*.62,y+6*s,value_text(d,self.mode),21,TEAL if self.mode!='Forbedring' or (d['improvement'] or 0)>=0 else RED,width=left*.36)
   secondary=f"{d['score']:.1f} samlet poeng" if self.mode!='Samlet poeng' else ('Første tur' if d['improvement'] is None else f"{d['improvement']:+.1f}% forbedring")
   txt(left*.62,y+32*s,secondary,11,MUTED)
   for item in c.find_enclosed(margin,y,left,y+row_h-5*s):c.addtag_withtag(tag,item)
   c.tag_bind(tag,'<Button-1>',lambda e,d=d:self.select(d))
  if not rows:txt(margin,top+80*s,'Venter på første registrering …\nVelg kurs eller registrer en tur.',26,width=left-margin)
  focus=next((d for d in rows if (d['course'],d['vehicle'],d['driver'])==self.focus),None) or (visible[0] if visible else None);rect(side,top,w-margin,bottom+10*s)
  if focus:
   x=side+18*s;sw=w-margin-x-14*s;history=sorted([r for r in self.app.rows if (r['course'],r['vehicle'],r['driver'])==(focus['course'],focus['vehicle'],focus['driver'])],key=lambda r:r['trip']);chosen=next((d for d in history if d['trip']==self.focus_trip),None) or focus
   txt(x,top+14*s,'ELEVENS TURER · KLIKK FOR DETALJER',11,TEAL);txt(x,top+40*s,focus['driver'],26,width=sw)
   for n in range(1,6):
    cx=x+(n-1)*sw/5;exists=n in focus['completed'];button(cx,top+79*s,sw/5-5*s,str(n)+(' ✓' if exists else ''),lambda e,n=n,exists=exists:self.choose_trip(n) if exists else None,n==chosen['trip'])
   chartkey='tid' if self.mode=='Tid per km' else 'stopp' if self.mode=='Stopp per km' else 'forbruk10';title={'tid':'MINUTTER PER KM','stopp':'STOPP PER KM','forbruk10':'LITER PER 10 KM'}[chartkey]
   vals=[metrics(d)[chartkey] for d in history];hi=max(vals+[.01]);chart_top=top+143*s;chart_bottom=top+241*s;pts=[]
   txt(x,top+123*s,title,11,MUTED)
   for j in range(4):c.create_line(x,chart_top+j*(chart_bottom-chart_top)/3,x+sw,chart_top+j*(chart_bottom-chart_top)/3,fill=EDGE)
   for d,value in zip(history,vals):
    px=x+14*s+(d['trip']-1)*(sw-28*s)/4;py=chart_bottom-value/hi*(chart_bottom-chart_top-12*s);pts.extend([px,py]);c.create_oval(px-4*s,py-4*s,px+4*s,py+4*s,fill=TEAL,outline='');txt(px,py-7*s,f'{value:.2f}',10,TEAL,'s')
   if len(pts)>2:c.create_line(*pts,fill=TEAL,width=max(2,2*s))
   m=metrics(chosen);y=chart_bottom+20*s;txt(x,y,f"TUR {chosen['trip']} · {chosen.get('date','')}",12,TEAL)
   txt(x,y+24*s,f"{chosen['minutes']:.2f} min  ·  {chosen['km']:.1f} km  ·  {m['fart']:.1f} km/t",13,width=sw)
   txt(x,y+46*s,f"{chosen['liters']:.2f} liter totalt  ·  {int(chosen['stops'])} stopp",13,width=sw)
   for j,q in enumerate(QUAL):
    color=TEAL if chosen[q]=='Bra' else GOLD if chosen[q]=='Middel' else RED;txt(x,y+(74+j*23)*s,LABELS[q],12,MUTED);txt(x+sw,y+(74+j*23)*s,'Middels' if chosen[q]=='Middel' else chosen[q],12,color,'ne')
   txt(x,bottom-24*s,'Lærer: '+(chosen.get('teacher') or '—'),11,MUTED,width=sw)
  sync=getattr(self.app,'last_cloud_update',None);state='Sky hentet '+sync if sync else 'Lokale data';state='Venter på sky · viser lagrede data' if getattr(self.app,'cloud_waiting',False) else state
  txt(margin,h-60*s,f"{state} · Side {self.page+1}/{pages} · "+('Automatisk gjennomgang' if self.auto else 'Gjennomgang på dine premisser'),12,MUTED)
  txt(margin,h-34*s,'Plass gjelder samme kurs, bil og tur. Fart gir ingen poeng. Positiv forbedring = redusert forbruk.',11,MUTED)
  button(w-390*s,h-66*s,62*s,'←',lambda e:self.move(-1));button(w-319*s,h-66*s,62*s,'→',lambda e:self.move(1));button(w-244*s,h-66*s,215*s,'Pause' if self.auto else 'Start automatikk',lambda e:self.toggle(),self.auto)
 def choose_trip(self,n):self.focus_trip=n;self.auto=False;self.paint()
 def select(self,d):self.focus=(d['course'],d['vehicle'],d['driver']);self.focus_trip=d['trip'];self.auto=False;self.paint()
