import unittest,tempfile
from pathlib import Path
from core import Store
from course_setup import *
from classroom_views import projection
class CourseTests(unittest.TestCase):
 def test_count_roundtrip_and_existing_trips(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'db';store=Store(path)
   self.assertEqual(course_count(store,'YSK'),5)
   save_course(store,'YSK',3);self.assertEqual(course_count(Store(path),'YSK'),3)
   self.assertEqual(course_names(store),['YSK'])
   for count in (0,6):
    with self.assertRaises(ValueError):save_course(store,'YSK',count)
   import_courses(store,[{'name':'New','active_trips':2}]);self.assertEqual(course_names(store),['New'])
 def test_names_and_selected_comparison(self):
  from test_classroom import ClassroomTests
  factory=ClassroomTests();rows=[factory.row(trip=n,id=str(n),liters=12/n) for n in range(1,6)]
  result=projection(rows,StoreWeights(),mode='Forbedring',baseline=NAMES[0],selected_trips=[1,3])
  self.assertEqual(result[0]['trip'],3);self.assertEqual([d['trip'] for d in result[0]['history']],[1,3])
  self.assertAlmostEqual(result[0]['improvement'],100*2/3)
  self.assertEqual(projection(rows,StoreWeights(),selected_trips=[]),[])
  result=projection(rows,StoreWeights(),trip=NAMES[3]);self.assertEqual(result[0]['trip'],4)
  for i,name in enumerate(NAMES,1):self.assertEqual(trip_number(name),i);self.assertEqual(trip_name(i),name)
def StoreWeights():
 from core import WEIGHTS
 return WEIGHTS
