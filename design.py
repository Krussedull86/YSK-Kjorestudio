"""One native comparison dashboard for the PC and classroom projector."""
import tkinter as tk
from tkinter import ttk
from core import QUAL
from live_display import LiveDisplay,BG,PANEL,TEXT,MUTED,TEAL,EDGE,GOLD

def classroom_class(Base):
 class ClassroomApp(Base):
  def __init__(self,root):
   self.ready=False;self.live_display=None;self.dashboard_display=None;self.last_cloud_update=None
   super().__init__(root)
   root.title('YSK Kjørestudio · Klasserom');root.configure(bg=BG);root.geometry('1480x950')
   style=ttk.Style();style.configure('.',background=BG,foreground=TEXT,font=('Segoe UI',10));style.configure('TFrame',background=BG);style.configure('TLabel',background=BG,foreground=TEXT);style.configure('TButton',padding=(12,8));style.configure('TEntry',fieldbackground=PANEL,foreground=TEXT,padding=7);style.configure('TCombobox',fieldbackground=PANEL,foreground=TEXT,padding=5);style.map('TCombobox',fieldbackground=[('readonly',PANEL)],foreground=[('readonly',TEXT)]);style.configure('TNotebook.Tab',padding=(16,10));style.configure('Treeview',rowheight=34)
   self.dashboard=tk.Frame(self.nb,bg=BG);self.nb.insert(0,self.dashboard,text='Klasserom');self.nb.select(self.dashboard);self.dashboard_display=LiveDisplay(self,self.dashboard,embedded=True)
   self.install_rating_buttons();self.ready=True;self.refresh()
  def install_rating_buttons(self):
   for k in QUAL:
    row,col=self.rating_positions[k]
    for widget in self.register_frame.grid_slaves(row=row,column=col):widget.destroy()
    group=tk.Frame(self.register_frame,bg=BG);group.grid(row=row,column=col,sticky='ew',padx=8,pady=8);var=self.fields[k];buttons=[]
    for value,color in [('Bra',TEAL),('Middel',GOLD),('Svak','#bb414e'),('-',MUTED),('',MUTED)]:
     b=tk.Button(group,text='Middels' if value=='Middel' else 'Tøm' if value=='' else value,relief='flat',font=('Segoe UI',10,'bold'),padx=10,pady=8,command=lambda v=var,value=value:v.set(value));b.pack(side='left',padx=(0,4));buttons.append((b,value,color))
    def update(*args,var=var,buttons=buttons):
     for b,value,color in buttons:b.configure(bg=color if var.get()==value else EDGE,fg='white' if var.get()==value else MUTED)
    var.trace_add('write',update);update()
  def refresh(self):
   super().refresh()
   if self.ready and self.dashboard_display:self.dashboard_display.paint()
  def bigscreen(self):
   if self.display and self.display.winfo_exists():self.display.destroy()
   self.live_display=None
   from main import monitors
   self.screens=monitors(self.root)
   if int(self.screen.get())>len(self.screens):self.screen.set('1')
   self.display=tk.Toplevel(self.root);self.fill_screen(self.display);self.live_display=LiveDisplay(self,self.display)
   if self.dashboard_display:
    for name in ('course','vehicle','view','metric'):getattr(self.live_display,name).set(getattr(self.dashboard_display,name).get())
    for t,var in self.dashboard_display.trip_vars.items():self.live_display.trip_vars[t].set(var.get())
    self.live_display.focus=self.dashboard_display.focus;self.live_display.paint(True)
  def paint_display(self):
   if self.live_display and self.display and self.display.winfo_exists():self.live_display.paint()
 return ClassroomApp
