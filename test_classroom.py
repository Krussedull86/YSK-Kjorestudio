import unittest
from classroom import board,improvement_rows
from core import QUAL,WEIGHTS
class ClassroomTests(unittest.TestCase):
 def row(self,**extra):return dict(id='a',driver='Anne',course='Kurs A',vehicle='Bil A',trip=1,minutes=30,km=30,liters=9,stops=2,**{k:'Bra' for k in QUAL})|extra
 def test_latest_one_student_and_all_students(self):
  rows=[self.row(id=f'{n}-{t}',driver=f'Elev {n}',trip=t,liters=10-t) for n in range(100) for t in range(1,6)]
  result=board(rows,WEIGHTS);self.assertEqual(len(result),100);self.assertTrue(all(d['trip']==5 and d['completed']=={1,2,3,4,5} for d in result))
 def test_improvement_and_filtered_trip(self):
  rows=[self.row(),self.row(id='b',trip=2,liters=6),self.row(id='c',trip=5,liters=3)]
  self.assertAlmostEqual(board(rows,WEIGHTS)[0]['fuel_improvement'],100*2/3)
  d=board(rows,WEIGHTS,trip='2')[0];self.assertAlmostEqual(d['fuel_improvement'],100/3);self.assertEqual(len(d['history']),2)
 def test_no_zero_baseline_division(self):
  result=board([self.row(liters=0),self.row(id='b',trip=2)],WEIGHTS);self.assertIsNone(result[0]['fuel_improvement'])
 def test_comparable_places_and_ties(self):
  rows=[self.row(),self.row(id='b',driver='B'),self.row(id='c',driver='C',liters=12),self.row(id='d',driver='D',vehicle='Bil B',liters=99)]
  result={d['driver']:d for d in board(rows,WEIGHTS)};self.assertEqual(result['Anne']['place'],1);self.assertEqual(result['B']['place'],1);self.assertEqual(result['C']['place'],3);self.assertEqual(result['D']['place'],1)
 def test_improvement_order(self):
  rows=[self.row(),self.row(id='b',trip=2,liters=6),self.row(id='c',driver='B'),self.row(id='d',driver='B',trip=2,liters=12),self.row(id='e',driver='C')]
  self.assertEqual([d['driver'] for d in improvement_rows(board(rows,WEIGHTS))],['Anne','B','C'])
 def test_many_courses_and_same_names(self):
  rows=[self.row(),self.row(id='b',course='Kurs B')];self.assertEqual(len(board(rows,WEIGHTS)),2);self.assertEqual(len(board(rows,WEIGHTS,course='Kurs B')),1)
if __name__=='__main__':unittest.main()
