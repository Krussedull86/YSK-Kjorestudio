import unittest,tempfile,copy
from pathlib import Path
from distribution import plan,validate_run,rows,summary
from course_setup import save_course,course_config,import_courses
from core import Store
import test_system
from cloud_sync import fingerprint
class DistributionTests(unittest.TestCase):
 def run_data(self):return dict(version=1,started_at=1791486000000,expected_minutes=60,deadlines=[20,40,60],events=[dict(stop=1,status='ramp',elapsed_minutes=18,reason=''),dict(stop=2,status='aborted',elapsed_minutes=43,reason='Stengt rampe'),dict(stop=3,status='ramp',elapsed_minutes=68,reason='')],finished_minutes=70)
 def test_plan_custom_and_even(self):
  self.assertEqual(plan(3,60)['deadlines'],[20,40,60]);self.assertEqual(plan(3,'60','15; 35; 60')['deadlines'],[15,35,60]);self.assertEqual(plan()['stop_count'],0)
  for args in [(31,60),(-1,60),(1.5,60),(3,0),(3,60,'15;10;60'),(3,60,'10;20'),(3,60,'10;20;61')]:
   with self.assertRaises(ValueError):plan(*args)
 def test_stop_intervals_totals_and_aborted(self):
  d=self.run_data();result=rows(d);self.assertEqual([r['segment_minutes'] for r in result],[18,25,25]);self.assertIn('2/3 til rampe',summary(d));self.assertIn('1 avbrutt',summary(d));self.assertIn('Avsluttet',summary(d))
 def test_invalid_and_incomplete(self):
  d=self.run_data();d['finished_minutes']=None;d['events']=d['events'][:1];self.assertIn('Pågår',summary(d));d['finished_minutes']=25
  with self.assertRaises(ValueError):validate_run(d)
  for mutate in [lambda d:d['events'][1].update(stop=1),lambda d:d['events'][1].update(elapsed_minutes=17),lambda d:d['events'][1].update(status='missing'),lambda d:d.update(finished_minutes=60),lambda d:d.update(started_at=1.5),lambda d:d.update(deadlines=None)]:
   d=self.run_data();mutate(d)
   with self.assertRaises(ValueError):validate_run(d)
 def test_course_sync_preserve_and_old_defaults(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp)/'db');save_course(store,'YSK',5,plan(3,60));save_course(store,'YSK',4);self.assertEqual(course_config(store,'YSK')['distribution_plan']['deadlines'],[20,40,60]);import_courses(store,[dict(name='YSK',active_trips=5,distribution_plan=plan(2,40)),dict(name='Old',active_trips=5)]);self.assertEqual(course_config(store,'YSK')['distribution_plan']['stop_count'],2);self.assertEqual(course_config(store,'Old')['distribution_plan'],plan())
 def test_payload_roundtrip_and_sync_fingerprint(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp)/'db');data=test_system.Tests.data(self,trip=4,distribution=self.run_data());saved=store.save(data);self.assertEqual(store.all()[0]['distribution'],self.run_data());changed=copy.deepcopy(saved);changed['distribution']['events'][1]['reason']='Vei stengt';self.assertNotEqual(fingerprint(saved),fingerprint(changed))
   with self.assertRaises(ValueError):store.validate(data|{'trip':1})
