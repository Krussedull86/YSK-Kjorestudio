import unittest,tempfile
from pathlib import Path
from core import Store,metrics,QUAL
class FuelTests(unittest.TestCase):
 def setUp(self):
  self.folder=tempfile.TemporaryDirectory();self.store=Store(Path(self.folder.name)/'test.db')
 def tearDown(self):self.folder.cleanup()
 def data(self,**values):
  result=dict(driver='Synthetic Student',course='Synthetic Course',vehicle='Test Vehicle',trip=1,minutes=60,km=40,liters=12,stops=0,date='2026-10-12',start_time='10:00',teacher='Synthetic Teacher')
  result.update({k:'Bra' for k in QUAL});result.update(values);return result
 def test_manual_fuel_per_100(self):
  from core import metrics
  d=self.store.save(self.data(fuel_per_100='28,5',km=40,liters=''))
  self.assertEqual(d['fuel_per_100'],28.5);self.assertEqual(d['liters'],11.4);self.assertAlmostEqual(metrics(d)['forbruk10'],2.85)
  d=self.store.save(self.data(id=d['id'],fuel_per_100=20,km=40,liters=12))
  self.assertEqual(d['liters'],12);self.assertEqual(metrics(d)['forbruk10'],2)
  d=self.store.save(self.data(id=d['id'],fuel_per_100='',km=40,liters=12))
  self.assertNotIn('fuel_per_100',d);self.assertEqual(metrics(d)['forbruk10'],3)
  for value in ('nan','inf',-1):
   with self.assertRaises(ValueError):self.store.validate(self.data(fuel_per_100=value))
