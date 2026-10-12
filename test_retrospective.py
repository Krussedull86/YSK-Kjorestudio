import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from trip_times import clock_text,clock_minutes
from core import Store,QUAL
from management import ManagementPanel

class RetrospectiveTests(unittest.TestCase):
 def test_minutes_and_clock_formats(self):
  self.assertEqual(clock_text('815'),'08:15');self.assertEqual(clock_text('8.15'),'08:15')
  self.assertEqual(clock_minutes('08:15','09:40'),85)
  self.assertEqual(clock_minutes('23:45','00:15'),30)
  self.assertIsNone(clock_minutes('08:15',''))
 def test_invalid_times_not_silently_saved(self):
  for t in ['25:00','12:60','xx','1:2']:
   with self.assertRaises(ValueError):clock_text(t)
  with self.assertRaises(ValueError):clock_minutes('08:15','08:15')
 def test_network_failure_keeps_local_payload_and_revision(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp)/'test.db');app=SimpleNamespace(store=store,edit_id=None,form_generation=0,refresh=Mock(),editlabel=Mock())
   panel=ManagementPanel.__new__(ManagementPanel);panel.app=app;panel.busy=False;from cloud_sync import Receiver
   panel.receiver=Receiver(store,Path(tmp)/'session');panel.receiver.load=Mock(return_value={'url':'https://school.example','session':{'user':{'id':'teacher'}}});panel.receiver.admin=Mock(side_effect=OSError('No network'));panel.run=lambda fn,done:done(fn())
   row=dict(driver='Test',course='Test',vehicle='Test',trip=1,minutes=85,km=40,liters=12,stops=0,date='2026-10-12',start_time='08:15',end_time='09:40',teacher='Test',**{q:'Bra' for q in QUAL})
   with patch('tkinter.messagebox.showwarning'):panel.save(row,'original-revision')
   saved=store.all(True)[0];self.assertEqual(saved['end_time'],'09:40');self.assertEqual(saved['pc_draft_revision'],'original-revision');self.assertEqual(saved['id'],app.edit_id)
 def test_incomplete_cloud_edit_persists(self):
  with tempfile.TemporaryDirectory() as tmp:
   from main import App
   app=App.__new__(App);app.store=Store(Path(tmp)/'test.db');app.edit_id='existing';app.edit_revision='old';app.edit_distribution=None;app.refresh=Mock();app.editlabel=Mock()
   data=dict(driver='Test',course='Test',vehicle='Test',trip='1',minutes=85,km=40,liters='',stops=0,date='2026-10-12',start_time='08:15',end_time='09:40',teacher='Test',**{q:'' for q in QUAL})
   app.fields={k:Mock(get=Mock(return_value=str(v))) for k,v in data.items()}
   with patch('tkinter.messagebox.showerror') as error:app.save();error.assert_not_called()
   saved=app.store.all(True)[0];self.assertEqual(saved['completion'],'incomplete');self.assertEqual(saved['pc_draft_revision'],'old')
