import tempfile,unittest,urllib.request,urllib.error,json
from pathlib import Path
from core import *
from main import server
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store=Store(Path(self.tmp.name)/'test.db')
 def tearDown(self):self.tmp.cleanup()
 def data(self,**kwargs):
  return dict(driver='Kjell',course='YSK',vehicle='C',trip=1,minutes=60,km=40,liters=12,stops=2,**{k:'Bra' for k in QUAL})|kwargs
 def test_metrics(self):
  m=metrics(self.store.save(self.data()));self.assertEqual(m['fart'],40);self.assertAlmostEqual(m['forbruk'],.3)
 def test_duplicate_and_edit(self):
  d=self.store.save(self.data())
  with self.assertRaises(ValueError):self.store.save(self.data())
  self.store.save(d|{'liters':10});self.assertEqual(len(self.store.all()),1)
 def test_ranking_and_groups(self):
  self.store.save(self.data());self.store.save(self.data(driver='B',liters=20));self.store.save(self.data(driver='C',vehicle='CE',liters=90))
  r=ranking(self.store.all(),self.store.settings());a=next(x for x in r if x['driver']=='Kjell');b=next(x for x in r if x['driver']=='B');self.assertGreater(a['score'],b['score'])
  self.assertEqual(next(x for x in r if x['driver']=='C')['score'],100)
 def test_changes_zero(self):
  a=self.store.save(self.data(liters=0));b=self.store.save(self.data(trip=5,liters=10));d=changes([a,b])[0];self.assertIsNone(d['percent']['forbruk']);self.assertEqual(d['first']['trip'],1);self.assertEqual(d['last']['trip'],5)
 def test_invalid(self):
  for change in [{'km':0},{'liters':'nan'},{'trip':6},{'stops':1.5},{'komfort':'God'}]:
   with self.assertRaises((ValueError,TypeError)):self.store.save(self.data(**change))
 def test_paper_form(self):
  d=self.store.save(self.data(minutes='12:30',date='2026-10-07',start_time='09:15',teacher='Lærer',average_speed='42,5',komfort='Middels'))
  self.assertEqual(d['minutes'],12.5);self.assertEqual(metrics(d)['fart'],42.5);self.assertEqual(metrics(d)['forbruk10'],3);self.assertEqual(d['komfort'],'Middel')
  self.assertEqual(self.store.all()[0]['teacher'],'Lærer')
  for extra in [{'start_time':'25:30'},{'date':'2026-02-30'},{'average_speed':'nan'},{'minutes':'12:99'}]:
   with self.assertRaises(ValueError):self.store.save(self.data(**extra))
 def test_backup(self):
  self.store.save(self.data());p=Path(self.tmp.name)/'backup.db';self.store.backup(p);self.assertEqual(len(Store(p).all()),1)
 def test_mobile(self):
  http,token=server(self.store)
  try:
   data=json.dumps(self.data(id='retry-safe-id')).encode()
   def post(code):return urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8765/api/trips',data=data,headers={'X-Token':code,'Content-Type':'application/json'}))
   with self.assertRaises(urllib.error.HTTPError) as e:post('wrong')
   self.assertEqual(e.exception.code,403)
   with post(token) as r:self.assertEqual(r.status,200)
   with post(token) as r:self.assertEqual(r.status,200)
   self.assertEqual(len(self.store.all()),1)
  finally:http.shutdown();http.server_close()
if __name__=='__main__':unittest.main()
