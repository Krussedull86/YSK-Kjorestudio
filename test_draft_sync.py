import copy,json,tempfile,unittest,uuid,sqlite3
from pathlib import Path
from unittest.mock import Mock
from core import Store,QUAL,missing_fields
from cloud_sync import Receiver,APIError,fingerprint

class DraftSyncTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=Store(Path(self.tmp.name)/'drafts.db');self.receiver=self.receiver_for(self.store);self.remote=None;self.calls=[]
  self.d=dict(id=str(uuid.uuid4()),driver='',course='',vehicle='',trip=1,minutes='',km='',liters='',stops=0,date='',start_time='',end_time='',teacher='',**{k:'' for k in QUAL})
 def receiver_for(self,store):
  r=Receiver(store,Path(self.tmp.name)/'session');r.load=Mock(return_value={'url':'https://test.example','session':{'user':{'id':'teacher'}}});r.admin=self.server;return r
 def server(self,action,**body):
  self.calls.append(copy.deepcopy(body))
  if self.remote and body['revision']==self.remote['revision']:return {'row':copy.deepcopy(self.remote)}
  if self.remote and body['expected_revision']!=self.remote['revision']:raise APIError('Newer server version',409)
  self.remote=dict(id=body['payload']['id'],payload=copy.deepcopy(body['payload']),revision=body['revision'],deleted_at=None)
  return {'row':copy.deepcopy(self.remote)}
 def test_empty_drafts_round_trip_and_finish(self):
  self.receiver.save_trip(self.d)
  second=Store(Path(self.tmp.name)/'second.db');receiver=self.receiver_for(second)
  self.assertEqual(receiver.import_rows([self.remote]),(1,[]));self.assertTrue(missing_fields(second.all(True)[0]));self.assertEqual(second.all(),[])
  updated=second.all(True)[0]|dict(driver='Anne',course='YSK',vehicle='Bil',minutes=85,km=40,liters=12,date='2026-10-12',start_time='08:15',end_time='09:40',teacher='KK',**{k:'Bra' for k in QUAL})
  receiver.save_trip(updated,self.remote['revision']);self.receiver.import_rows([self.remote]);self.assertEqual(self.store.all()[0]['end_time'],'09:40')
 def test_two_unidentified_drafts_do_not_collide(self):
  self.store.save(self.d);self.store.save(self.d|{'id':str(uuid.uuid4())});self.assertEqual(len(self.store.all(True)),2)
 def test_lost_ack_then_newer_save_and_restart(self):
  def lose_ack(action,**body):self.server(action,**body);raise OSError('Response lost')
  self.receiver.admin=lose_ack
  with self.assertRaises(OSError):self.receiver.save_trip(self.d)
  revision=self.remote['revision'];self.receiver.queue_trip(self.d|{'notes':'newer'})
  restarted=self.receiver_for(self.store);restarted.send_queued(self.d['id'])
  self.assertEqual(self.calls[-1]['revision'],revision);self.assertTrue(restarted.pending(self.d['id']));self.assertEqual(self.store.all(True)[0]['notes'],'newer')
  restarted.send_queued(self.d['id']);self.assertEqual(self.remote['payload']['notes'],'newer');self.assertFalse(restarted.pending(self.d['id']))
 def test_save_during_upload_keeps_newest_payload(self):
  self.receiver.queue_trip(self.d)
  def concurrent(action,**body):
   self.receiver.queue_trip(self.d|{'notes':'typed while sending'});return self.server(action,**body)
  self.receiver.admin=concurrent;self.receiver.send_queued(self.d['id']);self.assertEqual(self.store.all(True)[0]['notes'],'typed while sending')
  self.receiver.admin=self.server;self.receiver.send_queued(self.d['id']);self.assertEqual(self.remote['payload']['notes'],'typed while sending')
 def test_stale_edit_conflicts_without_overwrite_and_can_resolve(self):
  self.receiver.save_trip(self.d);base=self.remote['revision'];self.remote['revision']='other-device';self.remote['payload']['notes']='phone'
  with self.assertRaises(APIError):self.receiver.save_trip(self.d|{'notes':'pc'},base)
  self.receiver.import_rows([self.remote]);self.assertEqual(self.store.all(True)[0]['notes'],'pc');self.assertEqual(self.remote['payload']['notes'],'phone')
  self.receiver.import_rows([self.remote],force=True);self.assertFalse(self.receiver.pending(self.d['id']));self.assertEqual(self.store.all(True)[0]['notes'],'phone')
 def test_cloud_deletion_does_not_remove_queued_draft(self):
  self.receiver.queue_trip(self.d);self.receiver.import_rows([dict(id=self.d['id'],payload=self.d,revision='delete',deleted_at='today')]);self.assertEqual(len(self.store.all(True)),1)
 def test_other_account_cannot_send_outbox(self):
  self.receiver.queue_trip(self.d);self.receiver.load.return_value['session']['user']['id']='other'
  with self.assertRaises(ValueError):self.receiver.send_queued(self.d['id'])
  self.assertFalse(self.calls);self.assertTrue(self.receiver.pending(self.d['id']))
 def test_old_open_form_can_follow_only_its_own_acknowledgments(self):
  self.receiver.save_trip(self.d);first=self.remote['revision'];self.receiver.save_trip(self.d|{'notes':'second'},'')
  self.assertNotEqual(first,self.remote['revision']);self.assertEqual(self.remote['payload']['notes'],'second')
  self.remote['revision']='external';self.remote['payload']['notes']='phone'
  with self.assertRaises(APIError):self.receiver.save_trip(self.d|{'notes':'stale'},'')
 def test_finished_time_change_is_detected(self):
  self.assertNotEqual(fingerprint(self.d|{'end_time':'09:40'}),fingerprint(self.d|{'end_time':'09:41'}))
 def test_distribution_draft_stays_out_of_ranking(self):
  log=dict(version=1,started_at=1791800000000,expected_minutes=60,deadlines=[30,60],events=[],finished_minutes=None)
  saved=self.store.save(self.d|{'trip':4,'distribution':log});self.assertIn('distribution',missing_fields(saved));self.assertEqual(self.store.all(),[])
