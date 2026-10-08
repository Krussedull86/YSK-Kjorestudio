import queue
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
from auth_gate import LoginGate,verify_access
from cloud_sync import Receiver,LoginRequired,APIError,DEFAULT_URL,DEFAULT_API
from core import Store

MEMBER={'active':True,'role':'teacher','organization_id':'school'}
class LoginTests(unittest.TestCase):
 def gate(self,receiver):
  receiver.load.return_value={'url':DEFAULT_URL,'session':{'user':{'id':'teacher'}}}
  gate=LoginGate.__new__(LoginGate);gate.receiver=receiver;gate.root=Mock();gate.on_success=Mock();gate.queue=queue.Queue();gate.busy=False;gate.finished=False;gate.button=Mock();gate.status=Mock();gate.frame=Mock();return gate
 def complete(self,gate):
  result=gate.queue.get(timeout=2);gate.queue.put(result);gate.drain()
 def test_fresh_start_builds_only_login_even_with_demo_flag(self):
  with tempfile.TemporaryDirectory() as tmp,patch.dict('os.environ',{'LOCALAPPDATA':tmp}),patch('sys.argv',['main.py','--demo']),patch('tkinter.Tk') as root,patch('core.Store'),patch('cloud_sync.Receiver'),patch('cloud_sync.CloudPanel') as cloud,patch('auth_gate.LoginGate') as gate,patch('design.classroom_class') as classroom,patch('http.server.ThreadingHTTPServer') as http:
   runpy.run_module('main',run_name='__main__')
   gate.assert_called_once();classroom.assert_not_called();cloud.assert_not_called();http.assert_not_called();root.return_value.mainloop.assert_called_once()
 def test_correct_login_opens_application_only_after_server_check(self):
  receiver=Mock();receiver.admin.return_value={'member':MEMBER};gate=self.gate(receiver)
  gate.start(('teacher@example.com','password'));self.complete(gate)
  receiver.connect.assert_called_once_with(DEFAULT_URL,DEFAULT_API,'teacher@example.com','password');receiver.admin.assert_called_once_with('me');gate.on_success.assert_called_once();self.assertTrue(gate.finished)
  gate.drain();gate.on_success.assert_called_once()
 def test_stored_session_is_verified_without_password(self):
  receiver=Mock();receiver.admin.return_value={'member':MEMBER};gate=self.gate(receiver);gate.start(None);self.complete(gate)
  receiver.connect.assert_not_called();receiver.admin.assert_called_once_with('me');gate.on_success.assert_called_once()
 def test_wrong_password_never_opens_data(self):
  receiver=Mock();receiver.connect.side_effect=APIError('Wrong password',400);gate=self.gate(receiver);gate.start(('user','wrong'));self.complete(gate)
  gate.on_success.assert_not_called();receiver.admin.assert_not_called();self.assertFalse(gate.finished)
 def test_inactive_missing_and_invalid_membership_never_open_data(self):
  for member in [{},MEMBER|{'active':False},MEMBER|{'role':'owner'},MEMBER|{'organization_id':''}]:
   receiver=Mock();receiver.admin.return_value={'member':member};gate=self.gate(receiver);gate.start(None);self.complete(gate);gate.on_success.assert_not_called();self.assertFalse(gate.finished)
 def test_expired_or_unreachable_session_never_opens_data(self):
  for error in [APIError('Expired',401),APIError('Disabled',403),OSError('Offline')]:
   receiver=Mock();receiver.admin.side_effect=error;gate=self.gate(receiver);gate.start(None);self.complete(gate);gate.on_success.assert_not_called();self.assertFalse(gate.finished)
 def test_school_change_never_opens_old_local_data(self):
  receiver=Mock();receiver.admin.return_value={'member':MEMBER};receiver.bind.side_effect=ValueError('Database belongs to another school');gate=self.gate(receiver);gate.start(None);self.complete(gate);gate.on_success.assert_not_called()
 def test_revoked_refresh_requires_login_in_session_and_sync(self):
  with tempfile.TemporaryDirectory() as tmp:
   receiver=Receiver(Store(Path(tmp)/'ysk.db'),Path(tmp)/'session')
   cfg={'url':DEFAULT_URL,'api':DEFAULT_API,'session':{'expires_at':0,'refresh_token':'revoked'}}
   for method in [receiver.session,receiver.sync]:
    with patch.object(receiver,'load',return_value=cfg),patch('cloud_sync.request',side_effect=APIError('Revoked refresh',400)),patch.object(receiver,'save') as save:
     with self.assertRaises(LoginRequired):method()
     save.assert_not_called()
 def test_logout_removes_session_even_offline_and_preserves_local_data(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'session';path.write_text('encrypted-session');store=Store(Path(tmp)/'ysk.db');receiver=Receiver(store,path)
   with store.conn() as c:c.execute('create table saved_draft(value text)');c.execute("insert into saved_draft values('local draft')")
   cfg={'url':'https://school.example','api':'public','session':{'access_token':'token'}}
   with patch.object(receiver,'load',return_value=cfg),patch('cloud_sync.request',side_effect=OSError('offline')) as request:
    receiver.logout();self.assertFalse(path.exists());self.assertIn('scope=local',request.call_args.args[0])
   with store.conn() as c:self.assertEqual(c.execute('select value from saved_draft').fetchone()[0],'local draft')

class ReleaseNotesTests(unittest.TestCase):
 def test_old_history_cannot_overflow_new_release(self):
  from scripts.publish_dev import release_notes
  self.assertEqual(release_notes('Current login changes\n\n'+'Old release history'*500),'Current login changes')
 def test_latest_release_limit_is_checked(self):
  from scripts.publish_dev import release_notes
  for text in ['', 'x'*5001]:
   with self.assertRaises(ValueError):release_notes(text)
