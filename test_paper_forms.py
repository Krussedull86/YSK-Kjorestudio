import unittest,tempfile
from pathlib import Path
from speed_preview import calculated_speed
from paper_forms import create_forms,classic_templates
from core import Store
from course_setup import save_course
class PaperFormsTest(unittest.TestCase):
 def test_blank_speed_and_explicit_override(self):
  self.assertEqual(calculated_speed('32,5','60'),32.5)
  self.assertEqual(calculated_speed('32,5','1:00:00'),32.5)
  self.assertIsNone(calculated_speed(32.5,60,'40'))
  self.assertIsNone(calculated_speed(32.5,60,'-'))
  for km,minutes in [('nan',60),(20,0),(20,'12:99'),(-1,10)]:self.assertIsNone(calculated_speed(km,minutes))
 def test_course_selection_and_stop_sheet(self):
  with tempfile.TemporaryDirectory() as folder:
   store=Store(Path(folder)/'db');save_course(store,'Kurs',4,{'stop_count':3,'expected_minutes':120})
   templates=classic_templates(store,'Kurs');self.assertEqual(len(templates),4);self.assertEqual(templates[-1]['stop_count'],3)
   pdf=Path(folder)/'forms.pdf';pages=create_forms(pdf,['Åse Ødegård','Åse Ødegård','Bjørn'],'Kurs',templates)
   self.assertGreater(pages,2);self.assertTrue(pdf.read_bytes().startswith(b'%PDF'))
 def test_empty_selection_rejected(self):
  with self.assertRaises(ValueError):create_forms('unused.pdf',[],[] ,[])
