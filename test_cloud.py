import tempfile,unittest,uuid
from unittest.mock import patch
from cloud_sync import APIError,LoginRequired
from pathlib import Path
from cloud_sync import Receiver,fingerprint,endpoint
from core import Store,QUAL
class CloudTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store=Store(Path(self.tmp.name)/'ysk.db');self.receiver=Receiver(self.store,Path(self.tmp.name)/'session');self.id=str(uuid.uuid4());self.d=dict(id=self.id,driver='Anne',course='YSK',vehicle='C',trip=1,date='2026-10-08',start_time='09:00',teacher='KK',minutes=60,km=40,liters=12,stops=1,notes='',**{k:'Bra' for k in QUAL})
 def tearDown(self):self.tmp.cleanup()
 def row(self,d=None):return {'id':self.id,'payload':d or self.d}
 def test_explicit_omissions_import_retry_and_finish(self):
  from core import ranking,changes
  for key in ['minutes','km','liters','stops',*QUAL,'average_speed']:
   omitted=self.d|{key:'-'}
   self.assertEqual(self.receiver.import_rows([self.row(omitted)],force=True),(1,[]))
   self.assertEqual(self.receiver.import_rows([self.row(omitted)]),(0,[]))
   saved=self.store.all(True)[0];self.assertEqual(saved[key],'-')
   self.assertEqual(self.store.all(),[])
   self.assertEqual(ranking([saved],self.store.settings()),[])
   self.assertEqual(changes([saved]),[])
  self.assertEqual(self.receiver.import_rows([self.row(self.d)],force=True),(1,[]))
  self.assertEqual(len(self.store.all()),1)
  self.assertNotEqual(fingerprint(self.d|{'stops':'-'}),fingerprint(self.d|{'stops':0}))
 def test_invalid_values_not_treated_as_omitted(self):
  for value in ['abc', -1, float('nan')]:
   with self.assertRaises((ValueError,TypeError)):self.store.save(self.d|{'liters':value})
 def test_import_and_retry(self):
  self.assertEqual(self.receiver.import_rows([self.row()]),(1,[]));self.assertEqual(self.receiver.import_rows([self.row()]),(0,[]));self.assertEqual(len(self.store.all()),1)
 def test_changed_remote(self):
  self.receiver.import_rows([self.row()]);self.assertEqual(self.receiver.import_rows([self.row(self.d|{'liters':10})]),(1,[]));self.assertEqual(self.store.all()[0]['liters'],10)
 def test_local_conflict_and_explicit_resolution(self):
  self.receiver.import_rows([self.row()]);local=self.store.all()[0];self.store.save(local|{'liters':9});n,errors=self.receiver.import_rows([self.row(self.d|{'liters':10})]);self.assertEqual(n,0);self.assertTrue(errors);self.assertEqual(self.store.all()[0]['liters'],9)
  self.assertEqual(self.receiver.import_rows([self.row(self.d|{'liters':10})],force=True),(1,[]));self.assertEqual(self.store.all()[0]['liters'],10)
 def test_numeric_normalization(self):self.assertEqual(fingerprint(self.d),fingerprint(self.d|{'km':40.0,'trip':1.0}))
 def test_binding(self):
  self.receiver.bind('account1');self.receiver.bind('account1')
  with self.assertRaises(ValueError):self.receiver.bind('account2')
 def test_tls_url(self):
  self.assertEqual(endpoint('https://sample.supabase.co/'),'https://sample.supabase.co')
  for url in ['http://example.com','https://user:secret@example.com','https://example.com/foo','https://example.com?api=1']:
   with self.assertRaises(ValueError):endpoint(url)
 def test_membership_fallback_and_denial(self):
  cfg={'url':'https://school.example','api':'public','session':{'user':{'id':self.id},'access_token':'token'}}
  with patch('cloud_sync.request',side_effect=APIError('missing',404,'PGRST205')):self.assertIsNone(self.receiver.membership(cfg))
  with patch('cloud_sync.request',side_effect=APIError('denied',403)):
   with self.assertRaises(LoginRequired):self.receiver.membership(cfg)
  with patch('cloud_sync.request',return_value=[{'active':False}]):
   with self.assertRaises(ValueError):self.receiver.membership(cfg)
 def test_school_binding_upgrade(self):
  self.receiver.bind('url|old-user');self.receiver.bind('url|school:A','url|old-user');self.receiver.bind('url|school:A','url|new-user')
  with self.assertRaises(ValueError):self.receiver.bind('url|school:B','url|new-user')
 def test_incremental_keyset_pagination(self):
  cfg={'url':'https://school.example','api':'public','session':{'user':{'id':self.id},'access_token':'token','expires_at':9999999999},'cursor':'2026-10-07T10:00:00+00:00'}
  calls=[];saved=[]
  rows=[{'id':str(uuid.uuid4()),'payload':self.d|{'id':str(uuid.uuid4()),'driver':str(i)},'updated_at':'2026-10-07T11:00:00+00:00'} for i in range(500)]
  for r in rows:r['payload']['id']=r['id']
  def fetch(url,*args,**kwargs):
   calls.append(url);return rows if len(calls)==1 else []
  with patch.object(self.receiver,'load',return_value=cfg),patch.object(self.receiver,'save',side_effect=lambda x:saved.append(x.copy())),patch.object(self.receiver,'membership',return_value=None),patch('cloud_sync.request',side_effect=fetch):
   n,errors,connected=self.receiver.sync()
  self.assertEqual(n,500);self.assertFalse(errors);self.assertTrue(connected);self.assertIn('updated_at=gte.',calls[0]);self.assertIn('or=',calls[1]);self.assertNotIn('offset=',calls[1]);self.assertEqual(saved[-1]['cursor'],'2026-10-07T11:00:00+00:00')
 def test_duplicate_other_id(self):
  self.store.save(self.d|{'id':str(uuid.uuid4())});n,errors=self.receiver.import_rows([self.row()]);self.assertEqual(n,0);self.assertTrue(errors)
 def test_delete_retry_and_restore(self):
  self.receiver.import_rows([self.row()]);deleted=self.row()|{'deleted_at':'2026-10-07','revision':'delete-version'}
  self.assertEqual(self.receiver.import_rows([deleted]),(1,[]));self.assertEqual(self.store.all(),[])
  self.assertEqual(self.receiver.import_rows([deleted]),(0,[]));self.assertEqual(self.receiver.remote(self.id)['revision'],'delete-version')
  self.assertEqual(self.receiver.import_rows([self.row()|{'deleted_at':None,'revision':'restore-version'}]),(1,[]));self.assertEqual(len(self.store.all()),1)
 def test_delete_preserves_unsent_local_edit(self):
  self.receiver.import_rows([self.row()]);self.store.save(self.d|{'liters':7})
  self.receiver.import_rows([self.row()|{'deleted_at':'today'}]);self.assertEqual(self.store.all(),[])
  with self.store.conn() as c:
   import json
   saved=json.loads(c.execute('SELECT payload FROM cloud_deleted_local WHERE id=?',(self.id,)).fetchone()[0])
  self.assertEqual(saved['liters'],7)
 def test_save_uses_expected_version_and_imports_server_response(self):
  response={'row':self.row()|{'revision':'new','deleted_at':None},'message':'Lagret'}
  with patch.object(self.receiver,'admin',return_value=response) as call:
   self.receiver.save_trip(self.d,'old');self.assertEqual(call.call_args.kwargs['expected_revision'],'old')
  self.assertEqual(self.receiver.remote(self.id)['revision'],'new');self.assertEqual(len(self.store.all()),1)
if __name__=='__main__':unittest.main()
