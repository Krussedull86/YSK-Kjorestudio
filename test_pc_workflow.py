import unittest
from pc_workflow import ElapsedClock,matching,manual_run
from distribution import plan

class WorkflowTests(unittest.TestCase):
 def test_pause_resume_excludes_pause_and_double_start(self):
  c=ElapsedClock();c.start(10);c.start(12);c.stop(20);c.start(50)
  self.assertEqual(c.seconds(65),25);c.stop(65);self.assertEqual(c.seconds(100),25)
 def test_lookup_is_exact_activity(self):
  r=dict(driver='Anne',course='A',vehicle='Bil1',trip=2)
  self.assertEqual(matching([r],' Anne ','A','Bil1',2),[r]);self.assertEqual(matching([r],'Anne','A','Bil2',2),[])
 def test_distribution_all_times_and_statuses_retained(self):
  events=[dict(stop=1,status='ramp',elapsed_minutes=10,reason='a'),dict(stop=2,status='aborted',elapsed_minutes=20,reason='b')]
  d=manual_run(plan(2,60),1000,events,35)
  self.assertEqual(d['finished_minutes'],35);self.assertEqual(d['events'][1]['status'],'aborted')
 def test_distribution_rejects_reversed_times_and_early_return(self):
  for times,finish in [([20,10],30),([10,20],15)]:
   events=[dict(stop=i+1,status='ramp',elapsed_minutes=t,reason='') for i,t in enumerate(times)]
   with self.assertRaises(ValueError):manual_run(plan(2,60),1000,events,finish)
