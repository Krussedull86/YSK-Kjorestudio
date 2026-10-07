import unittest,tempfile,hashlib
from pathlib import Path
from unittest.mock import patch
import test_classroom
from classroom_views import projection,statistics
from core import WEIGHTS
from updates import download,install_script
class ViewTests(unittest.TestCase):
 def row(self,**kw):return test_classroom.ClassroomTests().row(**kw)
 def test_modes_and_ties(self):
  rows=[self.row(),self.row(id='b',driver='B',liters=6,minutes=60),self.row(id='c',driver='C',liters=6,minutes=60)]
  fuel=projection(rows,WEIGHTS,mode='Forbruk');self.assertEqual([d['view_place'] for d in fuel],[1,1,3]);self.assertEqual(fuel[0]['driver'],'B')
  self.assertEqual(projection(rows,WEIGHTS,mode='Tid per km')[0]['driver'],'Anne')
 def test_individual_ratings(self):
  rows=[self.row(komfort='Svak'),self.row(id='b',driver='B',avpassing='Svak')]
  self.assertEqual(projection(rows,WEIGHTS,mode='Komfort')[0]['driver'],'B')
  self.assertEqual(projection(rows,WEIGHTS,mode='Fartsavpassing')[0]['driver'],'Anne')
 def test_selectable_baseline(self):
  rows=[self.row(),self.row(id='b',trip=2,liters=6),self.row(id='c',trip=5,liters=3)]
  self.assertEqual(projection(rows,WEIGHTS,mode='Forbedring',baseline='2')[0]['improvement'],50)
  self.assertIsNone(projection(rows,WEIGHTS,mode='Forbedring',baseline='4')[0]['view_place'])
 def test_missing_and_zero(self):
  rows=[self.row(liters=0),self.row(id='b',trip=5,liters=1)]
  self.assertIsNone(projection(rows,WEIGHTS)[0]['improvement'])
  self.assertEqual(statistics(projection(rows,WEIGHTS))['trips'],2)
 def test_large_class_all_present(self):
  rows=[self.row(id=f'{n}-{t}',driver=f'Elev{n}',trip=t) for n in range(1000) for t in range(1,6)]
  result=projection(rows,WEIGHTS,mode='Vurderinger');self.assertEqual(len(result),1000);self.assertEqual(statistics(result)['complete'],1000)
class DownloadTests(unittest.TestCase):
 def test_untrusted_address_rejected(self):
  for url in ['http://school.test/storage/v1/object/sign/a','https://other.test/storage/v1/object/sign/a','https://school.test/evil','https://user@school.test/storage/v1/object/sign/a']:
   with self.assertRaises(ValueError):download({'url':url,'size':5},'https://school.test','unused.exe')
 def test_hash_failure_never_replaces(self):
  import io
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/'app.exe';target.write_bytes(b'old');asset={'url':'https://school.test/storage/v1/object/sign/a','size':3,'sha256':'0'*64}
   with patch('urllib.request.build_opener') as opener:
    opener.return_value.open.return_value=io.BytesIO(b'new')
    with self.assertRaises(ValueError):download(asset,'https://school.test',target)
   self.assertEqual(target.read_bytes(),b'old');self.assertFalse(target.with_suffix('.part').exists())
 def test_verified_download(self):
  import io
  with tempfile.TemporaryDirectory() as d,patch('urllib.request.build_opener') as opener:
   opener.return_value.open.return_value=io.BytesIO(b'new');p=download({'url':'https://school.test/storage/v1/object/sign/a','size':3,'sha256':hashlib.sha256(b'new').hexdigest()},'https://school.test',Path(d)/'app.exe');self.assertEqual(p.read_bytes(),b'new')
 def test_powershell_literal_path(self):
  text=install_script(123,"C:/it's here/$x.exe","C:/app.exe");self.assertIn("'C:/it''s here/$x.exe'",text);self.assertIn('Get-Process -Id 123',text);self.assertIn('.previous',text)
