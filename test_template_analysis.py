import unittest
from template_analysis import comparable,percent
class TemplateAnalysisTests(unittest.TestCase):
 def run_(self,id='1',**kw):
  r=dict(id=id,organization_id='school',template_id='template',template_revision=1,created_at=id,snapshot=dict(base_trip=1,parameters=[dict(id='fuel',weight=30)]),payload=dict(driver='A',course='Course',vehicle='41',date='2026-10-10'))
  r.update(kw);return r
 def test_version_school_vehicle_scoring_separation(self):
  a=self.run_();rows=[a,self.run_('2',template_revision=2),self.run_('3',organization_id='other'),self.run_('4',payload=dict(driver='A',course='Course',vehicle='42',date='2026-10-10')),self.run_('5',snapshot=dict(base_trip=2,parameters=[dict(id='fuel',weight=50)]))]
  self.assertEqual(comparable(rows,a),[a])
 def test_optimal_three_templates_can_compare_same_schema(self):
  a=self.run_();b=self.run_('2',template_id='second',snapshot=dict(base_trip=2,parameters=a['snapshot']['parameters']))
  self.assertEqual(comparable([b,a],a),[a,b])
 def test_missing_and_zero_do_not_fake_percent(self):
  self.assertIsNone(percent(0,1));self.assertIsNone(percent('-',1));self.assertAlmostEqual(percent(3,2.4),-20)
