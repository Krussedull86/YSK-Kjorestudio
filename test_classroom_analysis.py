import unittest
from classroom_analysis import analyse,value,percent
from core import WEIGHTS,QUAL
class AnalysisTests(unittest.TestCase):
 def row(self,t=1,**kw):return dict(id=str(t),course='A',driver='Anne',vehicle='41',trip=t,minutes=60,km=40,liters=12,stops=4,**{q:'Bra' for q in QUAL})|kw
 def test_common_scale_and_progress(self):
  d=analyse([self.row(),self.row(2,liters=10),self.row(3,liters=8)],WEIGHTS)[0]
  self.assertLess(d['points'][1],d['points'][3]);self.assertGreater(d['delta'],0)
 def test_incomplete_is_visible(self):
  d=analyse([self.row(),self.row(3,minutes='',completion='incomplete')],WEIGHTS)[0]
  self.assertIsNone(d['points'][3]);self.assertIsNone(d['delta']);self.assertIsNone(value(d['history'][3],'time'))
 def test_car_change_and_duplicate(self):
  d=analyse([self.row(),self.row(3,vehicle='42')],WEIGHTS)[0];self.assertTrue(d['changed']);self.assertIsNone(d['delta'])
  d=analyse([self.row(),self.row(id='other',vehicle='42')],WEIGHTS)[0];self.assertTrue(d['ambiguous'])
 def test_class_size_filter_and_courses(self):
  rows=[self.row(driver=f'Elev {n}',id=str(n)) for n in range(100)]
  self.assertEqual(len(analyse(rows,WEIGHTS)),100);self.assertEqual(analyse(rows,WEIGHTS,course='B'),[])
 def test_normalisation_and_zero(self):
  self.assertEqual(value(self.row(),'fuel'),3);self.assertEqual(value(self.row(),'stops'),1);self.assertEqual(percent(3,2.4),-20.000000000000004);self.assertIsNone(percent(0,2))
