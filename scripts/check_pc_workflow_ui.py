"""Real PC form integration on Windows, without a cloud account or real data."""
import sys,tempfile,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
import tkinter as tk
import main
from design import classroom_class
from core import QUAL
with tempfile.TemporaryDirectory() as tmp,patch.object(main,'DATA',Path(tmp)),patch.object(main,'server',return_value=(None,'test')):
 root=tk.Tk();errors=[];root.report_callback_exception=lambda cls,e,tb:errors.append(str(e))
 app=classroom_class(main.App)(root);root.update()
 assert app.nb.tab(app.nb.select(),'text')=='Sentral'
 d=dict(driver='Synthetic Student',course='Test Course',vehicle='Test Vehicle',trip=1,minutes='60',km='40',liters='12',stops='1',date=datetime.date.today().isoformat(),start_time='10:00',teacher='Test',notes='',**{k:'Bra' for k in QUAL})
 for key,val in d.items():app.fields[key].set(main.trip_name(val) if key=='trip' else val)
 with patch('tkinter.messagebox.showerror') as error:
  app.save();first=app.edit_id;assert first;assert app.fields['driver'].get()=='Synthetic Student'
  app.fields['liters'].set('10');app.save();assert app.edit_id==first;assert len(app.store.all(True))==1;error.assert_not_called()
 app.reset()
 for key in ('driver','course','vehicle'):app.fields[key].set(d[key])
 app.workflow.lookup();root.update();assert app.edit_id==first;assert float(app.fields['liters'].get())==10
 app.workflow.start();assert app.workflow.clock.started is not None
 app.workflow.pause();assert app.workflow.clock.started is None
 app.workflow.stop();root.update()
 assert not errors,errors
 app.close()
 print('PC central UI passed: home, save stays in form, repeated save retains ID, existing activity lookup, timer controls.')
