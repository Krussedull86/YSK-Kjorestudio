"""Exercise native Tk layout with synthetic data; run on the Windows build runner."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace
from core import QUAL,WEIGHTS
from live_display import LiveDisplay,METRICS
from design import classroom_class
from course_setup import trip_name
rows=[]
for i in range(120):
 for t in (1,2,3):
  if i%7==0 and t==3:continue
  r=dict(id=f'{i}-{t}',driver=f'Synthetic Student {i:03}',course='Synthetic Course',vehicle='Test Vehicle',trip=t,minutes=60-t*2,km=40,liters=12-t,stops=4-t,date='2026-10-12',start_time='10:00',teacher='Synthetic Teacher',notes='',**{q:'Bra' for q in QUAL})
  if i%11==0 and t==2:r.update(minutes='',completion='incomplete')
  rows.append(r)
rows.append(dict(rows[1],id='delivery',driver='Delivery Student',trip=4))
class Base:
 def __init__(self,root):
  self.root=root;self.nb=ttk.Notebook(root);self.nb.pack(fill='both',expand=True);self.register_frame=ttk.Frame(self.nb);self.nb.add(self.register_frame,text='Register');self.fields={};self.rating_positions={};self.display=None;self.screen=tk.StringVar(value='1');self.compare_trips=None
  for i,q in enumerate(QUAL):self.fields[q]=tk.StringVar();self.rating_positions[q]=(i,0)
  self.filters={k:(tk.StringVar(value='Alle'),None) for k in ('course','vehicle','trip')};self.store=SimpleNamespace(all=lambda **kwargs:rows,settings=lambda:WEIGHTS)
 def refresh(self):pass
 def fill_screen(self,window):window.geometry('1480x950')
 def show_distribution(self,*args):pass
root=tk.Tk();errors=[];root.report_callback_exception=lambda cls,error,tb:errors.append(str(error));app=classroom_class(Base)(root);root.update();root.update_idletasks();view=app.dashboard_display
assert len(view.tree.get_children())==121
assert len(view.split.panes())==1
view.open_analysis();root.update();assert len(view.split.panes())==2
view.overview();root.update();assert len(view.split.panes())==1
view.table_mode.set('Alle data');view.paint(True);root.update();assert 'Km/t T1' in view.tree['columns']
view.table_mode.set('Poeng og målinger');view.paint(True)
for metric in METRICS:view.metric.set(metric);view.draw();root.update()
for column in view.tree['columns']:view.sort_by(column);root.update()
view.trip_vars[3].set(False);view.paint(True);root.update();assert 'T3' not in view.tree['columns']
view.search.set('does-not-exist');root.update();assert not view.tree.get_children()
view.search.set('');view.trip_vars[3].set(True);view.paint(True);root.update()
view.view.set(trip_name(4));view.paint(True);root.update();view.sort_by('Tid');view.details();root.update()
for w in root.winfo_children():
 if isinstance(w,tk.Toplevel):w.destroy()
view.view.set('Optimaltur 1–2–3');view.paint(True);root.update();view.metric.set('Forbruk');view.draw();root.update();app.bigscreen();root.update();app.live_display.move(1);app.live_display.draw();root.update();app.display.destroy();root.update()
if errors:raise AssertionError(errors)
try:
 from PIL import ImageGrab
 root.lift();root.update();ImageGrab.grab(bbox=(root.winfo_rootx(),root.winfo_rooty(),root.winfo_rootx()+root.winfo_width(),root.winfo_rooty()+root.winfo_height())).save('classroom_ui.png')
except Exception as error:print('Screenshot unavailable:',error)
root.destroy();print('Native UI passed: 121 students, all metrics, sorting, selected trips, search, delivery view, details and full-screen lifecycle.')
