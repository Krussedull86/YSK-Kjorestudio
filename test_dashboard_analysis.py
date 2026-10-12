import unittest
from classroom_analysis import analyse
from core import WEIGHTS,QUAL

class SelectedTripTests(unittest.TestCase):
 def row(self,t,**kw):return dict(id=str(t),course='Synthetic Course',driver='Synthetic Student',vehicle='Test Car',trip=t,minutes=60,km=40,liters=12,stops=4,**{q:'Bra' for q in QUAL})|kw
 def test_selected_endpoints_and_real_percent(self):
  d=analyse([self.row(1),self.row(2,liters=9),self.row(3,liters=6)],WEIGHTS,selected_trips=[1,2])[0]
  self.assertEqual(d['trips'],(1,2));self.assertAlmostEqual(d['changes']['fuel'],-25);self.assertEqual(d['delta'],d['points'][2]-d['points'][1])
 def test_single_and_no_selected_do_not_imply_change(self):
  for trips in ([2],[]):
   d=analyse([self.row(1),self.row(2)],WEIGHTS,selected_trips=trips)[0];self.assertIsNone(d['delta']);self.assertIsNone(d['changes']['fuel'])
 def test_all_students_and_duplicate_records_remain(self):
  d=analyse([self.row(4)],WEIGHTS)[0];self.assertEqual(d['history'],{});self.assertIsNone(d['average'])
  d=analyse([self.row(1),self.row(1,id='duplicate'),self.row(3)],WEIGHTS)[0];self.assertEqual(len(d['records']),3);self.assertTrue(d['ambiguous']);self.assertIsNone(d['changes']['fuel'])
 def test_unselected_car_change_not_compared(self):
  d=analyse([self.row(1),self.row(2),self.row(3,vehicle='Other Car')],WEIGHTS,selected_trips=[1,2])[0];self.assertFalse(d['changed']);self.assertIsNotNone(d['delta'])
 def test_manual_fuel_and_zero_baseline(self):
  d=analyse([self.row(1,fuel_per_100=30),self.row(3,fuel_per_100=24)],WEIGHTS)[0];self.assertAlmostEqual(d['changes']['fuel'],-20)
  d=analyse([self.row(1,stops=0),self.row(3,stops=2)],WEIGHTS)[0];self.assertIsNone(d['changes']['stops'])
